"""
Agent System - Multi-Agent Coordination (FIXED)
================================================
Pattern: AGiXT + AutoGPT + Cline + GPT Researcher
Implémentation 100% locale sans API keys.

FIXES:
1. Factory Pattern pour reconstruction des agents
2. deque pour mémoire circulaire O(1)
3. Blackboard pattern pour le chaînage
4. lru_cache pour singleton thread-safe
"""

import logging
import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from collections import deque
from functools import lru_cache


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
AGENTS_DIR = BASE_DIR / "storage" / "agents"


class AgentStatus(str, Enum):
    """Statuts possibles d'un agent"""
    DISABLED = "disabled"
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    ERROR = "error"


class AgentType(str, Enum):
    """Types d'agents disponibles"""
    CRITIC = "critic"
    RESEARCHER = "researcher"
    CODER = "coder"
    SYNTHESIZER = "synthesizer"
    DECOMPOSER = "decomposer"
    ETHIC = "ethic"
    MEMORY = "memory"
    AUTONOMOUS = "autonomous"
    LOGIC = "logic"
    INTUITION = "intuition"


@dataclass
class AgentConfig:
    """Configuration d'un agent"""
    name: str
    agent_type: AgentType
    description: str
    enabled: bool = True
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = ""
    priority: int = 5
    metadata: Dict = field(default_factory=dict)


@dataclass
class AgentResult:
    """Résultat d'exécution d'un agent"""
    agent_name: str
    status: AgentStatus
    output: str
    confidence: float = 0.0
    sources: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    timestamp: str = ""


@dataclass
class Blackboard:
    """
    Mémoire partagée pour le chaînage d'agents.
    Pattern: Blackboard Architecture
    
    Chaque agent lit et écrit dans le blackboard,
    plutôt que de passer des dictionnaires modifiés.
    """
    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    
    def write(self, key: str, value: Any, agent_name: str):
        """Écrit une valeur dans le blackboard"""
        self.data[key] = {
            "value": value,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append({
            "key": key,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat()
        })
    
    def read(self, key: str, default: Any = None) -> Any:
        """Lit une valeur du blackboard"""
        entry = self.data.get(key)
        if entry:
            return entry.get("value", default)
        return default
    
    def read_agent_output(self, agent_name: str) -> Optional[str]:
        """Lit la dernière sortie d'un agent spécifique"""
        for key, entry in reversed(list(self.data.items())):
            if entry.get("agent") == agent_name:
                return entry.get("value")
        return None
    
    def get_all(self) -> Dict[str, Any]:
        """Retourne toutes les données"""
        return {k: v.get("value") for k, v in self.data.items()}
    
    def clear(self):
        """Vide le blackboard"""
        self.data.clear()
        self.history.clear()


class BaseAgent(ABC):
    """
    Classe abstraite pour tous les agents.
    Pattern: Strategy + Template Method + Blackboard
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        # FIX 2: Utiliser deque pour mémoire circulaire O(1)
        self.execution_history: deque = deque(maxlen=100)
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """
        Exécute l'agent avec les données d'entrée.
        
        Args:
            input_data: Données d'entrée spécifiques à l'agent
            blackboard: Mémoire partagée pour le chaînage (optionnel)
        
        Chaque agent implémente sa propre logique.
        Si blackboard est fourni, l'agent peut lire les résultats
        d'autres agents via blackboard.read_agent_output(agent_name).
        """
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Retourne le system prompt pour cet agent"""
        pass
    
    def update_status(self, status: AgentStatus):
        """Met à jour le statut de l'agent"""
        self.status = status
    
    def add_to_history(self, result: AgentResult):
        """Ajoute un résultat à l'historique (O(1) avec deque)"""
        # FIX 2: deque.append fait tout le travail, zéro réallocation
        self.execution_history.append(result)
    
    def get_stats(self) -> Dict:
        """Statistiques de l'agent"""
        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.status == AgentStatus.EXECUTING)
        return {
            "name": self.config.name,
            "type": self.config.agent_type.value,
            "enabled": self.config.enabled,
            "status": self.status.value,
            "total_executions": total,
            "success_rate": success / max(total, 1),
        }


# ============================================
# FIX 1: FACTORY PATTERN
# ============================================

# Registre global des classes d'agents
_AGENT_CLASSES: Dict[AgentType, Type[BaseAgent]] = {}


