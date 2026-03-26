"""
Cognitive API Routes
===================
Endpoints for conductor, thinking, hemispheres
FastAPI Dependency Injection pattern with async delegation
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server.extensions import registry

router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])


# ==============================================================================
# DEPENDENCY INJECTORS
# ==============================================================================


def get_conductor():
    """Resolve conductor or reject request immediately"""
    if not registry.conductor:
        raise HTTPException(status_code=501, detail="Conductor Subsystem Offline")
    return registry.conductor


def get_corps_calleux():
    if not registry.corps_calleux:
        raise HTTPException(status_code=501, detail="Corps Calleux Subsystem Offline")
    return registry.corps_calleux


def get_autonomous_thinker():
    if not registry.autonomous_thinker:
        raise HTTPException(status_code=501, detail="Autonomous Thinker Offline")
    return registry.autonomous_thinker


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================


class ThinkRequest(BaseModel):
    prompt: str
    context: str = ""


class SandboxRequest(BaseModel):
    code: str
    filename: str = "sandbox.py"
    timeout: int = 10


class ScaffoldingToggle(BaseModel):
    enabled: bool


# ==============================================================================
# ENDPOINTS - All blocking calls delegated to threadpool
# ==============================================================================


@router.get("/conductor/stats")
async def conductor_stats(conductor=Depends(get_conductor)):
    """Get conductor statistics"""
    return await asyncio.to_thread(conductor.get_stats)


@router.get("/conductor/history")
async def conductor_history(limit: int = 20, conductor=Depends(get_conductor)):
    """Get task history"""
    return await asyncio.to_thread(conductor.get_history, limit)


@router.put("/conductor/auto_scaffolding")
async def toggle_auto_scaffolding(req: ScaffoldingToggle):
    """Toggle auto-scaffolding via Switchboard"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    switchboard.toggle("auto_scaffolding", req.enabled)
    return {"status": "success", "enabled": req.enabled}


@router.get("/conductor/auto_scaffolding")
async def get_auto_scaffolding():
    """Get auto-scaffolding status via Switchboard"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    return {"enabled": switchboard.is_active("auto_scaffolding")}


@router.post("/think")
async def think(req: ThinkRequest, corps_calleux=Depends(get_corps_calleux)):
    """Trigger thinking process - uses dialogue_interieur"""
    result = await asyncio.to_thread(corps_calleux.dialogue_interieur, req.prompt, req.context)
    return result


@router.post("/sandbox/execute")
async def sandbox_execute(req: SandboxRequest, conductor=Depends(get_conductor)):
    """Execute code in sandbox - delegated to threadpool"""
    result = await asyncio.to_thread(conductor.execute_sandbox, req.code, req.filename, req.timeout)
    return result


@router.get("/autonomous/status")
async def autonomous_status(thinker=Depends(get_autonomous_thinker)):
    """Get autonomous thinker status"""
    is_running = (
        await asyncio.to_thread(thinker.is_running) if hasattr(thinker, "is_running") else False
    )
    return {"running": is_running}


@router.get("/thoughts")
async def get_thoughts(limit: int = 30):
    """Get recent thoughts from Telemetry Ring Buffer (O(1) RAM read)"""
    from core.system.telemetry import get_telemetry

    telemetry = get_telemetry()
    if not telemetry:
        return []

    thoughts = telemetry.get_recent_thoughts(limit=limit)
    filtered = [t for t in thoughts if t.get("type") in ("autonomous_thought", "thought")]
    return filtered


class CrucibleRequest(BaseModel):
    prompt: str
    max_iterations: int = 4


@router.post("/crucible")
async def run_crucible(req: CrucibleRequest, conductor=Depends(get_conductor)):
    """Exécute l'hyper-cognition dans une chambre blanche isolée."""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()

    lockdown_protocol = {"autonomous_loop": False, "hyper_cognition_mode": True}

    def _execute_crucible_sync():
        with switchboard.override_states(lockdown_protocol):
            return conductor._mode_crucible(req.prompt, max_iterations=req.max_iterations)

    try:
        result = await asyncio.to_thread(_execute_crucible_sync)
        return result
    except Exception as e:
        return {"status": "ERROR", "error": f"Le Creuset a explosé : {str(e)}"}
