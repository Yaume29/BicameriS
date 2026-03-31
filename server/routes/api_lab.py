"""
API Lab Routes
==============
Chat Technique Lab endpoints
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict

router = APIRouter(tags=["lab"])

logger = logging.getLogger("lab")


def get_lab_engine():
    """Get the lab engine instance"""
    try:
        from core.lab.lab_engine import get_lab_engine as _get
        from server.extensions import registry
        
        config = {}
        if hasattr(registry, 'config'):
            config = registry.config.get('lab', {})
        
        engine = _get(config)
        return engine
    except Exception as e:
        logger.error(f"Failed to get lab engine: {e}")
        return None


def get_specialist_manager():
    """Get specialist manager"""
    try:
        from core.lab.specialist import get_specialist_manager as _get
        from server.extensions import registry
        
        config = {}
        if hasattr(registry, 'config'):
            config = registry.config.get('lab', {})
        
        return _get(config)
    except Exception as e:
        logger.error(f"Failed to get specialist manager: {e}")
        return None


@router.get("/lab/status")
async def lab_status():
    """Get lab status"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "message": "Lab engine not available"}
    
    return {
        "status": "ok",
        "conversations": len(engine.conversations),
        "workspaces": len(engine.workspaces),
        "active_conversation": engine.active_conversation,
        "active_workspace": engine.active_workspace
    }


@router.get("/lab/specialists")
async def lab_specialists():
    """Get available specialists"""
    manager = get_specialist_manager()
    if not manager:
        return {"status": "error", "specialists": []}
    
    specialists = []
    for spec in manager.list_specialists():
        specialists.append({
            "id": spec.id,
            "name": spec.name,
            "description": spec.description,
            "icon": spec.icon,
            "hemisphere": spec.hemisphere,
            "temperature": spec.temperature,
            "capabilities": spec.capabilities,
            "enabled": manager.is_enabled(spec.id)
        })
    
    return {"status": "ok", "specialists": specialists}


@router.post("/lab/conversation/create")
async def create_conversation(request: Request):
    """Create a new lab conversation"""
    try:
        data = await request.json()
        specialist_id = data.get("specialist_id", "multi")
        workspace_name = data.get("workspace_name", "Nouveau Projet")
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        conv = engine.create_conversation(specialist_id, workspace_name)
        
        return {
            "status": "ok",
            "conversation": {
                "id": conv.id,
                "specialist_id": conv.specialist_id,
                "workspace_id": conv.workspace_id,
                "title": conv.title,
                "created_at": conv.created_at
            }
        }
    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/lab/conversations")
async def list_conversations(specialist_id: str = None):
    """List all conversations"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "conversations": []}
    
    convs = engine.list_conversations(specialist_id)
    
    result = []
    for conv in convs:
        result.append({
            "id": conv.id,
            "specialist_id": conv.specialist_id,
            "workspace_id": conv.workspace_id,
            "title": conv.title,
            "message_count": len(conv.messages),
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "status": conv.status
        })
    
    return {"status": "ok", "conversations": result}


@router.get("/lab/conversation/{conv_id}")
async def get_conversation(conv_id: str):
    """Get a specific conversation"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "message": "Lab engine not available"}
    
    conv = engine.get_conversation(conv_id)
    if not conv:
        return {"status": "error", "message": "Conversation not found"}
    
    messages = []
    for msg in conv.messages:
        messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "timestamp": msg.timestamp,
            "specialist_id": msg.specialist_id
        })
    
    return {
        "status": "ok",
        "conversation": {
            "id": conv.id,
            "specialist_id": conv.specialist_id,
            "workspace_id": conv.workspace_id,
            "title": conv.title,
            "messages": messages,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "status": conv.status
        }
    }


@router.post("/lab/conversation/{conv_id}/message")
async def send_message(conv_id: str, request: Request):
    """Send a message to a conversation"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        if not message:
            return {"status": "error", "message": "Message vide"}
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        conv = engine.get_conversation(conv_id)
        if not conv:
            return {"status": "error", "message": "Conversation not found"}
        
        specialist_id = data.get("specialist_id", conv.specialist_id)
        
        response = await engine.process_message(conv_id, message, specialist_id)
        
        return {
            "status": "ok",
            "response": response,
            "conversation_id": conv_id
        }
    except Exception as e:
        logger.error(f"Send message error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/lab/conversation/{conv_id}/stream")
async def stream_message(conv_id: str, request: Request):
    """Stream a message response"""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        
        if not message:
            return {"status": "error", "message": "Message vide"}
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        conv = engine.get_conversation(conv_id)
        if not conv:
            return {"status": "error", "message": "Conversation not found"}
        
        specialist_id = data.get("specialist_id", conv.specialist_id)
        
        async def generate_stream():
            """Generate streaming response"""
            full_response = ""
            
            try:
                response = await engine.process_message(conv_id, message, specialist_id)
                full_response = response
                
                yield f"data: {json.dumps({'type': 'response', 'content': response})}\n\n"
                
            except Exception as e:
                error_msg = f"Erreur: {str(e)}"
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                full_response = error_msg
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        logger.error(f"Stream message error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/lab/workspace/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace details"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "message": "Lab engine not available"}
    
    workspace = engine.get_workspace(workspace_id)
    if not workspace:
        return {"status": "error", "message": "Workspace not found"}
    
    files = engine.list_workspace_files(workspace_id)
    
    return {
        "status": "ok",
        "workspace": {
            "id": workspace.id,
            "name": workspace.name,
            "path": workspace.path,
            "files": files,
            "created_at": workspace.created_at,
            "updated_at": workspace.updated_at
        }
    }


@router.get("/lab/workspace/{workspace_id}/files")
async def list_workspace_files(workspace_id: str):
    """List workspace files"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "message": "Lab engine not available"}
    
    files = engine.list_workspace_files(workspace_id)
    
    return {
        "status": "ok",
        "files": files
    }


