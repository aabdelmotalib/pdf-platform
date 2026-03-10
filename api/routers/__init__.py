"""
Routers for PDF Platform API.

All application routers are defined in separate modules and imported here.
"""

from .auth import router as auth_router
from .upload import router as upload_router

__all__ = ["auth_router", "upload_router"]
