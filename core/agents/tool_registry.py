"""
Tool Registry
=============
Système de registre d'outils pour les agents.
Inspiré par AutoGPT.

Désactivé par défaut - chaque outil doit être activé explicitement.
"""

from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
import logging
import asyncio
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger("agents.tool_registry")


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    category: str = "general"
    enabled: bool = False
    requires_auth: bool = False
    examples: List[str] = field(default_factory=list)
    version: str = "1.0.0"


@dataclass
class ToolExecution:
    tool_name: str
    parameters: Dict
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    status: str = "pending"


class ToolRegistry:
    """
    Registre central d'outils disponibles pour les agents.
    
    Désactivé par défaut (enabled=False pour chaque outil).
    Utilisez enable(name) pour activer un outil spécifique.
    """

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._categories: Dict[str, List[str]] = {}
        self._enabled_tools: set = set()
        self._execution_history: List[ToolExecution] = []
        self._max_history: int = 1000
        self._global_enabled: bool = False
        self._cache: Dict[str, Dict] = {}
        self._max_cache_per_tool: int = 128

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable,
        category: str = "general",
        enabled: bool = False,
        examples: List[str] = None
    ) -> bool:
        """
        Enregistre un nouvel outil.
        
        Args:
            name: Nom unique de l'outil
            description: Description pour le LLM
            parameters: Schéma des paramètres (JSON Schema)
            function: Fonction à exécuter
            category: Catégorie (research, code, search, etc.)
            enabled: Activé par défaut (False)
            examples: Exemples d'utilisation
            
        Returns:
            True si enregistré, False si déjà existant
        """
        if name in self._tools:
            logger.warning(f"[ToolRegistry] Tool {name} already registered, skipping")
            return False

        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            function=function,
            category=category,
            enabled=enabled,
            examples=examples or []
        )

        self._tools[name] = tool

        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(name)

        if enabled:
            self._enabled_tools.add(name)

        logger.info(f"[ToolRegistry] Registered tool: {name} (enabled={enabled}, category={category})")
        return True

    def enable(self, name: str) -> bool:
        """Active un outil"""
        if name not in self._tools:
            logger.warning(f"[ToolRegistry] Tool {name} not found")
            return False
        
        if not self._global_enabled:
            logger.warning(f"[ToolRegistry] Tool registry is disabled globally")
            return False
        
        self._tools[name].enabled = True
        self._enabled_tools.add(name)
        logger.info(f"[ToolRegistry] Enabled tool: {name}")
        return True

    def disable(self, name: str) -> bool:
        """Désactive un outil"""
        if name not in self._tools:
            return False
        
        self._tools[name].enabled = False
        self._enabled_tools.discard(name)
        logger.info(f"[ToolRegistry] Disabled tool: {name}")
        return True

    def enable_all(self, category: str = None):
        """Active tous les outils ou ceux d'une catégorie"""
        for name, tool in self._tools.items():
            if category is None or tool.category == category:
                tool.enabled = True
                self._enabled_tools.add(name)
        logger.info(f"[ToolRegistry] Enabled all tools" + (f" in {category}" if category else ""))

    def disable_all(self):
        """Désactive tous les outils"""
        for tool in self._tools.values():
            tool.enabled = False
        self._enabled_tools.clear()
        logger.info(f"[ToolRegistry] Disabled all tools")

    def is_enabled(self, name: str) -> bool:
        """Vérifie si un outil est actif"""
        return name in self._enabled_tools and self._global_enabled

    def is_global_enabled(self) -> bool:
        """Vérifie si le registre est globalement activé"""
        return self._global_enabled

    def enable_global(self):
        """Active le registre global"""
        self._global_enabled = True
        logger.info("[ToolRegistry] Global enabled")

    def disable_global(self):
        """Désactive le registre global"""
        self._global_enabled = False
        logger.info("[ToolRegistry] Global disabled")

    def list_tools(self, category: Optional[str] = None, enabled_only: bool = True) -> List[Dict]:
        """
        Liste les outils disponibles.
        
        Args:
            category: Filtrer par catégorie
            enabled_only: Ne montrer que les outils activés
        """
        tools = []
        for name, tool in self._tools.items():
            if enabled_only and not tool.enabled:
                continue
            if category and tool.category != category:
                continue
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "enabled": tool.enabled,
                "examples": tool.examples[:3]
            })
        return tools

    def list_categories(self) -> List[str]:
        """Liste les catégories disponibles"""
        return list(self._categories.keys())

    def get_tool_info(self, name: str) -> Optional[Dict]:
        """Retourne les infos d'un outil"""
        if name not in self._tools:
            return None
        
        tool = self._tools[name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "category": tool.category,
            "enabled": tool.enabled,
            "examples": tool.examples,
            "version": tool.version
        }

    async def execute(self, name: str, parameters: Dict) -> Dict:
        """
        Exécute un outil.
        
        Returns:
            Dict avec status, result/error, et métadonnées
        """
        execution = ToolExecution(
            tool_name=name,
            parameters=parameters,
            start_time=datetime.now()
        )

        if name not in self._tools:
            execution.status = "error"
            execution.error = f"Tool {name} not found"
            self._add_execution(execution)
            return {"status": "error", "message": f"Tool {name} not found"}

        tool = self._tools[name]

        if not tool.enabled:
            execution.status = "error"
            execution.error = f"Tool {name} is disabled"
            self._add_execution(execution)
            return {"status": "error", "message": f"Tool {name} is disabled"}

        if not self._global_enabled:
            execution.status = "error"
            execution.error = "Tool registry is disabled globally"
            self._add_execution(execution)
            return {"status": "error", "message": "Tool registry is disabled globally"}

        try:
            if tool.enabled:
                cache_key = (name, frozenset(parameters.items()))
                if name in self._cache and cache_key in self._cache[name]:
                    cached = self._cache[name][cache_key]
                    self._add_execution(execution)
                    return cached

            if asyncio.iscoroutinefunction(tool.function):
                result = await tool.function(**parameters)
            else:
                result = tool.function(**parameters)

            execution.result = result
            execution.status = "success"
            execution.end_time = datetime.now()

            self._add_execution(execution)

            response = {
                "status": "ok",
                "result": result,
                "tool": name,
                "execution_time_ms": (execution.end_time - execution.start_time).total_seconds() * 1000
            }

            if tool.enabled:
                if name not in self._cache:
                    self._cache[name] = {}
                tool_cache = self._cache[name]
                if len(tool_cache) >= self._max_cache_per_tool:
                    oldest_key = next(iter(tool_cache))
                    del tool_cache[oldest_key]
                tool_cache[cache_key] = response

            return response

        except Exception as e:
            logger.error(f"[ToolRegistry] Tool execution error: {e}")
            execution.status = "error"
            execution.error = str(e)
            execution.end_time = datetime.now()
            self._add_execution(execution)

            return {
                "status": "error",
                "message": str(e),
                "tool": name
            }

    def _add_execution(self, execution: ToolExecution):
        """Ajoute une exécution à l'historique"""
        self._execution_history.append(execution)
        if len(self._execution_history) > self._max_history:
            self._execution_history = self._execution_history[-self._max_history:]

    def clear_cache(self):
        self._cache.clear()

    def invalidate_cache(self, tool_name: str):
        self._cache.pop(tool_name, None)

    def get_history(self, limit: int = 50, tool_name: str = None, status: str = None) -> List[Dict]:
        """Historique des exécutions"""
        history = self._execution_history[-limit:]
        
        if tool_name:
            history = [h for h in history if h.tool_name == tool_name]
        if status:
            history = [h for h in history if h.status == status]
        
        return [
            {
                "tool": h.tool_name,
                "status": h.status,
                "start_time": h.start_time.isoformat(),
                "execution_time_ms": (h.end_time - h.start_time).total_seconds() * 1000 if h.end_time else None,
                "error": h.error
            }
            for h in history
        ]

    def get_stats(self) -> Dict:
        """Statistiques d'utilisation"""
        total = len(self._execution_history)
        success = len([h for h in self._execution_history if h.status == "success"])
        errors = len([h for h in self._execution_history if h.status == "error"])
        
        tool_usage = {}
        for h in self._execution_history:
            tool_usage[h.tool_name] = tool_usage.get(h.tool_name, 0) + 1
        
        return {
            "total_executions": total,
            "success": success,
            "errors": errors,
            "success_rate": success / total if total > 0 else 0,
            "tools_registered": len(self._tools),
            "tools_enabled": len(self._enabled_tools),
            "global_enabled": self._global_enabled,
            "tool_usage": tool_usage
        }


_tool_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Retourne l'instance globale du registre d'outils"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


def register_tool(
    name: str,
    description: str,
    parameters: Dict,
    function: Callable,
    category: str = "general",
    enabled: bool = False,
    examples: List[str] = None
):
    """Helper pour enregistrer un outil rapidement"""
    return get_tool_registry().register(
        name=name,
        description=description,
        parameters=parameters,
        function=function,
        category=category,
        enabled=enabled,
        examples=examples
    )
