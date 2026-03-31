"""
Server Middlewares
=================
Security and authentication middlewares
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for Diadikos & Palladion"""

    # Routes that require special handling
    ADMIN_ROUTES = [
        "/api/security",
        "/api/config",
        "/api/admin",
    ]

    SENSITIVE_ROUTES = [
        "/api/files/write",
        "/api/shell",
        "/api/execute",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Log all requests
        logger.info(f"{request.method} {path}")

        # Check for sensitive operations
        for sensitive in self.SENSITIVE_ROUTES:
            if path.startswith(sensitive):
                logger.warning(f"Sensitive operation: {path}")
                # Could add additional auth checks here

        response = await call_next(request)
        return response


class CORSMiddleware:
    """Custom CORS handling"""

    ALLOWED_ORIGINS = ["*"]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["*"]

    @staticmethod
    def get_headers() -> dict:
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": ", ".join(CORSMiddleware.ALLOWED_METHODS),
            "Access-Control-Allow-Headers": "*",
        }
