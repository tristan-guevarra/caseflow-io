# combines all the endpoint routers into one api router

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.documents import router as documents_router
from app.api.v1.endpoints.matters import router as matters_router
from app.api.v1.endpoints.tasks import router as tasks_router
from app.api.v1.endpoints.other import (
    audit_router,
    dashboard_router,
    notification_router,
    org_router,
    search_router,
    timeline_router,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(org_router)
api_router.include_router(matters_router)
api_router.include_router(documents_router)
api_router.include_router(tasks_router)
api_router.include_router(timeline_router)
api_router.include_router(search_router)
api_router.include_router(dashboard_router)
api_router.include_router(notification_router)
api_router.include_router(audit_router)
