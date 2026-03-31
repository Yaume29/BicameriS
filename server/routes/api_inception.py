"""
API Inception Routes
===================
Thought inception endpoints
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["inception"])


@router.post("/inception/launch")
async def inception_launch(request: Request):
    """Launch a new inception"""
    try:
        data = await request.json()
        content = data.get("content", "")
        category = data.get("category", "reflection")
        weight = data.get("weight", 50)
        
        from core.cognition.thought_inception import get_thought_inception
        inception = get_thought_inception()
        
        # Determine target based on category
        target = "BOTH"
        if category in ["logic", "analysis"]:
            target = "LEFT"
        elif category in ["creativity", "intuition"]:
            target = "RIGHT"
        
        thought = inception.create_induced_thought(
            content=content,
            influence_level=float(weight),
            integration_type=category,
            target=target
        )
        
        return {"status": "ok", "thought_id": thought.id, "message": "Inception lancée"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/inception/create")
async def inception_create(request: Request):
    """Create an inception (alternate endpoint)"""
    return await inception_launch(request)


@router.get("/inception/status")
async def inception_status():
    """Get inception status"""
    try:
        from core.cognition.thought_inception import get_thought_inception
        inception = get_thought_inception()
        stats = inception.get_stats()
        return {
            "acknowledged": stats.get("warning_acknowledged", True),
            "pending": stats.get("pending", 0),
            "all": stats.get("total", 0)
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/inception/ack")
async def inception_acknowledge():
    """Acknowledge inception warning"""
    try:
        from core.cognition.thought_inception import get_thought_inception
        inception = get_thought_inception()
        inception.acknowledge_warning()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/inception")
async def inception_list():
    """List all thoughts"""
    try:
        from core.cognition.thought_inception import get_thought_inception
        inception = get_thought_inception()
        thoughts = inception.get_all_thoughts()
        return {
            "thoughts": [
                {
                    "id": t.id,
                    "content": t.content,
                    "timestamp": t.timestamp,
                    "influence_level": t.influence_level,
                    "integration_type": t.integration_type,
                    "target": t.target,
                    "injected": t.injected
                }
                for t in thoughts
            ]
        }
    except Exception as e:
        return {"error": str(e)}
