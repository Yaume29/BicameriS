"""
Super Agent System
=================
Agent qui peut créer et gérer d'autres agents dynamiquement.
Inspiré par AutoGPT + MetaGPT.
"""

import uuid
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("agents.super_agent")


class AgentState(Enum):
    CREATING = "creating"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentSpec:
    """Specification for dynamically created agent"""
    id: str
    name: str
    role: str
    goal: str
    tools: List[str] = field(default_factory=list)
    created_by: str = ""
    status: AgentState = AgentState.CREATING


@dataclass
class Task:
    """Task for an agent"""
    id: str
    description: str
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Any = None
    dependencies: List[str] = field(default_factory=list)


class SuperAgent:
    """
    Super Agent - Peut créer et gérer des sous-agents dynamiquement.
    
    Architecture:
    - SuperAgent analyse les tâches complexes
    - Crée des sous-agents spécialisés si nécessaire
    - Orchestre le travail parallèle
    - Synthétise les résultats
    """

    def __init__(self, name: str = "SuperAgent"):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        
        self.agents: Dict[str, AgentSpec] = {}
        self.tasks: Dict[str, Task] = {}
        
        self.corps_calleux = None
        self.tool_registry = None
        
        self.enabled = False

    def connect_corps_calleux(self, corps_calleux):
        """Connect to bicameral system"""
        self.corps_calleux = corps_calleux

    def connect_tool_registry(self, registry):
        """Connect tool registry"""
        self.tool_registry = registry

    def enable(self):
        self.enabled = True
        logger.info(f"[SuperAgent] {self.name} enabled")

    def disable(self):
        self.enabled = False
        logger.info(f"[SuperAgent] {self.name} disabled")

    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """
        Execute complex task by spawning agents if needed.
        
        Flow:
        1. Analyze task
        2. Decide if sub-agents needed
        3. Create agents if needed
        4. Execute in parallel/sequence
        5. Synthesize results
        """
        if not self.enabled:
            return {"status": "error", "message": "SuperAgent disabled"}

        task = Task(
            id=str(uuid.uuid4())[:8],
            description=task_description
        )
        self.tasks[task.id] = task

        analysis = await self._analyze_task(task_description)
        
        if analysis["needs_agents"]:
            agents = await self._create_agents(analysis["sub_tasks"])
            results = await self._execute_agents(agents)
            final = await self._synthesize(task_description, results)
        else:
            final = await self._execute_direct(task_description)

        task.status = "completed"
        task.result = final

        return {
            "status": "ok",
            "task_id": task.id,
            "result": final,
            "agents_created": len(self.agents),
            "analysis": analysis
        }

    async def _analyze_task(self, task: str) -> Dict:
        """Analyze if task needs sub-agents"""
        
        if not self.corps_calleux or not self.corps_calleux.left:
            return {
                "needs_agents": False,
                "reason": "No hemispheres",
                "sub_tasks": []
            }

        prompt = f"""Analyze this task and decide if it needs multiple specialized agents or can be done by one agent.

Task: {task}

Respond with:
1. needs_agents: true/false
2. reason: why
3. sub_tasks: array of task descriptions if needs_agents=true, else empty

Examples:
- "Write a research paper" -> needs_agents=true, sub_tasks=["Research", "Write", "Review"]
- "Translate this sentence" -> needs_agents=false
- "Build a web app" -> needs_agents=true, sub_tasks=["Design", "Frontend", "Backend", "Deploy"]
- "Find information" -> needs_agents=false"""

        response = self.corps_calleux.left.think(
            "You are a task planning assistant. Analyze tasks and decide if multiple agents are needed.",
            prompt,
            temperature=0.3
        )

        try:
            if "needs_agents: true" in response.lower():
                parts = response.split("sub_tasks:")
                if len(parts) > 1:
                    sub = parts[1].strip().split("\n")
                    sub_tasks = [s.strip("- ").strip() for s in sub if s.strip()]
                else:
                    sub_tasks = []
                return {"needs_agents": True, "reason": "Multi-agent analysis", "sub_tasks": sub_tasks}
        except:
            pass

        return {"needs_agents": False, "reason": "Simple task", "sub_tasks": []}

    async def _create_agents(self, sub_tasks: List[str]) -> List[AgentSpec]:
        """Create sub-agents for each subtask"""
        created = []

        for i, subtask in enumerate(sub_tasks):
            agent_id = f"agent_{self.id}_{i}"
            
            spec = AgentSpec(
                id=agent_id,
                name=f"Agent-{i+1}",
                role=self._infer_role(subtask),
                goal=subtask,
                tools=self._infer_tools(subtask),
                created_by=self.id,
                status=AgentState.CREATING
            )

            self.agents[agent_id] = spec
            created.append(spec)
            logger.info(f"[SuperAgent] Created agent {agent_id}: {spec.role}")

        return created

    def _infer_role(self, task: str) -> str:
        """Infer agent role from task"""
        task_lower = task.lower()
        
        if any(w in task_lower for w in ["research", "find", "search", "analyze"]):
            return "researcher"
        elif any(w in task_lower for w in ["write", "draft", "create content"]):
            return "writer"
        elif any(w in task_lower for w in ["code", "program", "build", "implement"]):
            return "coder"
        elif any(w in task_lower for w in ["review", "check", "validate", "test"]):
            return "reviewer"
        elif any(w in task_lower for w in ["design", "plan", "architecture"]):
            return "designer"
        else:
            return "assistant"

    def _infer_tools(self, task: str) -> List[str]:
        """Infer required tools from task"""
        tools = []
        task_lower = task.lower()

        if "web" in task_lower or "search" in task_lower or "research" in task_lower:
            tools.extend(["web_search", "web_fetch"])

        if "code" in task_lower or "implement" in task_lower:
            tools.extend(["code_executor", "file_read", "file_write"])

        if "arxiv" in task_lower or "paper" in task_lower or "academic" in task_lower:
            tools.append("ingest_arxiv")

        if "github" in task_lower or "code" in task_lower:
            tools.append("ingest_github")

        return tools

    async def _execute_agents(self, agents: List[AgentSpec]) -> Dict[str, Any]:
        """Execute tasks with sub-agents in parallel"""
        results = {}

        async def run_agent(agent: AgentSpec):
            agent.status = AgentState.RUNNING
            result = await self._execute_agent_task(agent)
            results[agent.id] = result
            agent.status = AgentState.COMPLETED

        await asyncio.gather(*[run_agent(a) for a in agents], return_exceptions=True)

        return results

    async def _execute_agent_task(self, agent: AgentSpec) -> str:
        """Execute single agent task using bicameral system"""
        
        if not self.corps_calleux:
            return "No corps calleux"

        system = f"You are a {agent.role} agent. Your goal: {agent.goal}"

        if self.corps_calleux.left and self.corps_calleux.right:
            left_resp = self.corps_calleux.left.think(system, agent.goal, temperature=0.4)
            right_resp = self.corps_calleux.right.think(system, agent.goal, temperature=0.8)

            if self.tool_registry and agent.tools:
                for tool_name in agent.tools[:2]:
                    if self.tool_registry.is_enabled(tool_name):
                        try:
                            tool_result = await self.tool_registry.execute(tool_name, {"query": agent.goal})
                            if tool_result.get("status") == "ok":
                                left_resp += f"\n\n[Tool {tool_name}]: {str(tool_result.get('result'))[:200]}"
                        except:
                            pass

            return f"**Analysis:** {left_resp[:300]}\n\n**Intuition:** {right_resp[:300]}"

        return f"Executed: {agent.goal}"

    async def _execute_direct(self, task: str) -> str:
        """Execute simple task directly"""
        if not self.corps_calleux:
            return f"Task: {task}"

        return self.corps_calleux.left.think(
            "Execute this task:",
            task,
            temperature=0.6
        )

    async def _synthesize(self, original: str, results: Dict) -> str:
        """Synthesize results from all agents"""
        if not self.corps_calleux:
            return str(results)

        summary = f"Original task: {original}\n\nResults:\n"
        for agent_id, result in results.items():
            agent = self.agents.get(agent_id)
            role = agent.role if agent else agent_id
            summary += f"\n[{role}]: {str(result)[:200]}..."

        synthesis = self.corps_calleux.left.think(
            "Synthesize these results into a coherent response:",
            summary,
            temperature=0.5
        )

        return synthesis

    def get_status(self) -> Dict:
        """Get super agent status"""
        return {
            "enabled": self.enabled,
            "agents_count": len(self.agents),
            "tasks_count": len(self.tasks),
            "agents": [
                {"id": a.id, "role": a.role, "status": a.status.value}
                for a in self.agents.values()
            ]
        }


_global_super_agent: Optional[SuperAgent] = None


def get_super_agent() -> SuperAgent:
    """Get global super agent instance"""
    global _global_super_agent
    if _global_super_agent is None:
        _global_super_agent = SuperAgent()
    return _global_super_agent
