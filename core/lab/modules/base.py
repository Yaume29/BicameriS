"""
Lab Module Base Class
=====================
Classe de base pour tous les modules du laboratoire.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger("lab.module")


class LabModule(ABC):
    """
    Classe de base abstraite pour les modules du laboratoire.
    
    Pour créer un nouveau module:
    1. Créer un dossier dans core/lab/modules/ nommé: X_NomModule (X = chiffre pour l'ordre)
    2. Créer un fichier __init__.py qui expose votre classe
    3. Hériter de cette classe LabModule
    """
    
    id: str = "base-module"
    name: str = "Base Module"
    icon: str = "📦"
    description: str = "Module de base"
    order: int = 99
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._active = False
        logger.info(f"[Module] {self.name} initialisé")
    
    @abstractmethod
    def render(self) -> str:
        """
        Retourne le HTML du module.
        """
        pass
    
    def handle_action(self, action: str, data: Dict) -> Dict:
        """
        Gère les actions reçues depuis le frontend.
        
        Args:
            action: Nom de l'action
            data: Données reçues
            
        Returns:
            Réponse JSON
        """
        return {"status": "error", "message": f"Action non implémentée: {action}"}
    
    def get_config(self) -> Dict:
        """
        Retourne la configuration du module.
        """
        return self.config
    
    def set_config(self, config: Dict):
        """
        Met à jour la configuration.
        """
        self.config.update(config)
    
    def activate(self):
        """Active le module"""
        self._active = True
        logger.info(f"[Module] {self.name} activé")
    
    def deactivate(self):
        """Désactive le module"""
        self._active = False
        logger.info(f"[Module] {self.name} désactivé")
    
    @property
    def is_active(self) -> bool:
        return self._active
    
    def to_dict(self) -> Dict:
        """Sérialisation du module"""
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "order": self.order,
            "active": self._active
        }