@router.get("/lab/workspace/{workspace_id}/file/{filename}")
async def get_file(workspace_id: str, filename: str):
    """Get file content from workspace"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "message": "Lab engine not available"}
    
    content = engine.get_file_content(workspace_id, filename)
    if content is None:
        return {"status": "error", "message": "File not found"}
    
    return {
        "status": "ok",
        "filename": filename,
        "content": content
    }


@router.post("/lab/workspace/{workspace_id}/file")
async def create_file(workspace_id: str, request: Request):
    """Create or update a file in workspace"""
    try:
        data = await request.json()
        filename = data.get("filename", "").strip()
        content = data.get("content", "")
        
        if not filename:
            return {"status": "error", "message": "Filename required"}
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        engine.add_file_to_workspace(workspace_id, filename, content)
        
        return {
            "status": "ok",
            "message": f"Fichier {filename} créé/modifié"
        }
    except Exception as e:
        logger.error(f"Create file error: {e}")
        return {"status": "error", "message": str(e)}


@router.delete("/lab/workspace/{workspace_id}/file/{filename}")
async def delete_file(workspace_id: str, filename: str):
    """Delete a file from workspace"""
    try:
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        workspace = engine.get_workspace(workspace_id)
        if not workspace:
            return {"status": "error", "message": "Workspace not found"}
        
        if filename in workspace.files:
            del workspace.files[filename]
        
        file_path = Path(workspace.path) / filename
        if file_path.exists():
            file_path.unlink()
        
        return {
            "status": "ok",
            "message": f"Fichier {filename} supprimé"
        }
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/lab/config")
async def get_lab_config():
    """Get lab configuration"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "config": {}}
    
    return {
        "status": "ok",
        "config": engine.get_config()
    }


@router.post("/lab/config")
async def update_lab_config(request: Request):
    """Update lab configuration"""
    try:
        data = await request.json()
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        engine.update_config(data)
        
        return {
            "status": "ok",
            "message": "Configuration mise à jour"
        }
    except Exception as e:
        logger.error(f"Update config error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/lab/tools")
async def list_tools():
    """List available tools"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "tools": []}
    
    tools = engine.brain.tools.list_tools()
    return {"status": "ok", "tools": tools}


@router.post("/lab/tool/{tool_name}")
async def run_tool(tool_name: str, request: Request):
    """Run a tool"""
    try:
        data = await request.json()
        conversation_id = data.pop("conversation_id", None)
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        result = await engine.run_tool(tool_name, conversation_id, **data)
        
        return result
    except Exception as e:
        logger.error(f"Run tool error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/lab/autonomous/{conv_id}")
async def run_autonomous(conv_id: str, request: Request):
    """Run autonomous task"""
    try:
        data = await request.json()
        task = data.get("task", "")
        
        if not task:
            return {"status": "error", "message": "Task required"}
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        result = await engine.process_autonomous(conv_id, task)
        
        return result
    except Exception as e:
        logger.error(f"Autonomous error: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/lab/memory/recall")
async def recall_memory(q: str = "", limit: int = 3):
    """Recall memories"""
    engine = get_lab_engine()
    if not engine:
        return {"status": "error", "memories": []}
    
    memories = await engine.brain.recall_memory(q, limit)
    return {"status": "ok", "memories": memories}


@router.post("/lab/memory/weave")
async def weave_memory(request: Request):
    """Weave a memory"""
    try:
        data = await request.json()
        content = data.get("content", "")
        source = data.get("source", "lab")
        category = data.get("category", "general")
        
        if not content:
            return {"status": "error", "message": "Content required"}
        
        engine = get_lab_engine()
        if not engine:
            return {"status": "error", "message": "Lab engine not available"}
        
        await engine.brain.weave_memory(content, source, category)
        
        return {"status": "ok", "message": "Souvenir tissé"}
    except Exception as e:
        logger.error(f"Weave memory error: {e}")
        return {"status": "error", "message": str(e)}


# ==================== MODULES API ====================

@router.get("/lab/modules")
async def list_modules():
    """List all available modules"""
    try:
        from core.lab.modules import list_lab_modules
        modules = list_lab_modules()
        return {"status": "ok", "modules": modules}
    except Exception as e:
        logger.error(f"List modules error: {e}")
        return {"status": "error", "modules": [], "message": str(e)}


@router.get("/lab/module/{module_id}/render")
async def render_module(module_id: str):
    """Render a module's HTML"""
    try:
        from core.lab.modules import get_lab_module
        module = get_lab_module(module_id)
        
        if not module:
            return {"status": "error", "message": f"Module not found: {module_id}"}
        
        html = module.render()
        return {"status": "ok", "html": html}
    except Exception as e:
        logger.error(f"Render module error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/lab/module/{module_id}/action")
async def module_action(module_id: str, request: Request):
    """Handle module action"""
    try:
        data = await request.json()
        action = data.pop("action", "")
        
        from core.lab.modules import get_lab_module
        module = get_lab_module(module_id)
        
        if not module:
            return {"status": "error", "message": f"Module not found: {module_id}"}
        
        result = module.handle_action(action, data)
        return result
    except Exception as e:
        logger.error(f"Module action error: {e}")
        return {"status": "error", "message": str(e)}
