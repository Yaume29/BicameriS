"""
API Laboratoire Routes
=====================
Operator, conscientisation, crucible endpoints
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["laboratoire"])


@router.get("/operator/profile")
async def operator_profile():
    """Get operator profile"""
    return {
        "sensitivity": 0.5,
        "impact": 0.5,
        "active": True,
        "name": "Operator",
        "email": "admin@local"
    }


@router.put("/operator/adjust")
@router.post("/operator/adjust")  # Support both PUT and POST
async def operator_adjust(request: Request):
    """Adjust operator parameters"""
    try:
        data = await request.json()
        return {
            "status": "ok",
            "sensitivity": data.get("sensitivity", 0.5),
            "impact": data.get("impact", 0.5)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/operator/reset")
async def operator_reset():
    """Reset operator to defaults"""
    return {"status": "ok", "sensitivity": 0.5, "impact": 0.5}


@router.get("/conscientisation/start")
async def conscientisation_get():
    """Get conscientisation status"""
    return {
        "active": False,
        "level": 0,
        "log": []
    }


@router.post("/conscientisation/start")
async def conscientisation_start(request: Request):
    """Start conscientisation"""
    try:
        data = await request.json()
        return {
            "status": "ok",
            "active": True,
            "level": data.get("level", 0.5)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/conscientisation/stop")
async def conscientisation_stop():
    """Stop conscientisation"""
    return {"status": "ok", "active": False}


@router.get("/conscientisation/status")
async def conscientisation_status():
    """Get conscientisation status"""
    return {
        "active": False,
        "level": 0,
        "log": []
    }


@router.get("/conscientisation/log")
async def conscientisation_log():
    """Get conscientisation log"""
    return {
        "log": []
    }


@router.post("/cognitive/crucible")
async def cognitive_crucible(request: Request):
    """Run cognitive crucible"""
    try:
        data = await request.json()
        return {
            "status": "ok",
            "result": "Crucible executed",
            "cycles": 1
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
