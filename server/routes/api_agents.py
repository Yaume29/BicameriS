"""
API Agents Routes
=================
Endpoints for agent management and coordination
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["agents"])


@router.get("/agents")
async def get_agents():
    """Get all agents"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        return {"agents": registry.get_all_agents()}
    except Exception as e:
        return {"error": str(e)}


@router.get("/agents/stats")
async def agents_stats():
    """Get agent statistics"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        return registry.get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.post("/agents/{agent_name}/enable")
async def enable_agent(agent_name: str):
    """Enable an agent"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        registry.enable_agent(agent_name)
        return {"status": "ok", "agent": agent_name, "enabled": True}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/agents/{agent_name}/disable")
async def disable_agent(agent_name: str):
    """Disable an agent"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        registry.disable_agent(agent_name)
        return {"status": "ok", "agent": agent_name, "enabled": False}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.get("/agents/{agent_name}/config")
async def get_agent_config(agent_name: str):
    """Get agent configuration"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        config = registry.configs.get(agent_name)
        if config:
            return {
                "name": config.name,
                "type": config.agent_type.value,
                "description": config.description,
                "enabled": config.enabled,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "priority": config.priority,
            }
        return {"error": f"Agent {agent_name} not found"}
    except Exception as e:
        return {"error": str(e)}


@router.put("/agents/{agent_name}/config")
async def update_agent_config(agent_name: str, request: Request = None):
    """Update agent configuration"""
    try:
        from core.agents.agent_system import get_agent_registry
        registry = get_agent_registry()
        
        data = await request.json()
        registry.update_agent_config(agent_name, **data)
        
        return {"status": "ok", "agent": agent_name, "config": data}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/agents/{agent_name}/execute")
async def execute_agent(agent_name: str, request: Request = None):
    """Execute an agent"""
    try:
        from core.agents.agent_system import get_agent_coordinator
        coordinator = get_agent_coordinator()
        
        data = await request.json()
        result = await coordinator.execute_agent(agent_name, data)
        
        return {
            "status": "ok",
            "agent": result.agent_name,
            "output": result.output,
            "confidence": result.confidence,
            "sources": result.sources,
            "metadata": result.metadata,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/agents/execute_parallel")
async def execute_agents_parallel(request: Request):
    """Execute multiple agents in parallel"""
    try:
        from core.agents.agent_system import get_agent_coordinator
        coordinator = get_agent_coordinator()
        
        data = await request.json()
        agent_names = data.get("agents", [])
        input_data = data.get("input", {})
        
        results = await coordinator.execute_parallel(agent_names, input_data)
        
        return {
            "status": "ok",
            "results": [
                {
                    "agent": r.agent_name,
                    "output": r.output,
                    "confidence": r.confidence,
                    "sources": r.sources,
                }
                for r in results
                if hasattr(r, 'agent_name')
            ]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/agents/execute_chain")
async def execute_agents_chain(request: Request):
    """Execute agents in sequence"""
    try:
        from core.agents.agent_system import get_agent_coordinator
        coordinator = get_agent_coordinator()
        
        data = await request.json()
        agent_names = data.get("agents", [])
        initial_input = data.get("input", {})
        
        result = await coordinator.execute_chain(agent_names, initial_input)
        
        return {
            "status": "ok",
            "agent": result.agent_name,
            "output": result.output,
            "confidence": result.confidence,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/agents/init")
async def init_agents():
    """Initialize default agents"""
    try:
        from core.agents.implementations import init_default_agents
        registry = init_default_agents()
        
        return {
            "status": "ok",
            "message": "Agents initialized",
            "count": len(registry.agents)
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
