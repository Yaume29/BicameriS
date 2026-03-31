"""
Laboratoire - Technical Chat Module
===================================
Système de modules auto-détectables.

Modules disponibles:
- Inception: Injection de pensées
- Éditeur Spécialiste: Chat technique avec thèmes
- Induction: Induction contextuelle
- Autonome: Pensée inter-hémisphérique
"""

from .lab_engine import LabEngine, get_lab_engine
from .workspace import Workspace, get_workspace
from .specialist import Specialist, get_specialist
from .modules import LabModule, get_registry, list_lab_modules, get_lab_module

__all__ = [
    "LabEngine",
    "get_lab_engine",
    "Workspace",
    "get_workspace",
    "Specialist",
    "get_specialist",
    "LabModule",
    "get_registry",
    "list_lab_modules",
    "get_lab_module"
]
