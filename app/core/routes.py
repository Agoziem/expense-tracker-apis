from fastapi import APIRouter
from app.api.v1.auth.routes.routes import auth_router
from app.api.v1.auth.routes.user_routes import user_router
from app.api.v1.files.routes import file_router


router = APIRouter()

# Include other routers
router.include_router(auth_router, prefix="/auth", tags=["authentication"])

# user router and profile router
router.include_router(user_router, prefix="/user", tags=["user"])


# file upload router
router.include_router(file_router, prefix="/file", tags=["file handler"])


# Add other routers as needed