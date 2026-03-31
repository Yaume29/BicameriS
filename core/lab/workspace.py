"""
Workspace - Alias for backward compatibility
=========================================
This module is now integrated into lab_engine.py
"""

from .lab_engine import Workspace as _Workspace, get_workspace as _get_workspace

# Re-export for compatibility
Workspace = _Workspace


def get_workspace(workspace_id: str = None):
    """Get workspace from lab engine"""
    return _get_workspace(workspace_id)


__all__ = ["Workspace", "get_workspace"]