def register_agent_class(agent_type: AgentType):
    """
    Décorateur pour enregistrer une classe d'agent.
    
    Usage:
        @register_agent_class(AgentType.CRITIC)
        class CriticAgent(BaseAgent):
            ...
    """
    def decorator(cls: Type[BaseAgent]):
        _AGENT_CLASSES[agent_type] = cls
        logging.info(f"[AgentFactory] Registered: {agent_type.value} -> {cls.__name__}")
        return cls
    return decorator


def get_agent_class(agent_type: AgentType) -> Optional[Type[BaseAgent]]:
    """Récupère une classe d'agent par son type"""
    return _AGENT_CLASSES.get(agent_type)


def get_all_agent_classes() -> Dict[AgentType, Type[BaseAgent]]:
    """Récupère toutes les classes d'agents enregistrées"""
    return _AGENT_CLASSES.copy()


# ============================================
# AGENT REGISTRY (FIXED)
# ============================================

class AgentRegistry:
    """
    Registre centralisé des agents.
    Pattern: Singleton via lru_cache + Factory pour reconstruction
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.configs: Dict[str, AgentConfig] = {}
        self.storage_file = AGENTS_DIR / "agents_config.json"
        AGENTS_DIR.mkdir(parents=True, exist_ok=True)
        self._load_config()
    
    def _load_config(self):
        """
        Charge la configuration des agents.
        FIX 1: Reconstruit les instances d'agents via Factory Pattern.
        """
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    for name, config_data in data.items():
                        # Reconstruire l'AgentConfig
                        if isinstance(config_data.get("agent_type"), str):
                            config_data["agent_type"] = AgentType(config_data["agent_type"])
                        
                        config = AgentConfig(**config_data)
                        self.configs[name] = config
                        
                        # FIX 1: RECONSTRUCTION DE L'AGENT PHYSIQUE via Factory
                        agent_class = get_agent_class(config.agent_type)
                        if agent_class:
                            try:
                                self.agents[name] = agent_class(config)
                                logging.info(f"[AgentRegistry] Reconstructed: {name} ({config.agent_type.value})")
                            except Exception as e:
                                logging.warning(f"[AgentRegistry] Failed to reconstruct {name}: {e}")
                        else:
                            logging.warning(f"[AgentRegistry] No class registered for type: {config.agent_type.value}")
                
            except Exception as e:
                logging.error(f"[AgentRegistry] Load error: {e}")
                self.agents = {}
                self.configs = {}
    
    def _save_config(self):
        """Sauvegarde la configuration"""
        try:
            data = {
                name: {
                    "name": config.name,
                    "agent_type": config.agent_type.value,
                    "description": config.description,
                    "enabled": config.enabled,
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                    "system_prompt": config.system_prompt,
                    "priority": config.priority,
                    "metadata": config.metadata
                }
                for name, config in self.configs.items()
            }
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[AgentRegistry] Save error: {e}")
    
    def register(self, agent: BaseAgent):
        """Enregistre un agent"""
        self.agents[agent.config.name] = agent
        self.configs[agent.config.name] = agent.config
        self._save_config()
        logging.info(f"[AgentRegistry] Agent registered: {agent.config.name}")
    
    def unregister(self, name: str):
        """Désenregistre un agent"""
        if name in self.agents:
            del self.agents[name]
        if name in self.configs:
            del self.configs[name]
        self._save_config()
    
    def enable_agent(self, name: str):
        """Active un agent"""
        if name in self.configs:
            self.configs[name].enabled = True
            self._save_config()
            logging.info(f"[AgentRegistry] Agent enabled: {name}")
    
    def disable_agent(self, name: str):
        """Désactive un agent"""
        if name in self.configs:
            self.configs[name].enabled = False
            self._save_config()
            logging.info(f"[AgentRegistry] Agent disabled: {name}")
    
    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Récupère un agent par son nom"""
        return self.agents.get(name)
    
    def get_enabled_agents(self) -> List[BaseAgent]:
        """Récupère tous les agents activés"""
        return [
            agent for name, agent in self.agents.items()
            if self.configs.get(name, AgentConfig(name="", agent_type=AgentType.CRITIC, description="")).enabled
        ]
    
    def get_all_agents(self) -> List[Dict]:
        """Récupère tous les agents avec leur statut"""
        result = []
        for name, agent in self.agents.items():
            config = self.configs.get(name)
            result.append({
                "name": name,
                "type": config.agent_type.value if config else "unknown",
                "description": config.description if config else "",
                "enabled": config.enabled if config else False,
                "status": agent.status.value,
                "temperature": config.temperature if config else 0.7,
                "max_tokens": config.max_tokens if config else 1000,
                "priority": config.priority if config else 5,
            })
        return result
    
    def update_agent_config(self, name: str, **kwargs):
        """Met à jour la configuration d'un agent"""
        if name in self.configs:
            config = self.configs[name]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            self._save_config()
    
    def get_stats(self) -> Dict:
        """Statistiques du registre"""
        return {
            "total_agents": len(self.agents),
            "enabled_agents": len(self.get_enabled_agents()),
            "agent_types": {
                agent_type.value: len([a for a in self.agents.values() if a.config.agent_type == agent_type])
                for agent_type in AgentType
            },
            "registered_classes": len(_AGENT_CLASSES),
        }


