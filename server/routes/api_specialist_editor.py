"""
API Routes for Specialist Editor
=================================
Endpoints pour l'Éditeur Spécialiste.
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import Dict, List, Optional
import asyncio
import json
import logging
import uuid

logger = logging.getLogger("api.specialist")

router = APIRouter(prefix="/specialist", tags=["specialist"])

# Store for active streams
_active_streams: Dict[str, asyncio.Queue] = {}


async def stream_generator(session_id: str, queue: asyncio.Queue):
    """Generator that yields events from the queue"""
    yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"
    
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=30)
            yield f"data: {json.dumps(event)}\n\n"
            
            if event.get("type") == "complete":
                break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
            break
    
    if session_id in _active_streams:
        del _active_streams[session_id]


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


@router.get("/stream")
async def stream_specialist(request: Request):
    """SSE stream pour les mises à jour en temps réel"""
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _active_streams[session_id] = queue
    
    async def event_generator():
        yield f"event: connected\ndata: {json.dumps({'session_id': session_id})}\n\n"
        
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
                
                if event.get("type") == "complete":
                    break
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
                break
        
        if session_id in _active_streams:
            del _active_streams[session_id]
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stream/session")
async def create_stream_session(request: Request):
    """Crée une session de streaming"""
    try:
        data = await request.json()
        mode = data.get("mode", "chat")
        
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        editor.activate(mode=mode)
        
        session_id = str(uuid.uuid4())
        queue: asyncio.Queue = asyncio.Queue()
        _active_streams[session_id] = queue
        
        return {
            "status": "ok",
            "session_id": session_id,
            "stream_url": f"/api/specialist/stream/{session_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream/process")
async def process_with_stream(request: Request):
    """Traite une entrée avec streaming des résultats"""
    try:
        data = await request.json()
        input_text = data.get("input", "")
        context = data.get("context", {})
        session_id = context.get("session_id", str(uuid.uuid4()))
        
        queue = _active_streams.get(session_id) or asyncio.Queue()
        
        await queue.put({"type": "thinking", "role": "assistant-left", "content": "Analyse en cours..."})
        
        from core.agents.specialized.specialist_editor import get_specialist_editor
        editor = get_specialist_editor()
        
        result = editor.process(input_text, context)
        
        await queue.put({
            "type": "message",
            "role": "corpus",
            "content": json.dumps(result, indent=2)
        })
        
        await queue.put({"type": "complete", "session_id": session_id})
        
        return {"status": "ok", "session_id": session_id, "result": result}
        
    except Exception as e:
        logger.error(f"[Stream Process] Error: {e}")
        return {"status": "error", "message": str(e)}
