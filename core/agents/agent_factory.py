"""
Agent Factory
============
Fabrique pour créer dynamiquement des agents.
Inspiré par SuperAGI.
"""

from typing import Dict, Type, Optional, Any, Callable
from dataclasses import dataclass
import logging
import uuid

from .base_agent import BaseAgent, AgentConfig, AgentStatus, Task

logger = logging.getLogger("agents.factory")


@dataclass
class AgentSpec:
    name: str
    agent_class: Type
    description: str
    default_config: Dict
    category: str = "general"
    required_tools: list = None

    def __post_init__(self):
        if self.required_tools is None:
            self.required_tools = []


class AgentFactory:
    """
    Fabrique d'agents - Crée et enregistre les agents.
    
    Usage:
        AgentFactory.register("research", ResearchAgent, {...})
        agent = AgentFactory.create("research", config={...})
    """

    _registry: Dict[str, AgentSpec] = {}
    _instances: Dict[str, BaseAgent] = {}

    @classmethod
    def register(
        cls,
        name: str,
        agent_class: Type,
        description: str,
        default_config: Dict,
        category: str = "general",
        required_tools: list = None
    ):
        """
        Enregistre un nouveau type d'agent.
        
        Args:
            name: Nom unique
            agent_class: Classe de l'agent (sous-classe de BaseAgent)
            description: Description pour l'UI
            default_config: Configuration par défaut
            category: Catégorie (research, code, write, etc.)
            required_tools: Liste des outils requis
        """
        if name in cls._registry:
            logger.warning(f"[Factory] Agent type {name} already registered, replacing")
        
        cls._registry[name] = AgentSpec(
            name=name,
            agent_class=agent_class,
            description=description,
            default_config=default_config,
            category=category,
            required_tools=required_tools or []
        )
        logger.info(f"[Factory] Registered agent type: {name} (category: {category})")

    @classmethod
    def create(
        cls,
        name: str,
        config: Dict = None,
        llm_client: Any = None,
        tool_registry: Any = None
    ) -> Optional[BaseAgent]:
        """
        Crée une instance d'agent.
        
        Args:
            name: Type d'agent (doit être enregistré)
            config: Configuration spécifique (fusionnée avec defaults)
            llm_client: Client LLM optionnel
            tool_registry: Registre d'outils optionnel
            
        Returns:
            Instance de l'agent ou None si non trouvé
        """
        if name not in cls._registry:
            logger.error(f"[Factory] Unknown agent type: {name}")
            return None

        spec = cls._registry[name]
        final_config = {**spec.default_config, **(config or {})}
        
        agent = spec.agent_class(
            name=final_config.get("name", name),
            description=final_config.get("description", spec.description),
            model=final_config.get("model", "default"),
            temperature=final_config.get("temperature", 0.7),
            max_tokens=final_config.get("max_tokens", 2048),
            tools=final_config.get("tools", []),
            memory_enabled=final_config.get("memory_enabled", True),
            max_iterations=final_config.get("max_iterations", 10),
            timeout=final_config.get("timeout", 300),
            system_prompt=final_config.get("system_prompt", "")
        )

        if llm_client:
            agent.set_llm_client(llm_client)
        
        if tool_registry:
            agent.set_tool_registry(tool_registry)

        instance_id = f"{name}_{uuid.uuid4().hex[:8]}"
        cls._instances[instance_id] = agent
        
        logger.info(f"[Factory] Created agent instance: {instance_id}")
        
        return agent

    @classmethod
    def create_with_hemispheres(
        cls,
        name: str,
        left_hemisphere=None,
        right_hemisphere=None,
        config: Dict = None
    ) -> Optional[BaseAgent]:
        """
        Crée un agent avec hemispheres bicamérales.
        
        Args:
            name: Type d'agent
            left_hemisphere: Hémisphère gauche (analytique)
            right_hemisphere: Hémisphère droit (intuitif)
            config: Configuration
            
        Returns:
            Agent configuré
        """
