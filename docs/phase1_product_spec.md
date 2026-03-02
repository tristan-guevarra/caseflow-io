# caseflow -- phase 1 planning notes

my working spec for the MVP. this is the document i used to plan out the entire first version before writing any code.

---

## the idea

a multi-tenant app for law firms that combines case/matter management with AI-powered document intelligence. you upload legal documents (PDFs, DOCX files) and the system uses GPT-4o-mini to automatically extract structured data -- parties, deadlines, obligations, key clauses, risk flags. then it generates tasks from deadlines, builds timelines from key dates, and lets you search across everything with natural language.

target users: small-to-mid firms (2-50 lawyers) who are still running on shared drives and spreadsheets.

---

## user roles

three roles, each with different levels of access:

**admin** (managing partner / office manager)
- sets up the firm, invites users, manages roles
- sees firm-wide dashboards, audit logs
- controls org settings

**lawyer** (associate / senior associate)
- creates and manages matters
- uploads documents, reviews AI extractions
- manages tasks, builds timelines, runs searches

**paralegal** (legal assistant)
- supports lawyers with doc prep and uploads
- read-only on matters they're assigned to
- completes tasks, adds timeline events

---

## core user flows

### onboarding
admin signs up -> creates organization -> verifies email -> lands on empty dashboard with guided setup -> invites first users -> creates first matter

### matter lifecycle
lawyer creates matter (title, case number, client, type, jurisdiction, opposing party) -> status defaults to "active" -> assigns team members -> uploads documents -> AI processes in background -> lawyer reviews extractions -> tasks auto-generated from deadlines -> timeline auto-populated -> eventually closed or archived

### document intelligence (the main thing)
user uploads PDF/DOCX to a matter -> file stored in S3 (scoped to org) -> celery job kicks off:
1. extract raw text (pypdf2 / python-docx)
2. chunk text for LLM context window
3. send to openai with structured extraction prompt
4. validate JSON response against pydantic schema
5. retry up to 3x on invalid output
6. store structured extraction in document_extractions table
7. generate embedding vectors, store in embeddings table
8. auto-create tasks from detected deadlines
9. auto-create timeline events from key dates
10. create audit log entry

user gets notified "document processed" -> reviews extraction on document detail page

### semantic search
user types natural language query -> backend generates embedding -> pgvector cosine similarity search across org's embeddings -> returns ranked doc chunks with source references -> click through to source document

### task management
AI detects deadline in document -> system creates task with title, calculated due date, assigned to lead lawyer, linked to source document, priority auto-set based on urgency -> lawyer can edit/reassign/complete/delete -> 7-day and 1-day deadline alerts via in-app notification

### timeline
auto-populates from: document upload dates, extracted dates (filings, hearings, deadlines), manual entries -> vertical chronological timeline on matter detail page -> each event has date, title, description, source, category -> filterable by category (filing, hearing, deadline, correspondence, custom)

---

## data model

```
organizations --1:N-- memberships --N:1-- users
organizations --1:N-- matters
matters --N:N-- users (via matter_assignments)
matters --1:N-- documents
documents --1:N-- document_extractions
documents --1:N-- embeddings
matters --1:N-- tasks
matters --1:N-- timeline_events
organizations --1:N-- audit_logs
users --1:N-- audit_logs
users --1:N-- notifications
```

key tables and what they store:

- **organizations** -- firm info, subscription tier, storage limits, settings (JSONB)
- **users** -- email, hashed password, name, active status
- **memberships** -- links users to orgs with a role (admin/lawyer/paralegal)
- **matters** -- the core entity. title, case number, client, type, status, jurisdiction, opposing party
- **matter_assignments** -- who's on each matter and in what capacity (lead/contributor/viewer)
- **documents** -- uploaded files. tracks filename, type, size, storage path, processing status
- **document_extractions** -- structured AI output per document. extraction type (parties/deadlines/obligations/clauses/risk flags/summary), extracted data as JSONB, confidence score
- **embeddings** -- vector chunks for semantic search. chunk text + 1536-dim embedding vector (pgvector)
- **tasks** -- can be AI-generated or manual. title, status, priority, due date, assignee, linked to source extraction
- **timeline_events** -- date, title, description, category, source (ai_extracted/manual/system)
- **audit_logs** -- who did what, when, on which resource. JSONB details, IP address
- **notifications** -- in-app alerts for deadline warnings, document processing, task assignments

