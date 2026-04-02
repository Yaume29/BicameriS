"""
API Routes for Bicameral Skills & Agents
========================================
Endpoints pour accéder aux skills, agents et hooks.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Optional

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/skills")
async def list_skills():
    """Liste tous les skills disponibles"""
    try:
        from core.agents.bicameral_skills import get_skills_manager
        manager = get_skills_manager()
        return {"skills": manager.list_skills()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/skills/{name}")
async def get_skill(name: str):
    """Récupère un skill spécifique"""
    try:
        from core.agents.bicameral_skills import get_skills_manager
        manager = get_skills_manager()
        
        skill = manager.get_skill(name)
        if not skill:
            raise HTTPException(status_code=404, detail=f"Skill {name} not found")
        
        return {
            "name": skill.name,
            "description": skill.description,
            "tools": skill.tools,
            "content": skill.content[:1000]  # Preview
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents")
async def list_agents():
    """Liste tous les agents disponibles"""
    try:
        from core.agents.bicameral_skills import get_skills_manager
        manager = get_skills_manager()
        return {"agents": manager.list_agents()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{name}")
async def get_agent(name: str):
    """Récupère un agent spécifique"""
    try:
        from core.agents.bicameral_skills import get_skills_manager
        manager = get_skills_manager()
        
        agent = manager.get_agent(name)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {name} not found")
        
        # Créer un agent bicaméral
        bicameral = manager.create_bicameral_agent(agent)
        
        return {
            "name": agent.name,
            "description": agent.description,
            "model": agent.model,
            "tools": agent.tools,
            "bicameral_config": bicameral
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/skills/relevant")
async def get_relevant_skills(request: Request):
    """Récupère les skills pertinents pour un type de tâche"""
    try:
        data = await request.json()
        task_type = data.get("task_type", "")
        
        from core.agents.bicameral_skills import get_skills_manager
        manager = get_skills_manager()
        
        skills = manager.get_relevant_skills(task_type)
        
        return {
            "task_type": task_type,
            "relevant_skills": [
                {
                    "name": skill.name,
                    "description": skill.description,
                    "tools": skill.tools
                }
                for skill in skills
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cognitive-hooks")
async def list_cognitive_hooks():
    """Liste les hooks cognitifs du Corps Calleux"""
    try:
        from core.cognition.cognitive_hooks import get_cognitive_hook_manager
        manager = get_cognitive_hook_manager()
        return {"history": manager.get_history()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
