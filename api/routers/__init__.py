"""
Routers for PDF Platform API.

All application routers are defined in separate modules and imported here.
"""

from .auth import router as auth_router
from .payments import router as payments_router
from .admin import router as admin_router
from .session import router as session_router
from .upload import router as upload_router

__all__ = ["auth_router", "payments_router", "session_router", "upload_router"]
