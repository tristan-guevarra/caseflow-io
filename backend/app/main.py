# this is the main app entry point

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.middleware.logging import RequestLoggingMiddleware

settings = get_settings()

# set up structured logging - pretty console in dev, json in prod
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.DEBUG else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

# create the fastapi app
app = FastAPI(
    title="AI CaseFlow",
    description="AI-powered legal matter management platform. Extracts intelligence from legal documents, auto-generates tasks and timelines.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# hook up all the api routes
app.include_router(api_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "healthy", "service": "ai-caseflow", "version": "1.0.0"}
