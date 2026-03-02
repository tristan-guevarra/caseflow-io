# document endpoints - upload, list, download, reprocess

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import RequireRole, require_lawyer
from app.models.document import Document, DocumentExtraction
from app.models.matter import Matter
from app.models.user import Membership
from app.schemas.documents import DocumentDetailResponse, DocumentResponse, ExtractionResponse
from app.services.audit import create_audit_log
from app.services.storage import generate_presigned_url, upload_document
from app.tasks.document_tasks import process_document

router = APIRouter(tags=["Documents"])

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25mb


@router.get(
    "/orgs/{org_id}/matters/{matter_id}/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    org_id: UUID,
    matter_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # grab all docs for this matter, newest first
    result = await db.execute(
        select(Document)
        .where(Document.organization_id == org_id, Document.matter_id == matter_id)
        .order_by(Document.created_at.desc())
    )
    return [DocumentResponse.model_validate(d) for d in result.scalars().all()]


@router.post(
    "/orgs/{org_id}/matters/{matter_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_endpoint(
    org_id: UUID,
    matter_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
):
    # only allow pdf and docx
    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}. Allowed: PDF, DOCX")

    # make sure the matter actually exists in this org
    matter = (await db.execute(
        select(Matter).where(Matter.id == matter_id, Matter.organization_id == org_id)
    )).scalar_one_or_none()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    # read the file and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 25MB.")

    # upload to s3/minio
    storage_path = upload_document(
        file_content=content,
        filename=file.filename or "unnamed",
        organization_id=str(org_id),
        matter_id=str(matter_id),
        content_type=content_type,
    )

    # save doc record in db
    doc = Document(
        organization_id=org_id,
        matter_id=matter_id,
        uploaded_by_id=membership.user_id,
        filename=file.filename or "unnamed",
        file_type=ALLOWED_TYPES[content_type],
        file_size_bytes=len(content),
        storage_path=storage_path,
        processing_status="pending",
    )
    db.add(doc)
    await db.flush()

    await create_audit_log(
        db,
        organization_id=org_id,
        user_id=membership.user_id,
        action="document.uploaded",
        resource_type="document",
        resource_id=doc.id,
        details={"filename": doc.filename, "matter_id": str(matter_id)},
    )

    # kick off ai processing in the background
    process_document.delay(str(doc.id))

    return DocumentResponse.model_validate(doc)


@router.get("/orgs/{org_id}/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    org_id: UUID,
    document_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # get doc with its extractions
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id, Document.organization_id == org_id)
        .options(selectinload(Document.extractions))
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    extractions = [ExtractionResponse.model_validate(e) for e in doc.extractions]

    return DocumentDetailResponse(
        **DocumentResponse.model_validate(doc).model_dump(),
        extractions=extractions,
    )


@router.get("/orgs/{org_id}/documents/{document_id}/download")
async def download_document_endpoint(
    org_id: UUID,
    document_id: UUID,
    membership: Annotated[Membership, Depends(RequireRole("paralegal"))],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # generate a temporary download link
    doc = (await db.execute(
        select(Document).where(Document.id == document_id, Document.organization_id == org_id)
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    url = generate_presigned_url(doc.storage_path)
    return {"download_url": url, "filename": doc.filename}


@router.post("/orgs/{org_id}/documents/{document_id}/reprocess", response_model=DocumentResponse)
async def reprocess_document(
    org_id: UUID,
    document_id: UUID,
    membership: Annotated[Membership, Depends(require_lawyer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # re-run ai extraction on a doc
    doc = (await db.execute(
        select(Document).where(Document.id == document_id, Document.organization_id == org_id)
    )).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # wipe old extractions first
    await db.execute(
        DocumentExtraction.__table__.delete().where(DocumentExtraction.document_id == document_id)
    )

    doc.processing_status = "pending"
    doc.processing_error = None
    await db.flush()

    process_document.delay(str(doc.id))

    return DocumentResponse.model_validate(doc)
