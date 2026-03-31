"""
Lab Modules
===========
Modules auto-détectables pour le laboratoire.

Pour créer un nouveau module:
1. Créer un dossier dans core/lab/modules/ nommé: X_NomModule
   - X = chiffre pour l'ordre d'affichage (ex: 1_Inception)
2. Créer un fichier __init__.py qui expose votre classe
3. Hériter de LabModule (core.lab.modules.base)

Exemple:
   from .base import LabModule
   
   class MonModule(LabModule):
       id = "mon-module"
       name = "Mon Module"
       icon = "🔧"
       description = "Description"
       order = 5
       
       def render(self):
           return "<div>Mon module</div>"
"""

from .base import LabModule
from ..registry import get_registry, list_lab_modules, get_lab_module

__all__ = [
    "LabModule",
    "get_registry",
    "list_lab_modules",
    "get_lab_module"
]
