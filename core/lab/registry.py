"""
Lab Module Registry
==================
Système d'auto-découverte des modules du laboratoire.
Scanne le dossier modules/ et charge automatiquement les modules.
"""

import os
import re
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .modules.base import LabModule

logger = logging.getLogger("lab.registry")

MODULES_DIR = Path(__file__).parent / "modules"


class ModuleRegistry:
    """
    Registre central des modules du laboratoire.
    Auto-discovery basé sur le nom des dossiers.
    """
    
    def __init__(self):
        self._modules: Dict[str, LabModule] = {}
        self._module_classes: Dict[str, type] = {}
        self._discovered = False
    
    def discover(self):
        """
        Découvre automatiquement les modules dans le dossier modules/.
        Le nom du dossier détermine l'ordre (ex: 1_Inception -> order=1)
        """
        if self._discovered:
            return
        
        if not MODULES_DIR.exists():
            logger.warning(f"[Registry] Dossier modules inexistant: {MODULES_DIR}")
            return
        
        for item in MODULES_DIR.iterdir():
            if not item.is_dir():
                continue
            
            folder_name = item.name
            
            match = re.match(r'^(\d+)_(\w+)$', folder_name)
            if not match:
                logger.debug(f"[Registry] Ignoré (pas de chiffre): {folder_name}")
                continue
            
            order = int(match.group(1))
            module_name = match.group(2)
            
            init_file = item / "__init__.py"
            if not init_file.exists():
                logger.warning(f"[Registry] Pas de __init__.py dans: {folder_name}")
                continue
            
            try:
                module_path = f"core.lab.modules.{folder_name}"
                module = importlib.import_module(module_path)
                
                module_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, LabModule) and attr != LabModule:
                        module_class = attr
                        break
                
                if module_class:
                    module_class.order = order
                    self._module_classes[module_name.lower()] = module_class
                    logger.info(f"[Registry] Découvert: {folder_name} (order={order})")
                else:
                    logger.warning(f"[Registry] Pas de LabModule dans: {folder_name}")
                    
            except Exception as e:
                logger.error(f"[Registry] Erreur chargement {folder_name}: {e}")
        
        self._discovered = True
        logger.info(f"[Registry] Découverte terminée: {len(self._module_classes)} modules")
    
    def register(self, name: str, module_class: type, config: Dict = None):
        """
        Enregistre un module manuellement.
        """
        if not issubclass(module_class, LabModule):
            raise ValueError(f" doit être un LabModule")
        
        instance = module_class(config)
        self._modules[name.lower()] = instance
        self._module_classes[name.lower()] = module_class
        logger.info(f"[Registry] Enregistré manuellement: {name}")
    
    def get(self, name: str, config: Dict = None) -> Optional[LabModule]:
        """
        Retourne une instance du module par son nom.
        """
        name_lower = name.lower()
        
        if name_lower in self._modules:
            return self._modules[name_lower]
        
        if name_lower in self._module_classes:
            instance = self._module_classes[name_lower](config)
            self._modules[name_lower] = instance
            return instance
        
        return None
    
    def list_modules(self) -> List[Dict]:
        """
        Liste tous les modules triés par ordre.
        """
        self.discover()
        
        modules = []
        for name, cls in self._module_classes.items():
            instance = self._modules.get(name)
            if instance:
                modules.append(instance.to_dict())
            else:
                modules.append({
                    "id": cls.id,
                    "name": cls.name,
                    "icon": cls.icon,
                    "description": cls.description,
                    "order": cls.order,
                    "active": False
                })
        
        return sorted(modules, key=lambda x: x["order"])
    
    def get_active_module(self, name: str) -> Optional[LabModule]:
        """
        Retourne un module actif ou le charge.
        """
        return self.get(name)


_registry = None


def get_registry() -> ModuleRegistry:
    """Singleton du registre"""
    global _registry
    if _registry is None:
        _registry = ModuleRegistry()
        _registry.discover()
    return _registry


def list_lab_modules() -> List[Dict]:
    """Liste tous les modules disponibles"""
    return get_registry().list_modules()


def get_lab_module(name: str, config: Dict = None) -> Optional[LabModule]:
    """Récupère un module par son nom"""
    return get_registry().get(name, config)
