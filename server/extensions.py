"""
Server Extensions - Registry
===========================
Links server to core modules with proper typing
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Registry:
    """Global registry for core dependencies"""

    thermal: Optional[object] = None
    entropy: Optional[object] = None
    modelscanner: Optional[object] = None
    conductor: Optional[object] = None
    corps_calleux: Optional[object] = None
    inference_manager: Optional[type] = None
    flux_logger: Optional[object] = None
    supervisor: Optional[object] = None
    switchboard: Optional[object] = None
    scheduler: Optional[object] = None
    left_hemisphere: Optional[object] = None
    right_hemisphere: Optional[object] = None


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
        
        # Try to connect hemispheres if loaded
        try:
            from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
            left = get_left_hemisphere()
            right = get_right_hemisphere()
            if left and right:
                registry.corps_calleux.set_hemispheres(left, right)
        except:
            pass
            
    return registry.corps_calleux
