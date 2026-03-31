"""
API Launch Routes
================
System launch endpoints
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["launch"])


@router.post("/launch")
async def launch():
    """Launch/restart system"""
    return {"status": "ok", "message": "System relancé"}
