"""
System Control API Routes
=======================
Endpoints for Switchboard state management.
Controls laboratory features (autonomous loop, auto-forge, docker, etc.)
"""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any
import logging

from server.extensions import registry, get_switchboard
from core.system.config_manager import get_config

router = APIRouter(prefix="/api/system", tags=["system_control"])
logger = logging.getLogger("api_system")


class ToggleRequest(BaseModel):
    state: bool


class InitRequest(BaseModel):
    persistent_autothink: bool = False


@router.get("/init/status")
async def get_init_status():
    """Récupère le statut d'initialisation du système."""
    config = get_config()
    return {
        "initialized": config.config.system.initialized,
        "persistent_autothink": config.config.system.persistent_autothink,
        "auto_start_scheduler": config.config.system.auto_start_scheduler
    }


@router.post("/init/start")
async def start_initialization(req: InitRequest):
    """Démarre l'initialisation du système."""
    from core.system.switchboard import get_switchboard
    
    config = get_config()
    config.config.system.initialized = True
    config.config.system.persistent_autothink = req.persistent_autothink
    config.save()
    
    switchboard = get_switchboard()
    switchboard.toggle("autonomous_loop", req.persistent_autothink)
    
    logger.info(f"[INIT] Système initialisé - persistent_autothink: {req.persistent_autothink}")
    
    return {
        "status": "ok",
        "initialized": True,
        "persistent_autothink": req.persistent_autothink,
        "message": "Système initialisé. Veuillez redémarrer le serveur pour appliquer les changements."
    }


@router.post("/init/stop")
async def stop_initialization():
    """Arrête et réinitialise le système (mode inerte)."""
    from core.system.switchboard import get_switchboard
    
    switchboard = get_switchboard()
    switchboard.toggle("autonomous_loop", False)
    switchboard.toggle("auto_scaffolding_full", False)
    
    config = get_config()
    config.config.system.initialized = False
    config.save()
    
    logger.info("[INIT] Système mis en mode inerte")
    
    return {
        "status": "ok",
        "initialized": False,
        "message": "Système en mode inerte. Veuillez redémarrer le serveur."
    }


@router.put("/persistent/autothink")
async def set_persistent_autothink(req: ToggleRequest):
    """Active ou désactive le mode persistant autothink."""
    config = get_config()
    config.config.system.persistent_autothink = req.state
    config.save()
    
    switchboard = get_switchboard()
    switchboard.toggle("autonomous_loop", req.state)
    
    logger.info(f"[PERSISTENT] autothink: {req.state}")
    
    return {
        "status": "ok",
        "persistent_autothink": req.state
    }


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
