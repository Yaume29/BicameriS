"""
API Knowledge Routes
====================
Knowledge base management endpoints
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["knowledge"])


@router.get("/knowledge/stats")
async def knowledge_stats():
    """Get knowledge base statistics"""
    try:
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        return kb.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.get("/knowledge/search")
async def knowledge_search(q: str = "", limit: int = 5, category: str = None):
    """Search knowledge base"""
    try:
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        if not q:
            return {"entries": []}
        
        results = kb.search(q, limit=limit, category=category)
        
        return {
            "entries": [
                {
                    "id": e.id,
                    "content": e.content[:200],
                    "category": e.category,
                    "importance": e.importance,
                    "tags": e.tags
                }
                for e in results
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/knowledge/add")
async def knowledge_add(request: Request):
    """Add entry to knowledge base"""
    try:
        data = await request.json()
        
        content = data.get("content", "")
        category = data.get("category", "fact")
        source = data.get("source", "manual")
        importance = data.get("importance", 0.5)
        tags = data.get("tags", [])
        
        if not content:
            return {"status": "error", "error": "Content required"}
        
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        entry = kb.add_entry(
            content=content,
            category=category,
            source=source,
            importance=importance,
            tags=tags
        )
        
        return {
            "status": "ok",
            "entry_id": entry.id,
            "message": "Knowledge entry added"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/knowledge/learn")
async def knowledge_learn(request: Request):
    """Learn from experience"""
    try:
        data = await request.json()
        
        learn_type = data.get("type", "insight")
        
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        if learn_type == "correction":
            kb.learn_from_correction(
                original=data.get("original", ""),
                corrected=data.get("corrected", ""),
                explanation=data.get("explanation", "")
            )
        elif learn_type == "insight":
            kb.learn_from_insight(
                insight=data.get("insight", ""),
                context=data.get("context", "")
            )
        elif learn_type == "pattern":
            kb.learn_pattern(
                pattern=data.get("pattern", ""),
                examples=data.get("examples", [])
            )
        elif learn_type == "technique":
            kb.learn_technique(
                technique=data.get("technique", ""),
                domain=data.get("domain", "")
            )
        
        return {"status": "ok", "message": f"Learned {learn_type}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/knowledge/export")
async def knowledge_export(format: str = "json"):
    """Export knowledge base"""
    try:
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        exported = kb.export_knowledge(format=format)
        
        return {
            "format": format,
            "content": exported
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/knowledge/import")
async def knowledge_import(request: Request):
    """Import knowledge"""
    try:
        data = await request.json()
        
        content = data.get("content", "")
        format = data.get("format", "json")
        
        if not content:
            return {"status": "error", "error": "Content required"}
        
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        imported = kb.import_knowledge(content, format=format)
        
        return {
            "status": "ok",
            "imported": imported,
            "message": f"Imported {imported} entries"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/knowledge/cleanup")
async def knowledge_cleanup(request: Request):
    """Clean up knowledge base"""
    try:
        data = await request.json()
        
        min_importance = data.get("min_importance", 0.1)
        max_age_days = data.get("max_age_days", 90)
        
        from core.system.knowledge_base import get_knowledge_base
        kb = get_knowledge_base()
        
        removed = kb.cleanup(min_importance=min_importance, max_age_days=max_age_days)
        
        return {
            "status": "ok",
            "removed": removed,
            "message": f"Cleaned up {removed} entries"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
