# seed script - populates the db with realistic demo data

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.document import Document, DocumentExtraction
from app.models.matter import Matter, MatterAssignment
from app.models.task import AuditLog, Notification, Task, TimelineEvent
from app.models.user import Membership, Organization, User

settings = get_settings()
engine = create_engine(settings.DATABASE_URL_SYNC)
SessionLocal = sessionmaker(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # bail if already seeded
        if db.query(Organization).first():
            print("Database already seeded. Skipping.")
            return

        print("Seeding database...")

        # create the demo org
        org = Organization(
            id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
            name="Chen & Park LLP",
            slug="chen-park-llp",
            subscription_tier="professional",
            subscription_status="active",
            max_users=25,
            max_storage_mb=10240,
        )
        db.add(org)
        db.flush()
        print("  Organization created: Chen & Park LLP")

        # create demo users (all same password for easy testing)
        password = hash_password("Demo1234!")

        sarah = User(
            id=uuid.UUID("20000000-0000-0000-0000-000000000001"),
            email="sarah@demo-firm.com",
            hashed_password=password,
            full_name="Sarah Chen",
            last_login_at=datetime.now(timezone.utc),
        )
        david = User(
            id=uuid.UUID("20000000-0000-0000-0000-000000000002"),
            email="david@demo-firm.com",
            hashed_password=password,
            full_name="David Park",
            last_login_at=datetime.now(timezone.utc),
        )
        maria = User(
            id=uuid.UUID("20000000-0000-0000-0000-000000000003"),
            email="maria@demo-firm.com",
            hashed_password=password,
            full_name="Maria Santos",
            last_login_at=datetime.now(timezone.utc),
        )
        db.add_all([sarah, david, maria])
        db.flush()
        print("  Users created: Sarah (admin), David (lawyer), Maria (paralegal)")

        # assign roles in the org
        db.add_all([
            Membership(user_id=sarah.id, organization_id=org.id, role="admin"),
            Membership(user_id=david.id, organization_id=org.id, role="lawyer"),
            Membership(user_id=maria.id, organization_id=org.id, role="paralegal"),
        ])
        db.flush()

        # create some matters
        today = date.today()

        matter1 = Matter(
            id=uuid.UUID("30000000-0000-0000-0000-000000000001"),
            organization_id=org.id,
            title="Acme Corp v. TechStart Inc — Patent Infringement",
            case_number="2026-CV-04521",
            client_name="Acme Corporation",
            matter_type="litigation",
            status="active",
            jurisdiction="Northern District of California",
            opposing_party="TechStart Inc.",
            description="Patent infringement action involving U.S. Patent No. 10,234,567 relating to AI-based document processing technology. Acme alleges TechStart's product directly infringes claims 1-15.",
            opened_at=today - timedelta(days=45),
            created_by_id=david.id,
        )

        matter2 = Matter(
            id=uuid.UUID("30000000-0000-0000-0000-000000000002"),
            organization_id=org.id,
            title="Meridian Real Estate — Series B Acquisition",
            case_number="DEAL-2026-0089",
            client_name="Meridian Properties LLC",
            matter_type="corporate",
            status="active",
            jurisdiction="Delaware",
            opposing_party=None,
            description="Advising Meridian on the acquisition of a 12-property commercial real estate portfolio. Transaction value approximately $45M. Involves complex financing structure with multiple lender parties.",
            opened_at=today - timedelta(days=20),
            created_by_id=david.id,
        )

        matter3 = Matter(
            id=uuid.UUID("30000000-0000-0000-0000-000000000003"),
            organization_id=org.id,
            title="Harper Employment Dispute",
            case_number="EEOC-2026-3301",
            client_name="GlobalTech Solutions",
            matter_type="employment",
            status="pending",
            jurisdiction="Southern District of New York",
            opposing_party="James Harper",
            description="Defense of employment discrimination claim filed by former senior engineer. Claimant alleges wrongful termination based on age and disability discrimination.",
            opened_at=today - timedelta(days=60),
            created_by_id=sarah.id,
        )

        matter4 = Matter(
            id=uuid.UUID("30000000-0000-0000-0000-000000000004"),
            organization_id=org.id,
            title="CloudNine IP Portfolio Review",
            case_number="IP-2026-0045",
            client_name="CloudNine Technologies",
            matter_type="ip",
            status="active",
            jurisdiction="USPTO",
            description="Comprehensive IP portfolio audit and freedom-to-operate analysis for CloudNine's upcoming product launch. Reviewing 23 patents and identifying potential infringement risks.",
            opened_at=today - timedelta(days=10),
            created_by_id=david.id,
        )

        matter5 = Matter(
            id=uuid.UUID("30000000-0000-0000-0000-000000000005"),
            organization_id=org.id,
            title="Williams Family Trust Restructuring",
            case_number="TRUST-2025-0912",
            client_name="Williams Family Office",
            matter_type="other",
            status="closed",
            jurisdiction="California",
            description="Restructuring of the Williams Family Trust to accommodate new beneficiaries and updated tax optimization strategies.",
            opened_at=today - timedelta(days=120),
            closed_at=today - timedelta(days=15),
            created_by_id=sarah.id,
        )

        db.add_all([matter1, matter2, matter3, matter4, matter5])
        db.flush()
        print("  5 matters created")

        # assign people to matters
        db.add_all([
            MatterAssignment(matter_id=matter1.id, user_id=david.id, role="lead"),
            MatterAssignment(matter_id=matter1.id, user_id=maria.id, role="contributor"),
            MatterAssignment(matter_id=matter2.id, user_id=david.id, role="lead"),
            MatterAssignment(matter_id=matter2.id, user_id=sarah.id, role="contributor"),
            MatterAssignment(matter_id=matter3.id, user_id=sarah.id, role="lead"),
            MatterAssignment(matter_id=matter3.id, user_id=maria.id, role="contributor"),
            MatterAssignment(matter_id=matter4.id, user_id=david.id, role="lead"),
            MatterAssignment(matter_id=matter5.id, user_id=sarah.id, role="lead"),
        ])
        db.flush()

        # create some documents (metadata only, no actual files)
        doc1 = Document(
            id=uuid.UUID("40000000-0000-0000-0000-000000000001"),
            organization_id=org.id,
            matter_id=matter1.id,
            uploaded_by_id=david.id,
            filename="Acme_v_TechStart_Complaint.pdf",
            file_type="pdf",
            file_size_bytes=2_450_000,
            storage_path=f"{org.id}/{matter1.id}/complaint.pdf",
            processing_status="completed",
            page_count=32,
        )
        doc2 = Document(
            id=uuid.UUID("40000000-0000-0000-0000-000000000002"),
            organization_id=org.id,
            matter_id=matter1.id,
            uploaded_by_id=maria.id,
            filename="Patent_10234567_Full_Text.pdf",
            file_type="pdf",
            file_size_bytes=890_000,
            storage_path=f"{org.id}/{matter1.id}/patent.pdf",
            processing_status="completed",
            page_count=18,
        )
        doc3 = Document(
            id=uuid.UUID("40000000-0000-0000-0000-000000000003"),
            organization_id=org.id,
            matter_id=matter2.id,
            uploaded_by_id=david.id,
            filename="Meridian_Purchase_Agreement_Draft.docx",
            file_type="docx",
            file_size_bytes=1_120_000,
            storage_path=f"{org.id}/{matter2.id}/purchase_agreement.docx",
            processing_status="completed",
            page_count=45,
        )
        doc4 = Document(
            id=uuid.UUID("40000000-0000-0000-0000-000000000004"),
            organization_id=org.id,
            matter_id=matter3.id,
            uploaded_by_id=sarah.id,
            filename="Harper_EEOC_Charge.pdf",
            file_type="pdf",
            file_size_bytes=340_000,
            storage_path=f"{org.id}/{matter3.id}/eeoc_charge.pdf",
            processing_status="completed",
            page_count=8,
        )
        db.add_all([doc1, doc2, doc3, doc4])
        db.flush()
        print("  4 documents created")

        # fake ai extraction results for the docs
        db.add_all([
            DocumentExtraction(
                document_id=doc1.id, organization_id=org.id, extraction_type="summary",
                extracted_data={"text": "Patent infringement complaint filed by Acme Corporation against TechStart Inc. in the Northern District of California. Acme alleges that TechStart's DocuMind product infringes U.S. Patent No. 10,234,567 relating to AI-based document analysis. The complaint seeks injunctive relief and damages exceeding $12 million."},
                confidence_score=0.92, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc1.id, organization_id=org.id, extraction_type="parties",
                extracted_data={"items": [
                    {"name": "Acme Corporation", "role": "plaintiff", "context": "Owner of the disputed patent, Delaware corporation with principal offices in San Jose, CA"},
                    {"name": "TechStart Inc.", "role": "defendant", "context": "Maker of the DocuMind product, incorporated in Delaware with offices in San Francisco"},
                    {"name": "Dr. Lisa Wong", "role": "other", "context": "Named inventor on U.S. Patent No. 10,234,567"},
                ]},
                confidence_score=0.95, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc1.id, organization_id=org.id, extraction_type="deadlines",
                extracted_data={"items": [
                    {"date": str(today + timedelta(days=12)), "description": "Defendant's Answer or Motion to Dismiss due", "source_text": "Defendant shall file a responsive pleading within 21 days of service...", "urgency": "high"},
                    {"date": str(today + timedelta(days=45)), "description": "Initial Disclosures under Rule 26(a)(1)", "source_text": "Parties shall exchange initial disclosures no later than 14 days after...", "urgency": "medium"},
                    {"date": str(today + timedelta(days=90)), "description": "Discovery cutoff", "source_text": "All fact discovery shall be completed within 120 days of the initial case management conference...", "urgency": "low"},
                ]},
                confidence_score=0.88, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc1.id, organization_id=org.id, extraction_type="risk_flags",
                extracted_data={"items": [
                    {"flag_type": "deadline_risk", "severity": "high", "description": "Response deadline approaching in 12 days. Failure to respond may result in default judgment."},
                    {"flag_type": "unfavorable_terms", "severity": "medium", "description": "Plaintiff seeks enhanced damages for willful infringement, which could triple the damage award."},
                ]},
                confidence_score=0.85, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc3.id, organization_id=org.id, extraction_type="summary",
                extracted_data={"text": "Draft purchase agreement for Meridian Properties LLC to acquire a portfolio of 12 commercial properties. Total consideration is $45,250,000 with a complex financing structure involving senior and mezzanine debt. Includes standard representations, warranties, and a 60-day due diligence period."},
                confidence_score=0.91, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc3.id, organization_id=org.id, extraction_type="key_clauses",
                extracted_data={"items": [
                    {"clause_type": "indemnification", "summary": "Seller indemnifies buyer for breaches of representations up to 15% of purchase price with an 18-month survival period", "source_text": "Seller shall indemnify, defend, and hold harmless Buyer from and against any and all Losses..."},
                    {"clause_type": "termination", "summary": "Either party may terminate if closing has not occurred within 90 days of execution, or upon material breach uncured for 15 business days", "source_text": "This Agreement may be terminated by either party upon written notice..."},
                    {"clause_type": "governing_law", "summary": "Agreement governed by Delaware law with exclusive jurisdiction in the Court of Chancery", "source_text": "This Agreement shall be governed by and construed in accordance with the laws of the State of Delaware..."},
                ]},
                confidence_score=0.90, model_version="gpt-4o-mini",
            ),
            DocumentExtraction(
                document_id=doc3.id, organization_id=org.id, extraction_type="obligations",
                extracted_data={"items": [
                    {"party": "Buyer (Meridian)", "obligation": "Complete environmental assessments for all 12 properties", "clause_reference": "Section 5.3(a)", "due_date": str(today + timedelta(days=30))},
                    {"party": "Seller", "obligation": "Provide all tenant leases and estoppel certificates", "clause_reference": "Section 4.2(b)", "due_date": str(today + timedelta(days=14))},
                    {"party": "Buyer (Meridian)", "obligation": "Deliver financing commitment letter", "clause_reference": "Section 6.1", "due_date": str(today + timedelta(days=21))},
                ]},
                confidence_score=0.87, model_version="gpt-4o-mini",
            ),
        ])
        db.flush()
        print("  Document extractions created")

        # create tasks (mix of ai-generated and manual)
        db.add_all([
            Task(organization_id=org.id, matter_id=matter1.id, document_id=doc1.id,
                 title="[AI] File Answer or Motion to Dismiss", description="Auto-generated: Defendant's responsive pleading deadline approaching.",
                 status="pending", priority="urgent", due_date=today + timedelta(days=12),
                 assigned_to_id=david.id, created_by="ai"),
            Task(organization_id=org.id, matter_id=matter1.id, document_id=doc1.id,
                 title="[AI] Prepare Initial Disclosures", description="Auto-generated: Exchange initial disclosures per Rule 26(a)(1).",
                 status="pending", priority="high", due_date=today + timedelta(days=45),
                 assigned_to_id=david.id, created_by="ai"),
            Task(organization_id=org.id, matter_id=matter1.id,
                 title="Review TechStart product documentation", description="Obtain and review TechStart's DocuMind technical documentation for infringement analysis.",
                 status="in_progress", priority="high", due_date=today + timedelta(days=7),
                 assigned_to_id=maria.id, created_by="manual"),
            Task(organization_id=org.id, matter_id=matter2.id, document_id=doc3.id,
                 title="[AI] Complete environmental assessments", description="Auto-generated: Environmental due diligence for all 12 properties.",
                 status="pending", priority="high", due_date=today + timedelta(days=30),
                 assigned_to_id=david.id, created_by="ai"),
            Task(organization_id=org.id, matter_id=matter2.id,
                 title="Review tenant lease abstracts", description="Review and summarize all existing tenant leases across the portfolio.",
                 status="pending", priority="medium", due_date=today + timedelta(days=14),
                 assigned_to_id=maria.id, created_by="manual"),
            Task(organization_id=org.id, matter_id=matter3.id,
                 title="Prepare EEOC position statement", description="Draft initial position statement responding to Harper's discrimination charge.",
                 status="in_progress", priority="urgent", due_date=today + timedelta(days=5),
                 assigned_to_id=sarah.id, created_by="manual"),
            Task(organization_id=org.id, matter_id=matter3.id,
                 title="Collect HR records for Harper", description="Request and organize all employment records, performance reviews, and communications related to James Harper.",
                 status="completed", priority="high", due_date=today - timedelta(days=5),
                 assigned_to_id=maria.id, created_by="manual",
                 completed_at=datetime.now(timezone.utc) - timedelta(days=3)),
            Task(organization_id=org.id, matter_id=matter4.id,
                 title="Freedom-to-operate analysis — Module 1", description="Complete FTO analysis for CloudNine's core inference engine module.",
                 status="pending", priority="high", due_date=today + timedelta(days=20),
                 assigned_to_id=david.id, created_by="manual"),
        ])
        db.flush()
        print("  8 tasks created (including 3 AI-generated)")

        # timeline events
        db.add_all([
            TimelineEvent(organization_id=org.id, matter_id=matter1.id,
                         title="Complaint Filed", event_date=today - timedelta(days=45),
                         category="filing", source="manual", created_by_id=david.id),
            TimelineEvent(organization_id=org.id, matter_id=matter1.id,
                         title="Service of Process Completed", event_date=today - timedelta(days=30),
                         category="correspondence", source="manual", created_by_id=maria.id),
            TimelineEvent(organization_id=org.id, matter_id=matter1.id, document_id=doc1.id,
                         title="Complaint analyzed by AI", event_date=today - timedelta(days=28),
                         description="AI extraction identified 3 parties, 3 deadlines, and 2 risk flags.",
                         category="custom", source="ai_extracted"),
            TimelineEvent(organization_id=org.id, matter_id=matter1.id,
                         title="Answer/MTD Deadline", event_date=today + timedelta(days=12),
                         category="deadline", source="ai_extracted"),
            TimelineEvent(organization_id=org.id, matter_id=matter1.id,
                         title="Initial Case Management Conference", event_date=today + timedelta(days=30),
                         category="hearing", source="manual", created_by_id=david.id),
            TimelineEvent(organization_id=org.id, matter_id=matter2.id,
                         title="Engagement letter executed", event_date=today - timedelta(days=20),
                         category="custom", source="manual", created_by_id=david.id),
            TimelineEvent(organization_id=org.id, matter_id=matter2.id,
                         title="Due diligence period begins", event_date=today - timedelta(days=15),
                         category="deadline", source="manual", created_by_id=david.id),
            TimelineEvent(organization_id=org.id, matter_id=matter2.id,
                         title="Due diligence period ends", event_date=today + timedelta(days=45),
                         category="deadline", source="ai_extracted"),
            TimelineEvent(organization_id=org.id, matter_id=matter3.id,
                         title="EEOC Charge received", event_date=today - timedelta(days=60),
                         category="filing", source="manual", created_by_id=sarah.id),
            TimelineEvent(organization_id=org.id, matter_id=matter3.id,
                         title="Position statement deadline", event_date=today + timedelta(days=5),
                         category="deadline", source="manual", created_by_id=sarah.id),
        ])
        db.flush()
        print("  10 timeline events created")

        # notifications
        db.add_all([
            Notification(organization_id=org.id, user_id=david.id,
                        title="Document processed", message='"Acme_v_TechStart_Complaint.pdf" analyzed. 3 deadlines and 2 risk flags found.',
                        notification_type="document_processed", link=f"/matters/{matter1.id}/documents/{doc1.id}"),
            Notification(organization_id=org.id, user_id=david.id,
                        title="Deadline approaching", message="Answer/MTD deadline in 12 days for Acme Corp v. TechStart Inc.",
                        notification_type="deadline_alert", link=f"/matters/{matter1.id}"),
            Notification(organization_id=org.id, user_id=sarah.id,
                        title="Deadline approaching", message="EEOC Position Statement due in 5 days for Harper Employment Dispute.",
                        notification_type="deadline_alert", link=f"/matters/{matter3.id}"),
            Notification(organization_id=org.id, user_id=maria.id,
                        title="Task assigned", message='You have been assigned "Review TechStart product documentation".',
                        notification_type="task_assigned", link=f"/matters/{matter1.id}"),
        ])
        db.flush()
        print("  4 notifications created")

        # audit log entries
        db.add_all([
            AuditLog(organization_id=org.id, user_id=sarah.id, action="org.created", resource_type="organization", resource_id=org.id, details={"name": "Chen & Park LLP"}),
            AuditLog(organization_id=org.id, user_id=sarah.id, action="member.invited", resource_type="membership", details={"email": "david@demo-firm.com", "role": "lawyer"}),
            AuditLog(organization_id=org.id, user_id=sarah.id, action="member.invited", resource_type="membership", details={"email": "maria@demo-firm.com", "role": "paralegal"}),
            AuditLog(organization_id=org.id, user_id=david.id, action="matter.created", resource_type="matter", resource_id=matter1.id, details={"title": matter1.title}),
            AuditLog(organization_id=org.id, user_id=david.id, action="document.uploaded", resource_type="document", resource_id=doc1.id, details={"filename": "Acme_v_TechStart_Complaint.pdf"}),
            AuditLog(organization_id=org.id, user_id=david.id, action="document.uploaded", resource_type="document", resource_id=doc3.id, details={"filename": "Meridian_Purchase_Agreement_Draft.docx"}),
            AuditLog(organization_id=org.id, user_id=sarah.id, action="matter.created", resource_type="matter", resource_id=matter3.id, details={"title": matter3.title}),
        ])
        db.flush()
        print("  Audit logs created")

        db.commit()
        print("\nSeeding complete! Demo credentials:")
        print("   Admin:    sarah@demo-firm.com / Demo1234!")
        print("   Lawyer:   david@demo-firm.com / Demo1234!")
        print("   Paralegal: maria@demo-firm.com / Demo1234!")

    except Exception as e:
        db.rollback()
        print(f"\nSeeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
