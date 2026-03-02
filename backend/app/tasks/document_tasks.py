# celery tasks for processing uploaded documents end to end

import uuid
from datetime import date, datetime, timezone

import structlog
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.document import Document, DocumentExtraction, Embedding
from app.models.task import Notification, Task, TimelineEvent
from app.tasks import celery_app
from app.services.ai import chunk_text, extract_text, generate_embeddings, run_extraction
from app.services.storage import download_document

logger = structlog.get_logger()
settings = get_settings()

# sync engine bc celery doesn't do async
sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_size=5, max_overflow=2)
SyncSession = sessionmaker(bind=sync_engine)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def process_document(self, document_id: str) -> dict:
    # the whole pipeline: download -> extract text -> ai extraction ->
    # save results -> embeddings -> create tasks -> timeline -> notify
    db = SyncSession()
    try:
        doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).one_or_none()
        if not doc:
            logger.error("document_not_found", document_id=document_id)
            return {"status": "error", "message": "Document not found"}

        # mark it as processing
        doc.processing_status = "processing"
        db.commit()

        logger.info("processing_started", document_id=document_id, filename=doc.filename)

        # step 1: grab the file from s3
        file_content = download_document(doc.storage_path)

        # step 2: pull the text out of the file
        raw_text = extract_text(file_content, doc.file_type)
        doc.raw_text = raw_text
        doc.page_count = raw_text.count("\n\n") + 1  # rough estimate
        db.commit()

        if not raw_text.strip():
            doc.processing_status = "failed"
            doc.processing_error = "No text could be extracted from document"
            db.commit()
            return {"status": "error", "message": "No text extracted"}

        # step 3: send it to openai for structured extraction
        extraction_result = run_extraction(raw_text, doc.filename, doc.file_type)

        # step 4: save all the extracted stuff to db
        extraction_map = {
            "summary": {"text": extraction_result.summary},
            "parties": extraction_result.parties,
            "deadlines": extraction_result.deadlines,
            "obligations": extraction_result.obligations,
            "key_clauses": extraction_result.key_clauses,
            "risk_flags": extraction_result.risk_flags,
        }

        for ext_type, ext_data in extraction_map.items():
            extraction = DocumentExtraction(
                document_id=doc.id,
                organization_id=doc.organization_id,
                extraction_type=ext_type,
                extracted_data=ext_data if isinstance(ext_data, dict) else {"items": ext_data},
                confidence_score=0.85,
                model_version=settings.OPENAI_MODEL,
            )
            db.add(extraction)
        db.flush()

        # step 5: chunk the text and generate embeddings
        chunks = chunk_text(raw_text)
        if chunks:
            embeddings_vectors = generate_embeddings(chunks)
            for i, (chunk, vector) in enumerate(zip(chunks, embeddings_vectors)):
                emb = Embedding(
                    organization_id=doc.organization_id,
                    document_id=doc.id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=vector,
                    metadata_={"filename": doc.filename, "matter_id": str(doc.matter_id)},
                )
                db.add(emb)

        # step 6: create tasks from any deadlines the ai found
        deadline_extraction = db.query(DocumentExtraction).filter(
            DocumentExtraction.document_id == doc.id,
            DocumentExtraction.extraction_type == "deadlines",
        ).first()

        if deadline_extraction and "items" in deadline_extraction.extracted_data:
            for deadline in deadline_extraction.extracted_data["items"]:
                due_date = None
                if deadline.get("date"):
                    try:
                        due_date = date.fromisoformat(deadline["date"])
                    except (ValueError, TypeError):
                        pass

                priority_map = {"low": "low", "medium": "medium", "high": "high", "critical": "urgent"}
                priority = priority_map.get(deadline.get("urgency", "medium"), "medium")

                task = Task(
                    organization_id=doc.organization_id,
                    matter_id=doc.matter_id,
                    document_id=doc.id,
                    title=f"[AI] {deadline.get('description', 'Review deadline')}",
                    description=f"Auto-generated from document: {doc.filename}\n\nSource: {deadline.get('source_text', '')}",
                    priority=priority,
                    due_date=due_date,
                    created_by="ai",
                    source_extraction_id=deadline_extraction.id,
                )
                db.add(task)

        # step 7: create timeline events from key dates
        for key_date in extraction_result.key_dates:
            if key_date.get("date"):
                try:
                    event_date = date.fromisoformat(key_date["date"])
                    category_map = {
                        "filing": "filing",
                        "hearing": "hearing",
                        "deadline": "deadline",
                        "execution": "custom",
                        "effective": "custom",
                        "expiration": "deadline",
                        "correspondence": "correspondence",
                    }
                    category = category_map.get(key_date.get("category", ""), "custom")
                    event = TimelineEvent(
                        organization_id=doc.organization_id,
                        matter_id=doc.matter_id,
                        document_id=doc.id,
                        title=key_date.get("description", "Date extracted from document"),
                        event_date=event_date,
                        category=category,
                        source="ai_extracted",
                    )
                    db.add(event)
                except (ValueError, TypeError):
                    continue

        # step 8: let the uploader know it's done
        if doc.uploaded_by_id:
            notification = Notification(
                organization_id=doc.organization_id,
                user_id=doc.uploaded_by_id,
                title="Document processed",
                message=f'"{doc.filename}" has been analyzed. {len(extraction_result.deadlines)} deadlines and {len(extraction_result.risk_flags)} risk flags found.',
                notification_type="document_processed",
                link=f"/matters/{doc.matter_id}/documents/{doc.id}",
            )
            db.add(notification)

        # all done, mark as completed
        doc.processing_status = "completed"
        db.commit()

        logger.info(
            "processing_completed",
            document_id=document_id,
            filename=doc.filename,
            deadlines=len(extraction_result.deadlines),
            parties=len(extraction_result.parties),
            risk_flags=len(extraction_result.risk_flags),
            chunks=len(chunks),
        )

        return {
            "status": "completed",
            "document_id": document_id,
            "parties": len(extraction_result.parties),
            "deadlines": len(extraction_result.deadlines),
            "risk_flags": len(extraction_result.risk_flags),
        }

    except Exception as exc:
        db.rollback()
        logger.error("processing_failed", document_id=document_id, error=str(exc))

        # try to mark the doc as failed
        try:
            doc = db.query(Document).filter(Document.id == uuid.UUID(document_id)).one_or_none()
            if doc:
                doc.processing_status = "failed"
                doc.processing_error = str(exc)[:1000]
                db.commit()
        except Exception:
            pass

        # retry if we have attempts left
        raise self.retry(exc=exc)

    finally:
        db.close()
