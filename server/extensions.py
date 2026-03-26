"""
Server Extensions - Registry
===========================
Links server to core modules with proper typing
"""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING


@dataclass
class Registry:
    """Global registry for core dependencies"""

    thermal: Optional[object] = None
    entropy: Optional[object] = None
    modelscanner: Optional[object] = None
    conductor: Optional[object] = None
    corps_calleux: Optional[object] = None
    autonomous_thinker: Optional[object] = None
    inference_manager: Optional[type] = None
    flux_logger: Optional[object] = None
    supervisor: Optional[object] = None
    switchboard: Optional[object] = None
    scheduler: Optional[object] = None


# Global instance
registry = Registry()


def get_registry() -> Registry:
    """Get the global registry"""
    return registry


def get_switchboard():
    if not registry.switchboard:
        from core.system.switchboard import get_switchboard

        registry.switchboard = get_switchboard()
    return registry.switchboard


def get_corps_calleux():
    if not registry.corps_calleux:
        from core.cognition.corps_calleux import CorpsCalleux

        registry.corps_calleux = CorpsCalleux()
    return registry.corps_calleux


def get_autonomous_thinker():
    if not registry.autonomous_thinker:
        from core.cognition.autonomous_thinker import AutonomousThinker

        registry.autonomous_thinker = AutonomousThinker()
    return registry.autonomous_thinker
