"""
Specialists - Agents IA spécialisés
==================================
Chaque specialist a son propre comportement, température et focus.
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Specialist:
    """Specialist AI avec configuration"""
    id: str
    name: str
    description: str
    icon: str
    hemisphere: str  # left, right, both
    temperature: float
    system_prompt: str
    capabilities: list


# Default specialists configuration
SPECIALISTS = {
    "research": Specialist(
        id="research",
        name="Research",
        description="Recherche scientifique et génération d'idées",
        icon="🔬",
        hemisphere="both",
        temperature=0.8,
        system_prompt="""Tu es un chercheur IA spécialisé dans la recherche scientifique.
Tu peux:
- Analyser des articles et papers
- Proposer des hypothèses de recherche
- Générer des idées originales
- Rédiger des rapports scientifiques
- Formuler des méthodologies

Réponds de manière rigoureuse et cite tes sources quand possible.""",
        capabilities=["analyze", "hypothesize", "write", "research"]
    ),
    "python": Specialist(
        id="python",
        name="Python Expert",
        description="Expert en code Python",
        icon="🐍",
        hemisphere="left",
        temperature=0.3,
        system_prompt="""Tu es un expert Python.
Tu peux:
- Écrire du code Python propre et performant
- Déboguer des erreurs
- Expliquer des concepts
- Refactorer du code
- Créer des scripts

Réponds de manière précise et logique.""",
        capabilities=["code", "debug", "explain", "refactor", "script"]
    ),
    "uiux": Specialist(
        id="uiux",
        name="UI/UX Designer",
        description="Design d'interfaces",
        icon="🎨",
        hemisphere="right",
        temperature=1.0,
        system_prompt="""Tu es un designer UI/UX expert.
Tu peux:
- Créer des designs d'interfaces
- Proposer des expériences utilisateur
- Analyser des designs existants
- Créer des palettes de couleurs
- Designer des composants

Réponds de manière créative et orientée utilisateur.""",
        capabilities=["design", "prototype", "colors", "ux", "components"]
    ),
    "multi": Specialist(
        id="multi",
        name="Multi Expert",
        description="Polyvalent",
        icon="🌐",
        hemisphere="both",
        temperature=0.7,
        system_prompt="""Tu es un expert polyvalent.
Tu peux handle tout type de demande:
- Recherche
- Code
- Design
- Analyse

Adapte ton approche selon la requête.""",
        capabilities=["research", "code", "design", "analyze", "write"]
    )
}


class SpecialistManager:
    """Gestionnaire de specialists"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.specialists = SPECIALISTS.copy()
        self.enabled_specialists = self._load_enabled()
        
        logging.info(f"[SpecialistManager] Loaded {len(self.specialists)} specialists")
    
    def _load_enabled(self) -> Dict:
        """Charge les specialists activés depuis la config"""
        enabled = {}
        lab_config = self.config.get("lab", {}).get("modules", {})
        
        for specialist_id, specialist in self.specialists.items():
            if lab_config.get(specialist_id, {}).get("enabled", True):
                enabled[specialist_id] = specialist
        
        return enabled
    
    def get_specialist(self, specialist_id: str) -> Optional[Specialist]:
        """Récupère un specialist"""
        return self.specialists.get(specialist_id)
    
    def get_enabled_specialists(self) -> Dict:
        """Récupère les specialists activés"""
        return self.enabled_specialists
    
    def list_specialists(self) -> list:
        """Liste tous les specialists"""
        return list(self.specialists.values())
    
    def is_enabled(self, specialist_id: str) -> bool:
        """Vérifie si un specialist est activé"""
        return specialist_id in self.enabled_specialists
    
    def enable_specialist(self, specialist_id: str):
        """Active un specialist"""
        if specialist_id in self.specialists:
            self.enabled_specialists[specialist_id] = self.specialists[specialist_id]
            logging.info(f"[SpecialistManager] Enabled: {specialist_id}")
    
    def disable_specialist(self, specialist_id: str):
        """Désactive un specialist"""
        if specialist_id in self.enabled_specialists:
            del self.enabled_specialists[specialist_id]
            logging.info(f"[SpecialistManager] Disabled: {specialist_id}")


# Global instance
_specialist_manager = None


def get_specialist_manager(config: Dict = None) -> SpecialistManager:
    """Récupère l'instance globale du Gestionnaire de Specialists"""
    global _specialist_manager
    if _specialist_manager is None:
        _specialist_manager = SpecialistManager(config)
    return _specialist_manager


def get_specialist(specialist_id: str) -> Optional[Specialist]:
    """Récupère un specialist"""
    manager = get_specialist_manager()
    return manager.get_specialist(specialist_id)
