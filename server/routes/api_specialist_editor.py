"""
API Routes for Specialist Editor
=================================
Endpoints pour l'Éditeur Spécialiste.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional

router = APIRouter(prefix="/specialist", tags=["specialist"])


@router.post("/activate")
async def activate_editor(request: Request):
    """Active l'Éditeur Spécialiste"""
    try:
        data = await request.json()
        mode = data.get("mode", "chat")
        capabilities = data.get("capabilities", {})
        
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        result = editor.activate(mode=mode, capabilities=capabilities)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deactivate")
async def deactivate_editor():
    """Désactive l'Éditeur Spécialiste"""
    try:
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        result = editor.deactivate()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process")
async def process_input(request: Request):
    """Traite une entrée selon le mode actuel"""
    try:
        data = await request.json()
        input_text = data.get("input", "")
        context = data.get("context", {})
        
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        result = editor.process(input_text, context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode")
async def set_mode(request: Request):
    """Change le mode de l'éditeur"""
    try:
        data = await request.json()
        mode = data.get("mode", "chat")
        
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        result = editor.set_mode(mode)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """Retourne le statut de l'éditeur"""
    try:
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        return editor.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thinking-modes")
async def get_thinking_modes():
    """Retourne les modes de pensée disponibles"""
    try:
        from core.agents.specialized.thinking_modes import get_thinking_mode_manager
        manager = get_thinking_mode_manager()
        
        if manager:
            return {"modes": manager.get_available_modes()}
        return {"modes": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logic-templates")
async def get_logic_templates():
    """Retourne les templates logiques disponibles"""
    try:
        from core.agents.specialized.logic_templates import get_logic_template_engine
        engine = get_logic_template_engine()
        
        return {"templates": engine.get_all_templates()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory-status")
async def get_memory_status():
    """Retourne le statut de la mémoire"""
    try:
        from core.agents.specialized.memory_sleep import get_memory_sleep_manager
        manager = get_memory_sleep_manager()
        
        return manager.get_sleep_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
