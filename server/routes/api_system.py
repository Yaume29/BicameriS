"""
System Control API Routes
========================
Endpoints for Switchboard state management.
Controls laboratory features (autonomous loop, auto-forge, docker, etc.)
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from server.extensions import registry, get_switchboard

router = APIRouter(prefix="/api/system", tags=["system_control"])


class ToggleRequest(BaseModel):
    state: bool


@router.get("/switches", response_model=Dict[str, bool])
async def list_switches():
    """Récupère l'état de tous les interrupteurs du labo."""
    switchboard = get_switchboard()
    return switchboard.get_all_states()


@router.post("/switches/{feature}")
async def toggle_switch(feature: str, req: ToggleRequest):
    """Bascule un interrupteur avec détection de conflits."""
    switchboard = get_switchboard()
    result = switchboard.toggle(feature, req.state)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result.get("error", "Unknown error"))

    return {
        "status": "success",
        "feature": feature,
        "state": req.state,
        "conflicts": result.get("conflicts", []),
    }


@router.get("/switches/{feature}/conflicts")
async def check_switch_conflicts(feature: str, state: bool = True):
    """Vérifie les conflits potentiels pour un interrupteur."""
    switchboard = get_switchboard()
    conflicts = switchboard.check_conflicts(feature, state)
    return {"feature": feature, "state": state, "conflicts": conflicts}


@router.get("/status")
async def system_status():
    """État global du système"""
    return {
        "switchboard": get_switchboard().get_all_states(),
        "endocrine": get_switchboard().get_endocrine_config(),
        "corps_calleux": registry.corps_calleux is not None,
        "conductor": registry.conductor is not None,
        "inference_manager": registry.inference_manager is not None,
    }


class EndocrineConfig(BaseModel):
    enabled: bool
    sensitivity: float
    impact: float


@router.put("/endocrine")
async def update_endocrine(config: EndocrineConfig):
    """Met à jour la configuration endocrine (hardware influence on LLM)"""
    sb = get_switchboard()
    sb.set_endocrine_config(config.enabled, config.sensitivity, config.impact)
    return {"status": "success", "config": config}