class BicameralLLM:
    """
    Wrapper for using both hemispheres.
    ALWAYS produces synthesis of both.
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def think(self, system, prompt, temperature=0.7):
        from core.system.identity_manager import get_entity_name
        entity_name = get_entity_name()
        
        if self.left and self.right:
            l = self.left.think(
                f"You are the analytical hemisphere of {entity_name}. Be precise and structured.",
                prompt,
                temperature=0.5
            )
            r = self.right.think(
                f"You are the intuitive hemisphere of {entity_name}. Be creative and original.",
                prompt,
                temperature=0.9
            )
            
            synth_prompt = f"Synthesize these two responses into one:\n\nAnalysis:\n{l}\n\nIntuition:\n{r}"
            if self.left:
                from core.system.identity_manager import get_entity_name
                entity_name = get_entity_name()
                synthesis = self.left.think(
                    f"Synthesize the two perspectives for {entity_name}.",
                    synth_prompt,
                    temperature=0.6
                )
            else:
                synthesis = r
            
            return f"**Analysis (DIA):**\n{l[:300]}\n\n**Intuition (PAL):**\n{r[:300]}\n\n---\n\n**SYNTHESIS:**\n{synthesis[:500]}"
        
        elif self.left:
            return self.left.think(system, prompt, temperature)
        elif self.right:
            return self.right.think(system, prompt, temperature)
        return "No hemisphere available. Please load models."
        
        llm = BicameralLLM(left_hemisphere, right_hemisphere)
        return cls.create(name, config, llm_client=llm)

    @classmethod
    def get(cls, instance_id: str) -> Optional[BaseAgent]:
        """Récupère une instance par ID"""
        return cls._instances.get(instance_id)

    @classmethod
    def list_agents(cls, category: Optional[str] = None) -> Dict:
        """
        Liste les types d'agents disponibles.
        
        Returns:
            Dict de {name: info}
        """
        agents = {}
        for name, spec in cls._registry.items():
            if category and spec.category != category:
                continue
            agents[name] = {
                "description": spec.description,
                "category": spec.category,
                "default_config": spec.default_config,
                "required_tools": spec.required_tools
            }
        return agents

    @classmethod
    def list_categories(cls) -> list:
        """Liste les catégories disponibles"""
        categories = set()
        for spec in cls._registry.values():
            categories.add(spec.category)
        return sorted(list(categories))

    @classmethod
    def get_instances(cls) -> Dict[str, Dict]:
        """Liste les instances actives"""
        instances = {}
        for id_, agent in cls._instances.items():
            instances[id_] = agent.get_state()
        return instances


class TaskQueue:
    """
    File de tâches pour les agents.
    """

    def __init__(self, max_size: int = 100):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._processing: bool = False

    async def add_task(self, agent: BaseAgent, task: Task):
        """Ajoute une tâche à la file"""
        await self._queue.put((agent, task))
        logger.info(f"[TaskQueue] Added task {task.id} for {agent.config.name}")

    async def process_next(self) -> bool:
        """Traite la prochaine tâche"""
        if self._queue.empty():
            return False

        agent, task = await self._queue.get()
        
        try:
            await agent.run(task)
            return True
        except Exception as e:
            logger.error(f"[TaskQueue] Error processing task: {e}")
            return False
        finally:
            self._queue.task_done()

    async def process_all(self):
        """Traite toutes les tâches en file"""
        self._processing = True
        
        while not self._queue.empty():
            await self.process_next()
        
        self._processing = False

    def size(self) -> int:
        """Taille de la file"""
        return self._queue.qsize()

    def is_empty(self) -> bool:
        """La file est-elle vide?"""
        return self._queue.empty()


def register_builtin_agents():
    """Enregistre les agents intégrés"""
    from .specialized.research_agent import ResearchAgent
    from .specialized.coder_agent import CoderAgent
    from .specialized.writer_agent import WriterAgent

    AgentFactory.register(
        name="research",
        agent_class=ResearchAgent,
        description="Agent de recherche avec sources vérifiées",
        default_config={
            "name": "Research Agent",
            "description": "Recherche des informations vérifiées sans hallucination",
            "temperature": 0.3,
            "max_iterations": 5,
            "system_prompt": "You are a research assistant. Find verified information."
        },
        category="research",
        required_tools=["web_search", "file_search"]
    )

    AgentFactory.register(
        name="coder",
        agent_class=CoderAgent,
        description="Agent de génération de code avec tests",
        default_config={
            "name": "Coder Agent",
            "description": "Génère du code et exécute des tests",
            "temperature": 0.5,
            "max_iterations": 3,
            "system_prompt": "You are a code generation assistant. Write clean, tested code."
        },
        category="code",
        required_tools=["code_executor"]
    )

    AgentFactory.register(
        name="writer",
        agent_class=WriterAgent,
        description="Agent de rédaction et révision",
        default_config={
            "name": "Writer Agent",
            "description": "Rédige et revise du contenu",
            "temperature": 0.7,
            "max_iterations": 3,
            "system_prompt": "You are a writing assistant. Write clear, engaging content."
        },
        category="write"
    )
