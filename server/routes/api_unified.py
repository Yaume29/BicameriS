"""
API Unified Routes
==================
Endpoints pour le module unifié de dialogue bicaméral.

Philosophie: "La beauté c'est vous, pas les outils qui vous sublime"
"""

import logging
import json
from typing import Dict, Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(tags=["unified"])


class UnifiedChatRequest(BaseModel):
    """Requête de chat unifié"""
    message: str
    mode: str = "emergence"  # emergence, knowledge, hybrid


class UnifiedModeRequest(BaseModel):
    """Requête de changement de mode"""
    mode: str  # emergence, knowledge, hybrid


class RAGIndexRequest(BaseModel):
    """Requête d'indexation RAG"""
    content: str
    source: str = "custom"
    category: str = "general"


@router.get("/unified/status")
async def unified_status():
    """Statut du module unifié"""
    try:
        from core.cognition.unified_engine import get_unified_engine
        engine = get_unified_engine()
        stats = engine.get_stats()
        
        # Connecter les hémisphères si disponibles
        from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
        left = get_left_hemisphere()
        right = get_right_hemisphere()
        
        if left and right and not engine.codeur:
            engine.set_hemispheres(left, right)
        
        return {
            "status": "operational",
            "mode": "emergence" if not engine.rag_enabled else "knowledge",
            "hemispheres_connected": engine.codeur is not None and engine.reviewer is not None,
            **stats
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/mode")
async def unified_set_mode(req: UnifiedModeRequest):
    """Configure le mode de fonctionnement"""
    try:
        from core.cognition.unified_engine import get_unified_engine, UnifiedMode
        engine = get_unified_engine()
        
        mode_map = {
            "emergence": UnifiedMode.EMERGENCE,
            "knowledge": UnifiedMode.KNOWLEDGE,
            "hybrid": UnifiedMode.HYBRID
        }
        
        mode = mode_map.get(req.mode, UnifiedMode.EMERGENCE)
        engine.set_mode(mode)
        
        # Configurer le RAG si nécessaire
        if mode == UnifiedMode.KNOWLEDGE:
            from core.system.rag_indexer import get_rag_indexer
            rag = get_rag_indexer()
            rag.enable()
        
        return {
            "status": "ok",
            "mode": req.mode,
            "message": f"Mode {req.mode} activé"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/session")
async def unified_create_session(req: UnifiedChatRequest):
    """Crée une nouvelle session de dialogue"""
    try:
        from core.cognition.unified_engine import get_unified_engine, UnifiedMode
        engine = get_unified_engine()
        
        mode_map = {
            "emergence": UnifiedMode.EMERGENCE,
            "knowledge": UnifiedMode.KNOWLEDGE,
            "hybrid": UnifiedMode.HYBRID
        }
        
        mode = mode_map.get(req.mode, UnifiedMode.EMERGENCE)
        session = engine.create_session(mode)
        
        return {
            "status": "ok",
            "session_id": session.session_id,
            "mode": req.mode
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/chat/{session_id}")
async def unified_chat(session_id: str, req: UnifiedChatRequest):
    """Envoie un message dans une session"""
    try:
        from core.cognition.unified_engine import get_unified_engine
        engine = get_unified_engine()
        
        session = engine.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        # Générer la réponse en streaming
        async def generate():
            async for event in engine.process_message(session_id, req.message):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive"
            }
        )
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.websocket("/ws/unified/{session_id}")
async def unified_websocket(websocket: WebSocket, session_id: str):
    """WebSocket pour le dialogue unifié"""
    await websocket.accept()
    
    try:
        from core.cognition.unified_engine import get_unified_engine
        engine = get_unified_engine()
        
        session = engine.get_session(session_id)
        if not session:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close()
            return
        
        while True:
            # Recevoir le message de l'utilisateur
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            if not message:
                continue
            
            # Traiter le message
            async for event in engine.process_message(session_id, message):
                await websocket.send_json(event)
    
    except WebSocketDisconnect:
        logging.info(f"[Unified] WebSocket disconnected: {session_id}")
    except Exception as e:
        logging.error(f"[Unified] WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass


@router.get("/unified/history/{session_id}")
async def unified_history(session_id: str):
    """Récupère l'historique d'une session"""
    try:
        from core.cognition.unified_engine import get_unified_engine
        engine = get_unified_engine()
        
        session = engine.get_session(session_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        return {
            "status": "ok",
            "session_id": session_id,
            "mode": session.mode.value,
            "iterations": session.iterations,
            "rag_consultations": session.rag_consultations,
            "completed": session.completed,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "iteration": msg.iteration,
                    "confidence": msg.confidence
                }
                for msg in session.messages
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/unified/stats")
async def unified_stats():
    """Statistiques du module unifié"""
    try:
        from core.cognition.unified_engine import get_unified_engine
        from core.system.rag_indexer import get_rag_indexer
        
        engine = get_unified_engine()
        rag = get_rag_indexer()
        
        return {
            "engine": engine.get_stats(),
            "rag": rag.get_stats()
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ============ RAG ENDPOINTS ============

@router.get("/unified/rag/status")
async def rag_status():
    """Statut du RAG"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        return rag.get_stats()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/rag/enable")
async def rag_enable():
    """Active le RAG (DÉPENDANCE)"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        rag.enable()
        return {"status": "ok", "message": "RAG activé - Mode dépendance"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/rag/disable")
async def rag_disable():
    """Désactive le RAG (ÉMERGENCE)"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        rag.disable()
        return {"status": "ok", "message": "RAG désactivé - Mode émergence"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/rag/index")
async def rag_index(req: RAGIndexRequest):
    """Indexe un document dans le RAG"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        
        doc = rag.index_document(
            content=req.content,
            source=req.source,
            category=req.category
        )
        
        return {
            "status": "ok",
            "document_id": doc.id,
            "message": "Document indexé"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/rag/index/builtin")
async def rag_index_builtin():
    """Indexe la documentation intégrée"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        
        rag.index_python_docs()
        rag.index_fastapi_docs()
        
        return {
            "status": "ok",
            "message": "Documentation intégrée indexée",
            "total_documents": len(rag.documents)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/unified/rag/clear")
async def rag_clear():
    """Vide l'index RAG"""
    try:
        from core.system.rag_indexer import get_rag_indexer
        rag = get_rag_indexer()
        rag.clear()
        return {"status": "ok", "message": "Index RAG vidé"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
