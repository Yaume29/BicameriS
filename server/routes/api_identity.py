"""
API Identity Routes
===================
Identity management endpoints
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["identity"])


@router.post("/identity/save")
async def identity_save(request: Request):
    """Save identity"""
    try:
        data = await request.json()
        return {
            "status": "ok",
            "name": data.get("name", "Aetheris"),
            "email": data.get("email", "admin@local")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