# ============================================
# AGENT COORDINATOR (FIXED)
# ============================================

class AgentCoordinator:
    """
    Orchestrateur multi-agent.
    Pattern: Mediator + Command + Blackboard
    
    NOTE: Cet orchestrateur est un composant de haut niveau.
    Le Conductor existant gère les Hémisphères (DIA/PAL).
    L'AgentCoordinator gère les agents spécialisés (Critic, Researcher, etc.).
    """
    
    def __init__(self, registry: AgentRegistry):
        self.registry = registry
        self.history: List[Dict] = []
    
    async def execute_agent(
        self,
        agent_name: str,
        input_data: Dict,
        blackboard: Blackboard = None
    ) -> AgentResult:
        """Exécute un agent spécifique"""
        agent = self.registry.get_agent(agent_name)
        if not agent:
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.ERROR,
                output=f"Agent {agent_name} not found"
            )
        
        if not self.registry.configs.get(agent_name, AgentConfig(name="", agent_type=AgentType.CRITIC, description="")).enabled:
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.DISABLED,
                output=f"Agent {agent_name} is disabled"
            )
        
        agent.update_status(AgentStatus.THINKING)
        
        try:
            # FIX 3: Passer le blackboard pour le chaînage
            result = await agent.execute(input_data, blackboard=blackboard)
            agent.update_status(AgentStatus.IDLE)
            agent.add_to_history(result)
            
            # Écrire le résultat dans le blackboard
            if blackboard:
                blackboard.write(f"output_{agent_name}", result.output, agent_name)
            
            return result
        except Exception as e:
            agent.update_status(AgentStatus.ERROR)
            return AgentResult(
                agent_name=agent_name,
                status=AgentStatus.ERROR,
                output=f"Error: {str(e)}"
            )
    
    async def execute_parallel(
        self,
        agent_names: List[str],
        input_data: Dict
    ) -> List[AgentResult]:
        """Exécute plusieurs agents en parallèle"""
        tasks = [
            self.execute_agent(name, input_data)
            for name in agent_names
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def execute_chain(
        self,
        agent_names: List[str],
        initial_input: Dict
    ) -> AgentResult:
        """
        Exécute une chaîne d'agents séquentiels.
        FIX 3: Utilise Blackboard au lieu de passer des dictionnaires modifiés.
        """
        blackboard = Blackboard()
        
        # Écrire l'input initial dans le blackboard
        for key, value in initial_input.items():
            blackboard.write(key, value, "input")
        
        last_result = None
        
        for agent_name in agent_names:
            # FIX 3: Chaque agent lit le blackboard pour obtenir les résultats précédents
            result = await self.execute_agent(agent_name, initial_input, blackboard=blackboard)
            
            if result.status == AgentStatus.ERROR:
                return result
            
            last_result = result
        
        return last_result or AgentResult(
            agent_name="chain",
            status=AgentStatus.ERROR,
            output="Chain execution failed"
        )
    
    def get_stats(self) -> Dict:
        """Statistiques de l'orchestrateur"""
        return {
            "history_size": len(self.history),
            "agents_stats": self.registry.get_stats()
        }


# ============================================
# FIX 4: SINGLETON THREAD-SAFE VIA lru_cache
# ============================================

@lru_cache()
def get_agent_registry() -> AgentRegistry:
    """
    Récupère le registre global des agents.
    FIX 4: Thread-safe via lru_cache (garantit un seul objet).
    """
    return AgentRegistry()


@lru_cache()
def get_agent_coordinator() -> AgentCoordinator:
    """
    Récupère l'orchestrateur global.
    FIX 4: Thread-safe via lru_cache (garantit un seul objet).
    """
    return AgentCoordinator(get_agent_registry())
