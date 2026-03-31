"""
Base Agent
==========
Classe de base pour tous les agents.
Inspiré par SuperAGI.

Désactivé par défaut - activez via enable().
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from datetime import datetime
from collections import deque

logger = logging.getLogger("agents.base")


class AgentState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"
    COMPLETED = "completed"
    STOPPED = "stopped"


class AgentStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class AgentConfig:
    name: str
    description: str
    model: str = "default"
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: List[str] = field(default_factory=list)
    memory_enabled: bool = True
    max_iterations: int = 10
    timeout: int = 300
    system_prompt: str = ""


@dataclass
class Task:
    id: str
    description: str
    parameters: Dict = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    iterations: int = 0
    metadata: Dict = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Agent de base - Template pour tous les agents.
    
    Désactivé par défaut (enabled=False).
    Utilisez enable() pour activer l'agent.
    """

    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self.status = AgentStatus.DISABLED
        self.current_task: Optional[Task] = None
        self.task_history: deque = deque(maxlen=100)
        self.tool_registry = None
        self.llm_client = None
        self._stop_requested = False

    def enable(self):
        """Active l'agent"""
        self.status = AgentStatus.ENABLED
        logger.info(f"[Agent] {self.config.name} enabled")

    def disable(self):
        """Désactive l'agent"""
        self.status = AgentStatus.DISABLED
        self.state = AgentState.IDLE
        logger.info(f"[Agent] {self.config.name} disabled")

    def request_stop(self):
        """Demande l'arrêt de l'agent"""
        self._stop_requested = True
        logger.info(f"[Agent] {self.config.name} stop requested")

    def reset_stop(self):
        """Reset la demande d'arrêt"""
        self._stop_requested = False

    def set_tool_registry(self, registry):
        """Configure le registre d'outils"""
        self.tool_registry = registry

    def set_llm_client(self, client):
        """Configure le client LLM"""
        self.llm_client = client

    @abstractmethod
    async def think(self, task: Task) -> str:
        """
        Phase de réflexion - analyser et planifier.
        
        Returns:
            Plan sous forme de string
        """
        pass

    @abstractmethod
    async def execute(self, task: Task, plan: str) -> Dict:
        """
        Phase d'exécution - appliquer le plan.
        
        Returns:
            Dict avec resultat et métadonnées
        """
        pass

    async def run(self, task: Task) -> Task:
        """
        Boucle principale de l'agent.
        
        Args:
            task: Tâche à exécuter
            
        Returns:
            Task avec résultat ou erreur
        """
        if self.status == AgentStatus.DISABLED:
            task.status = "error"
            task.error = "Agent is disabled"
            return task

        self.current_task = task
        self.state = AgentState.THINKING
        self.status = AgentStatus.RUNNING
        self.reset_stop()

        try:
            logger.info(f"[Agent] {self.config.name} starting task: {task.description[:50]}")

            while task.iterations < self.config.max_iterations:
                if self._stop_requested:
                    task.status = "stopped"
                    self.state = AgentState.STOPPED
                    break

                try:
                    self.state = AgentState.THINKING
                    plan = await self.think(task)
                    
                    if self._stop_requested:
                        task.status = "stopped"
                        break

                    self.state = AgentState.EXECUTING
                    result = await self.execute(task, plan)
                    
                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    self.state = AgentState.COMPLETED
                    
                    logger.info(f"[Agent] {self.config.name} completed task")
                    break

                except Exception as e:
                    task.iterations += 1
                    logger.warning(f"[Agent] {self.config.name} iteration {task.iterations} failed: {e}")
                    
                    if task.iterations >= self.config.max_iterations:
                        task.status = "error"
                        task.error = f"Max iterations reached: {str(e)}"
                        self.state = AgentState.ERROR

            self.task_history.append(task)
            
        except Exception as e:
            logger.error(f"[Agent] {self.config.name} error: {e}")
            task.status = "error"
            task.error = str(e)
            self.state = AgentState.ERROR

        self.current_task = None
        self.status = AgentStatus.ENABLED if self.state != AgentState.ERROR else AgentStatus.DISABLED
        
        return task

    async def evaluate(self, result: Any) -> float:
        """
        Évalue la qualité du résultat.
        
        Returns:
            Score entre 0 et 1
        """
        if not self.llm_client:
            return 0.5
        
        try:
            prompt = f"Évalue la qualité de ce résultat de 0 à 1 (décimal): {str(result)[:500]}"
            response = self.llm_client.think(
                self.config.system_prompt or "You are a quality evaluator.",
                prompt,
                temperature=0.2
            )
            
            score = float(response.strip().split()[-1].replace(',', '.'))
            return max(0.0, min(1.0, score))
        except:
            return 0.5

    def get_state(self) -> Dict:
        """Retourne l'état actuel de l'agent"""
        return {
            "name": self.config.name,
            "status": self.status.value,
            "state": self.state.value,
            "current_task": self.current_task.description[:50] if self.current_task else None,
            "task_history_count": len(self.task_history),
            "iterations": self.current_task.iterations if self.current_task else 0
        }

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Historique des tâches"""
        return [
            {
                "id": t.id,
                "description": t.description[:50],
                "status": t.status,
                "created_at": t.created_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "iterations": t.iterations
            }
            for t in list(self.task_history)[-limit:]
        ]


class StreamingAgent(BaseAgent):
    """
    Agent avec support streaming.
    """

    async def run_streaming(self, task: Task, callback):
        """
        Execute task with streaming callback.
        
        callback(chunk: str) -> None
        """
        if self.status == AgentStatus.DISABLED:
            task.status = "error"
            task.error = "Agent is disabled"
            yield {"type": "error", "content": "Agent is disabled"}
            return

        self.current_task = task
        self.state = AgentState.THINKING
        self.status = AgentStatus.RUNNING
        self.reset_stop()

        try:
            yield {"type": "status", "content": "thinking"}
            
            plan = await self.think(task)
            yield {"type": "plan", "content": plan}

            self.state = AgentState.EXECUTING
            yield {"type": "status", "content": "executing"}

            result = await self.execute_streaming(task, plan, callback)
            
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.now()
            
            yield {"type": "complete", "content": result}

        except Exception as e:
            logger.error(f"[StreamingAgent] Error: {e}")
            yield {"type": "error", "content": str(e)}
            task.status = "error"
            task.error = str(e)

        self.current_task = None
        self.status = AgentStatus.ENABLED

    async def execute_streaming(self, task: Task, plan: str, callback):
        """Exécution avec streaming - à surcharger"""
        result = await self.execute(task, plan)
        await callback(str(result))
        return result
