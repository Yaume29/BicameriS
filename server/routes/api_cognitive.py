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
    """Toggle auto-scaffolding FULL (Level 1) via Switchboard"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    switchboard.toggle("auto_scaffolding_full", req.enabled)
    return {"status": "success", "level": "full", "enabled": req.enabled}


@router.get("/conductor/auto_scaffolding")
async def get_auto_scaffolding():
    """Get auto-scaffolding status (all 3 levels) via Switchboard"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    return {
        "full": switchboard.is_active("auto_scaffolding_full"),
        "limited": switchboard.is_active("auto_scaffolding_limited"),
        "optimization": switchboard.is_active("auto_optimization")
    }


@router.put("/conductor/auto_scaffolding/limited")
async def toggle_auto_scaffolding_limited(req: ScaffoldingToggle):
    """Toggle auto-scaffolding LIMITED (Level 2) - file creation + web tools"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    switchboard.toggle("auto_scaffolding_limited", req.enabled)
    return {"status": "success", "level": "limited", "enabled": req.enabled}


@router.put("/conductor/auto_optimization")
async def toggle_auto_optimization(req: ScaffoldingToggle):
    """Toggle auto-optimization (Level 3) - LLM params only"""
    from core.system.switchboard import get_switchboard

    switchboard = get_switchboard()
    switchboard.toggle("auto_optimization", req.enabled)
    return {"status": "success", "level": "optimization", "enabled": req.enabled}


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


# ============================================
# STM MODULES ENDPOINTS
# ============================================


@router.get("/stm/status")
async def stm_status():
    """Get STM engine status"""
    try:
        from core.cognition.stm_engine import get_stm_engine
        stm = get_stm_engine()
        return stm.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.post("/stm/toggle/{module_id}")
async def stm_toggle(module_id: str, request: Request):
    """Toggle a STM module"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        
        from core.cognition.stm_engine import get_stm_engine
        stm = get_stm_engine()
        
        if enabled:
            stm.enable_module(module_id)
        else:
            stm.disable_module(module_id)
        
        return {"status": "ok", "module": module_id, "enabled": enabled}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/stm/apply")
async def stm_apply(request: Request):
    """Apply STM modules to text"""
    try:
        data = await request.json()
        text = data.get("text", "")
        
        from core.cognition.stm_engine import get_stm_engine
        stm = get_stm_engine()
        
        result = stm.apply(text)
        return {"status": "ok", "original": text, "transformed": result}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# AUTOTUNE ENDPOINTS
# ============================================


@router.get("/autotune/status")
async def autotune_status():
    """Get AutoTune engine status"""
    try:
        from core.cognition.auto_tune import get_autotune_engine
        engine = get_autotune_engine()
        return engine.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.post("/autotune/toggle")
async def autotune_toggle(request: Request):
    """Toggle AutoTune"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        
        from core.cognition.auto_tune import get_autotune_engine
        engine = get_autotune_engine()
        
        if enabled:
            engine.enable()
        else:
            engine.disable()
        
        return {"status": "ok", "enabled": enabled}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/autotune/tune")
async def autotune_tune(request: Request):
    """Tune parameters for text"""
    try:
        data = await request.json()
        text = data.get("text", "")
        
        from core.cognition.auto_tune import get_autotune_engine
        engine = get_autotune_engine()
        
        result = engine.tune(text)
        return {
            "status": "ok",
            "context": result.context.value,
            "confidence": result.confidence,
            "params": {
                "temperature": result.params.temperature,
                "top_p": result.params.top_p,
                "top_k": result.params.top_k,
                "frequency_penalty": result.params.frequency_penalty,
                "presence_penalty": result.params.presence_penalty,
                "repetition_penalty": result.params.repetition_penalty
            },
            "reasoning": result.reasoning
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/autotune/feedback")
async def autotune_feedback(request: Request):
    """Submit feedback for AutoTune learning"""
    try:
        data = await request.json()
        context = data.get("context", "balanced")
        rating = data.get("rating", 0)
        
        from core.cognition.auto_tune import get_autotune_engine
        engine = get_autotune_engine()
        
        engine.feedback(context, rating)
        return {"status": "ok", "message": "Feedback enregistré"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============================================
# LEGACY/COMPATIBILITY ENDPOINTS
# ============================================


@router.get("/think/history")
async def think_history(limit: int = 10):
    """Get thinking history (alias for conductor/history)"""
    try:
        from server.extensions import registry
        
        if registry.conductor and hasattr(registry.conductor, 'task_history'):
            history = registry.conductor.task_history[-limit:]
            return history
        return []
    except Exception as e:
        return []


@router.get("/logs")
async def get_logs(type: str = "all", limit: int = 100):
    """Get system logs"""
    try:
        from core.system.telemetry import get_telemetry
        telemetry = get_telemetry()
        
        if telemetry:
            if type == "ERREUR":
                logs = [l for l in telemetry.buffer if l.get("type") == "ERREUR"][-limit:]
            else:
                logs = list(telemetry.buffer)[-limit:]
            return logs
        return []
    except Exception as e:
        return []


@router.get("/logs_by_type")
async def logs_by_type():
    """Get logs grouped by type"""
    try:
        from core.system.telemetry import get_telemetry
        telemetry = get_telemetry()
        
        if telemetry:
            by_type = {}
            for log in telemetry.buffer:
                log_type = log.get("type", "unknown")
                if log_type not in by_type:
                    by_type[log_type] = 0
                by_type[log_type] += 1
            return by_type
        return {}
    except Exception as e:
        return {}


@router.get("/entropy")
async def get_entropy():
    """Get entropy/pulse data"""
    try:
        from core.hardware.entropy_generator import get_entropy_generator
        entropy = get_entropy_generator()
        
        return {
            "pulse": entropy.get_pulse(),
            "mood": entropy._interpret_mood(entropy.last_pulse)
        }
    except Exception as e:
        return {"pulse": 0.5, "mood": "UNKNOWN"}


@router.get("/agents")
async def get_agents():
    """Get list of agents"""
    try:
        # Return available agents
        return {
            "agents": [
                {"name": "Conductor", "status": "active" if registry.conductor else "inactive"},
                {"name": "Corps Calleux", "status": "active" if registry.corps_calleux else "inactive"},
                {"name": "CriticAgent", "status": "available"},
                {"name": "ResearchAgent", "status": "available"},
                {"name": "CoderAgent", "status": "available"},
            ]
        }
    except Exception as e:
        return {"agents": []}


@router.get("/agents/providers")
async def get_agent_providers():
    """Get agent providers"""
    return {"providers": []}


@router.get("/memory/stats")
async def memory_stats():
    """Get memory statistics"""
    try:
        from core.system.traumatic_memory import get_traumatic_memory
        memory = get_traumatic_memory()
        
        return memory.get_stats()
    except Exception as e:
        return {"total": 0, "errors": 0, "success": 0}


@router.get("/memory/summary")
async def memory_summary(hours: int = 24):
    """Get memory summary for last N hours"""
    try:
        from core.system.traumatic_memory import get_traumatic_memory
        memory = get_traumatic_memory()
        
        recent = memory.get_recent_failures(hours=hours)
        return {"summary": recent}
    except Exception as e:
        return {"summary": []}
