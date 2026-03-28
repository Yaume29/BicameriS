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
    """Legacy compatibility - redirects to CorpsCalleux"""
    return get_corps_calleux()


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
async def autonomous_status(corps=Depends(get_corps_calleux)):
    """Get autonomous thinker status"""
    is_running = (
        await asyncio.to_thread(corps.is_autonomous) if hasattr(corps, "is_autonomous") else False
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


@router.get("/stats")
async def get_stats(corps_calleux=Depends(get_corps_calleux)):
    """Get cognitive system stats"""
    try:
        cycles = 0
        if hasattr(corps_calleux, 'history'):
            cycles = len(corps_calleux.history)
        
        return {
            "thinker": {
                "is_thinking": False,
                "cycles": cycles
            },
            "corps_calleux": {
                "connected": corps_calleux.left is not None and corps_calleux.right is not None if corps_calleux else False,
                "cycles": cycles
            }
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/think/start")
async def start_thinking(corps_calleux=Depends(get_corps_calleux)):
    """Start autonomous thinking loop"""
    try:
        if hasattr(corps_calleux, 'start_autonomous'):
            corps_calleux.start_autonomous()
        return {"status": "ok", "message": "Boucle de pensée démarrée"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/think/stop")
async def stop_thinking(corps_calleux=Depends(get_corps_calleux)):
    """Stop autonomous thinking loop"""
    try:
        if hasattr(corps_calleux, 'stop_autonomous'):
            corps_calleux.stop_autonomous()
        return {"status": "ok", "message": "Boucle de pensée arrêtée"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/think/set_interval")
async def set_think_interval(request: Request, corps_calleux=Depends(get_corps_calleux)):
    """Set thinking interval"""
    try:
        data = await request.json()
        interval = data.get("interval", 5)
        if hasattr(corps_calleux, 'think_interval'):
            corps_calleux.think_interval = interval
        return {"status": "ok", "interval": interval}
    except Exception as e:
        return {"status": "error", "error": str(e)}
