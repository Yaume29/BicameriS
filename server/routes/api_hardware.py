"""
Hardware API Routes
=================
Endpoints for thermal, entropy, models
FastAPI Dependency Injection pattern with async delegation
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from server.extensions import registry

router = APIRouter(prefix="/api/hardware", tags=["hardware"])


# ==============================================================================
# HARDWARE CONFIG STORAGE
# ==============================================================================

_hardware_config = {
    "n_gpu_layers": -1,
    "n_threads": 0,
    "os_vram_reserve": 2.0,
    "kv_cache_reserve": 1.5,
    "use_mmap": True,
    "use_mlock": False,
}


# ==============================================================================
# DEPENDENCY INJECTORS
# ==============================================================================


def get_thermal():
    """Resolve thermal governor or reject request"""
    if not registry.thermal:
        raise HTTPException(status_code=501, detail="Thermal Subsystem Offline")
    return registry.thermal


def get_entropy():
    if not registry.entropy:
        raise HTTPException(status_code=501, detail="Entropy Generator Offline")
    return registry.entropy


def get_modelscanner():
    if not registry.modelscanner:
        raise HTTPException(status_code=501, detail="Model Scanner Offline")
    return registry.modelscanner


# ==============================================================================
# PYDANTIC MODELS
# ==============================================================================


class UndervoltRequest(BaseModel):
    profile: str = "AGGRESSIVE"


# ==============================================================================
# ENDPOINTS
# ==============================================================================


@router.get("/thermal/status")
async def thermal_status(thermal=Depends(get_thermal)):
    """Get current thermal status - delegated to threadpool"""
    return await asyncio.to_thread(thermal.get_status)


@router.post("/thermal/prepare")
async def thermal_prepare(strategy: str = "EVOLVE", thermal=Depends(get_thermal)):
    """Prepare substrate before inference - delegated to threadpool"""
    await asyncio.to_thread(thermal.prepare_for_inference, strategy)
    return {"status": "prepared"}


@router.post("/thermal/undervolt")
async def thermal_undervolt(req: UndervoltRequest, thermal=Depends(get_thermal)):
    """Apply undervolting profile - delegated to threadpool"""
    success = await asyncio.to_thread(thermal.apply_undervolt, req.profile)
    return {"status": "success" if success else "failed", "profile": req.profile}


@router.get("/entropy/pulse")
async def entropy_pulse(entropy=Depends(get_entropy)):
    """Get current entropy pulse - delegated to threadpool"""
    return await asyncio.to_thread(entropy.get_pulse)


@router.get("/models")
async def list_models(modelscanner=Depends(get_modelscanner)):
    """List available models - delegated to threadpool"""
    return await asyncio.to_thread(modelscanner.list_models)


@router.get("/topology")
async def hardware_topology():
    """Get hardware topology (CPU, RAM, VRAM)"""
    try:
        from core.hardware.profiler import get_profiler

        profiler = get_profiler()
        return {
            "cpu_threads": profiler.cpu_cores,
            "ram_gb": profiler.ram_total_gb,
            "vram_gb": profiler.vram_total_gb,
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/config")
async def get_hardware_config():
    """Get saved hardware config"""
    return {"config": _hardware_config}


@router.post("/config")
async def save_hardware_config(config: dict):
    """Save hardware config"""
    global _hardware_config
    _hardware_config.update(config)

    try:
        from core.hardware.profiler import set_hardware_config

        set_hardware_config(_hardware_config)
    except Exception:
        pass

    return {"status": "ok"}
