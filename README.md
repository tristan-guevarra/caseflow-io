# caseflow

**ai-powered legal matter management platform**

upload. extract. act.

---

## why i built this

law firms drown in documents. every contract, filing, and agreement has deadlines, obligations, and risk buried in it — and most of the time someone has to manually read through everything to find it. that's slow, expensive, and things get missed.

caseflow automates that. upload a pdf or docx to a matter, and the system uses gpt-4o-mini to extract structured data — parties, deadlines, obligations, key clauses, risk flags — then auto-generates tasks and timeline events from what it finds. it also builds vector embeddings so you can search across all your documents in natural language.

the goal was to build something a small firm could actually use: plug it in, upload documents, and immediately get actionable intelligence out of them instead of reading 50-page contracts line by line.

---

## what it does

### ai document intelligence
- upload pdf or docx, system extracts structured data via gpt-4o-mini with validated pydantic schemas
- extracts parties, deadlines, obligations, key clauses, and risk flags
- retry loop with schema validation (up to 3x on invalid output)

### auto-generated tasks
- deadlines found in documents automatically become tasks
- calculated due dates, priority levels, and assignees

### case timelines
- timeline events auto-constructed from extracted dates and document uploads
- supports manual entries

### semantic search
- natural language search across all documents using pgvector cosine similarity on openai embeddings

### multi-tenant architecture
- full org isolation with role-based access control (admin, lawyer, paralegal)
- every query scoped to organization, middleware enforces tenant isolation

### background processing
- celery workers handle document extraction asynchronously so the ui stays responsive

### dashboard analytics
- at-a-glance stats for active matters, open tasks, upcoming deadlines, and recent activity

---

## tech stack

| layer | tech |
|-------|------|
| frontend | next.js 14 (app router), typescript, tailwind css |
| data fetching | tanstack query |
| forms | react hook form + zod |
| charts | recharts |
| backend | fastapi, python 3.11 |
| orm | sqlalchemy 2.0 (async) |
| database | postgresql 16 + pgvector |
| migrations | alembic |
| ai | openai gpt-4o-mini (extraction), text-embedding-3-small (search) |
| cache/queue | redis 7 |
| background jobs | celery |
| file storage | minio (s3-compatible) |
| auth | jwt (access + refresh tokens), bcrypt |
| infra | docker compose |

---

## getting started

### prerequisites
- docker & docker compose
- an openai api key

### 1. clone and configure

```bash
git clone https://github.com/tristan-guevarra/caseflow-io.git
cd caseflow-io
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...
```

### 2. start everything

```bash
make up
make migrate
make seed
```

### 3. open it up

| service | url |
|---------|-----|
| frontend | http://localhost:3000 |
| api docs (swagger) | http://localhost:8000/docs |
| api docs (redoc) | http://localhost:8000/redoc |

---

## project structure

```
caseflow/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   route handlers
│   │   ├── core/               config, security, dependencies
│   │   ├── models/             sqlalchemy orm models
│   │   ├── schemas/            pydantic request/response schemas
│   │   ├── services/           business logic (ai, storage, audit)
│   │   ├── tasks/              celery background tasks
│   │   ├── prompts/            ai prompt templates
│   │   └── middleware/         tenant isolation, logging
│   ├── migrations/             alembic migration files
│   └── tests/                  pytest test suite
├── frontend/
│   └── src/
│       ├── app/                pages (app router)
│       ├── components/         layout, ui components
│       ├── contexts/           auth context
│       ├── hooks/              custom react hooks
│       ├── lib/                api client, utils
│       └── types/              typescript definitions
├── docker/                     dockerfiles
├── scripts/                    seed scripts
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## how the ai pipeline works

1. user uploads a pdf or docx to a matter
2. file is stored in minio (s3-compatible object storage)
3. a celery task picks up the job and extracts raw text
4. text is chunked and sent to gpt-4o-mini with a structured extraction prompt
5. the response is validated against a strict pydantic schema (retries up to 3x on invalid output)
6. structured extractions (parties, deadlines, obligations, clauses, risk flags) are stored in the database
7. embedding vectors are generated via text-embedding-3-small and stored in pgvector
8. tasks are auto-created from detected deadlines, timeline events from key dates
9. the user gets a notification when processing is complete

---

## useful commands

```bash
make up              # build and start all services
make down            # stop all services
make migrate         # run alembic database migrations
make seed            # seed the database with sample data
make test            # run backend test suite
make test-frontend   # run frontend tests
make logs            # tail logs for all containers
make reset           # full teardown and rebuild (drops volumes)
make lint            # run linters (ruff + eslint)
make shell-backend   # open a shell in the backend container
make shell-db        # open psql in the database container
```

---

## architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│   next.js    │───>│   fastapi     │───>│  postgresql    │
│   frontend   │    │   backend     │    │  + pgvector    │
└─────────────┘    └──────┬───────┘    └───────────────┘
                          │
                   ┌──────┴───────┐
                   │    redis      │
                   │  (cache +     │
                   │   queue)      │
                   └──────┬───────┘
                          │
                   ┌──────┴───────┐    ┌───────────────┐
                   │   celery      │───>│  openai api    │
                   │   workers     │    │  gpt-4o-mini   │
                   └──────────────┘    └───────────────┘
                          │
                   ┌──────┴───────┐
                   │    minio      │
                   │  (s3 storage) │
                   └──────────────┘
```

---

## license

proprietary. all rights reserved.
