"""
API Identity Routes
==================
Entity identity management endpoints
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["identity"])


@router.get("/identity")
async def get_identity():
    """Get current entity identity"""
    try:
        from core.system.identity_manager import get_identity_manager
        manager = get_identity_manager()
        return manager.get_identity()
    except Exception as e:
        return {"error": str(e)}


@router.post("/identity/save")
async def identity_save(request: Request):
    """Save identity (name, description, personality)"""
    try:
        data = await request.json()
        
        from core.system.identity_manager import get_identity_manager
        manager = get_identity_manager()
        
        if "name" in data:
            manager.set_name(data["name"])
        
        if "description" in data:
            manager.set_description(data["description"])
        
        if "personality" in data:
            manager.set_personality(data["personality"])
        
        return {
            "status": "ok",
            "identity": manager.get_identity()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/identity/reset")
async def identity_reset():
    """Reset identity to defaults"""
    try:
        from core.system.identity_manager import get_identity_manager
        manager = get_identity_manager()
        manager.set_name("Aetheris")
        manager.set_description("A bicameral cognitive entity")
        manager.set_personality({
            "tone": "thoughtful and direct",
            "style": "analytical yet creative",
            "traits": ["curious", "honest", "helpful"]
        })
        return {"status": "ok", "message": "Identity reset to defaults"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
