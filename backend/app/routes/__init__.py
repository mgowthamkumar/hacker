from backend.app.routes.auth import router as auth_router
from backend.app.routes.profile import router as profile_router
from backend.app.routes.jobs import router as jobs_router

__all__ = ["auth_router", "profile_router", "jobs_router"]
