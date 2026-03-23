"""
Agent Manager for Aetheris
Découverte et gestion dynamique des agents dans le dossier /aetheris/agents/
"""

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Callable


class AgentManager:
    """
    Gère le chargement et l'accès aux agents auto-générés par Aetheris.
    Chaque agent est un module Python avec une fonction `introspect()`.
    """
    
    def __init__(self, agents_path: str = "/aetheris/agents"):
        self.agents_path = Path(agents_path)
        self.agents: Dict[str, Any] = {}
        self._loaded = False
        
        # Créer le dossier s'il n'existe pas
        self.agents_path.mkdir(parents=True, exist_ok=True)
    
    def discover(self) -> Dict[str, Any]:
        """
        Parcourt le dossier agents/ et charge tous les modules Python.
        Retourne un dictionnaire {nom_agent: module}
        """
        self.agents = {}
        
        # Chercher tous les fichiers .py dans agents/
        for py_file in self.agents_path.glob("*.py"):
            # Ignorer __init__.py et les fichiers commençant par _
            if py_file.name.startswith("__"):
                continue
            
            module_name = py_file.stem
            module_path = str(py_file)
            
            try:
                # Charger le module dynamiquement
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    self.agents[module_name] = module
                    
            except Exception as e:
                print(f"[AgentManager] Erreur chargement {module_name}: {e}")
        
        self._loaded = True
        return self.agents
    
    def list_agents(self) -> list:
        """Retourne la liste des noms d'agents disponibles."""
        if not self._loaded:
            self.discover()
        return list(self.agents.keys())
    
    def get_agent(self, name: str) -> Optional[Any]:
        """Retourne un agent par son nom, ou None s'il n'existe pas."""
        if not self._loaded:
            self.discover()
        return self.agents.get(name)
    
    def introspect(self, name: str) -> Optional[str]:
        """
        Appelle la fonction introspect() d'un agent si elle existe.
        Retourne le résultat ou None.
        """
        agent = self.get_agent(name)
        if agent and hasattr(agent, "introspect"):
            try:
                return agent.introspect()
            except Exception as e:
                return f"[Erreur introspect {name}] {e}"
        return None
    
    def call_agent_function(self, name: str, func_name: str, *args, **kwargs) -> Any:
        """
        Appelle une fonction spécifique d'un agent.
        """
        agent = self.get_agent(name)
        if agent and hasattr(agent, func_name):
            try:
                func = getattr(agent, func_name)
                return func(*args, **kwargs)
            except Exception as e:
                return f"[Erreur appel {func_name}] {e}"
        return None
    
    def reload(self) -> Dict[str, Any]:
        """Recharge tous les agents (utile après création d'un nouvel agent)."""
        # Nettoyer les modules existants
        for name in self.agents:
            if name in sys.modules:
                del sys.modules[name]
        
        self.agents = {}
        self._loaded = False
        return self.discover()
    
    def get_info(self) -> dict:
        """Retourne des informations sur l'état du gestionnaire."""
        if not self._loaded:
            self.discover()
        
        agents_info = {}
        for name, module in self.agents.items():
            agents_info[name] = {
                "has_introspect": hasattr(module, "introspect"),
                "functions": [f for f in dir(module) if not f.startswith("_") and callable(getattr(module, f))]
            }
        
        return {
            "agents_path": str(self.agents_path),
            "agent_count": len(self.agents),
            "agents": agents_info
        }


# Pour un accès direct depuis orchestrator.py
_default_manager = None

def get_agent_manager() -> AgentManager:
    """Singleton pour récupérer le gestionnaire d'agents."""
    global _default_manager
    if _default_manager is None:
        _default_manager = AgentManager()
    return _default_manager