---

## api design

everything is org-scoped: `/api/v1/orgs/{org_id}/...`

### auth
- POST /auth/register -- sign up + create org
- POST /auth/login -- returns JWT + refresh token
- POST /auth/refresh -- refresh access token
- POST /auth/logout -- invalidate refresh token
- GET /auth/me -- current user + memberships

### matters
- standard CRUD at /orgs/{org_id}/matters
- POST .../assign for team assignment
- GET .../timeline for timeline events

### documents
- upload to /orgs/{org_id}/matters/{mid}/documents
- GET .../documents/{id} returns doc + all extractions
- POST .../documents/{id}/reprocess to re-run AI

### tasks
- list all at /orgs/{org_id}/tasks (filterable)
- per-matter at /orgs/{org_id}/matters/{mid}/tasks

### search
- POST /orgs/{org_id}/search -- semantic search endpoint

### other
- notifications (list, mark read, mark all read)
- audit logs (list, admin only)
- dashboard stats

---

## frontend pages

public: login, register, forgot password

authenticated:
- **/dashboard** -- stat cards (active matters, open tasks, upcoming deadlines, docs processed), upcoming deadlines list, recent activity feed, my tasks table
- **/matters** -- filterable/searchable list
- **/matters/new** -- create form
- **/matters/[id]** -- tabbed detail view (overview, documents, tasks, timeline)
- **/matters/[id]/documents/[docId]** -- document preview on left, tabbed extractions on right (parties, deadlines, obligations, clauses, risk flags)
- **/tasks** -- personal task board with filters
- **/search** -- semantic search with ranked results
- **/notifications** -- notification center
- **/settings** -- org settings (admin), member management, audit log
- **/profile** -- personal settings, password change

---

## AI extraction output shape

what GPT-4o-mini returns (validated against pydantic):

```json
{
  "summary": "2-3 sentence summary",
  "parties": [{ "name": "...", "role": "plaintiff", "context": "..." }],
  "deadlines": [{ "date": "2024-03-15", "description": "...", "source_text": "...", "urgency": "high" }],
  "obligations": [{ "party": "...", "obligation": "...", "clause_reference": "...", "due_date": "..." }],
  "key_clauses": [{ "clause_type": "indemnification", "summary": "...", "source_text": "..." }],
  "risk_flags": [{ "flag_type": "statute_of_limitations", "severity": "high", "description": "..." }],
  "key_dates": [{ "date": "2024-01-15", "description": "...", "category": "filing" }]
}
```

---

## non-functional targets

- api response time (p95): < 500ms for non-AI endpoints
- document processing: < 60s for a typical 20-page doc
- max document size: 25MB
- embedding dimensions: 1536 (text-embedding-3-small)
- LLM: gpt-4o-mini for extraction, text-embedding-3-small for embeddings

---

## scope boundaries

### in (MVP)
- email/password auth with JWT
- single-org user management with 3 roles
- full matter CRUD with team assignment
- document upload (PDF/DOCX) with AI extraction
- AI-generated tasks from deadlines
- auto-constructed + manual timeline
- semantic search across documents
- in-app notifications
- audit logging
- dashboard with stats

### out (post-MVP / future)
- OAuth/SSO
- real-time collaboration / websockets
- email notifications
- billing integration
- document version history
- client portal
- mobile app
- advanced analytics
- calendar integrations
- e-signature integration
- multi-language support
