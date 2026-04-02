"""
Memory Sleep Manager
====================
Gère la mise en veille et le réveil de la mémoire autonome
quand on entre/sort de l'Éditeur Spécialiste.

Fonctionnement:
- Sleep: Sauvegarde le contexte, débranche la mémoire autonome
- Wake: Restaure le contexte, rebranche la mémoire autonome
"""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger("specialist.memory_sleep")


@dataclass
class MemorySnapshot:
    """Instantané de l'état mémoire"""
    timestamp: str
    autonomous_mode: str
    current_context: str
    thought_history: list
    memory_state: Dict
    hemisphere_settings: Dict
    auto_scaffolding: bool


class MemorySleepManager:
    """
    Gestionnaire de veille mémoire.
    
    Quand on entre dans l'Éditeur Spécialiste:
    1. Vérifier le contexte immédiat
    2. Sauvegarder l'état dans Woven Memory
    3. Débrancher la mémoire autonome
    4. Activer le mode "outil"
    
    Quand on sort de l'Éditeur Spécialiste:
    1. Restaurer le contexte sauvegardé
    2. Rebrancher la mémoire autonome
    3. Désactiver le mode "outil"
    """
    
    def __init__(self):
        self._snapshot: Optional[MemorySnapshot] = None
        self._is_sleeping = False
        self._sleep_count = 0
        
        base_dir = Path(__file__).parent.parent.parent.parent
        self._storage_dir = base_dir / "storage" / "memory_snapshots"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    def sleep(self, corps_calleux=None) -> Dict:
        """
        Met en veille la mémoire autonome.
        
        Returns:
            Dict avec status et informations de sauvegarde
        """
        if self._is_sleeping:
            return {"status": "already_sleeping", "message": "Mémoire déjà en veille"}
        
        try:
            snapshot = self._create_snapshot(corps_calleux)
            self._save_snapshot(snapshot)
            
            self._is_sleeping = True
            self._sleep_count += 1
            
            logger.info(f"[MemorySleep] Sleep #{self._sleep_count} - Context saved")
            
            return {
                "status": "sleeping",
                "snapshot_id": snapshot.timestamp,
                "mode_before_sleep": snapshot.autonomous_mode,
                "thoughts_saved": len(snapshot.thought_history),
                "message": f"Mémoire mise en veille. Contexte sauvegardé."
            }
            
        except Exception as e:
            logger.error(f"[MemorySleep] Sleep failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def wake(self, corps_calleux=None) -> Dict:
        """
        Réveille la mémoire autonome.
        
        Returns:
            Dict avec status et informations de restauration
        """
        if not self._is_sleeping:
            return {"status": "already_awake", "message": "Mémoire déjà active"}
        
        try:
            snapshot = self._load_latest_snapshot()
            
            if snapshot:
                self._restore_context(snapshot, corps_calleux)
                logger.info(f"[MemorySleep] Wake - Context restored from {snapshot.timestamp}")
            
            self._is_sleeping = False
            
            return {
                "status": "awake",
                "snapshot_restored": snapshot is not None,
                "mode_restored": snapshot.autonomous_mode if snapshot else None,
                "message": f"Mémoire réveillée. Contexte {'restauré' if snapshot else 'perdu'}."
            }
            
        except Exception as e:
            logger.error(f"[MemorySleep] Wake failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_snapshot(self, corps_calleux=None) -> MemorySnapshot:
        """Crée un instantané de l'état actuel"""
        autonomous_mode = "metacognition"
        current_context = ""
        thought_history = []
        memory_state = {}
        hemisphere_settings = {}
        auto_scaffolding = False
        
        if corps_calleux:
            autonomous_mode = getattr(corps_calleux, 'autonomous_mode', 'metacognition')
            thought_history = getattr(corps_calleux, '_thought_history', [])
            auto_scaffolding = getattr(corps_calleux, 'auto_scaffolding_enabled', False)
            
            if hasattr(corps_calleux, 'left') and corps_calleux.left:
                hemisphere_settings['left'] = {
                    'temperature': getattr(corps_calleux.left, 'temperature', 0.7),
                    'top_p': getattr(corps_calleux.left, 'top_p', 0.9)
                }
            
            if hasattr(corps_calleux, 'right') and corps_calleux.right:
                hemisphere_settings['right'] = {
                    'temperature': getattr(corps_calleux.right, 'temperature', 0.7),
                    'top_p': getattr(corps_calleux.right, 'top_p', 0.9)
                }
        
        return MemorySnapshot(
            timestamp=datetime.now().isoformat(),
            autonomous_mode=autonomous_mode,
            current_context=current_context,
            thought_history=thought_history[-10:] if thought_history else [],
            memory_state=memory_state,
            hemisphere_settings=hemisphere_settings,
            auto_scaffolding=auto_scaffolding
        )
    
    def _save_snapshot(self, snapshot: MemorySnapshot):
        """Sauvegarde l'instantané sur disque"""
        filename = f"snapshot_{snapshot.timestamp.replace(':', '-')}.json"
        filepath = self._storage_dir / filename
        
        data = {
            "timestamp": snapshot.timestamp,
            "autonomous_mode": snapshot.autonomous_mode,
            "current_context": snapshot.current_context,
            "thought_history": snapshot.thought_history,
            "memory_state": snapshot.memory_state,
            "hemisphere_settings": snapshot.hemisphere_settings,
            "auto_scaffolding": snapshot.auto_scaffolding
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self._snapshot = snapshot
    
    def _load_latest_snapshot(self) -> Optional[MemorySnapshot]:
        """Charge le dernier instantané sauvegardé"""
        try:
            snapshots = list(self._storage_dir.glob("snapshot_*.json"))
            
            if not snapshots:
                return None
            
            latest = max(snapshots, key=lambda p: p.stat().st_mtime)
            
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return MemorySnapshot(**data)
            
        except Exception as e:
            logger.error(f"[MemorySleep] Failed to load snapshot: {e}")
            return None
    
    def _restore_context(self, snapshot: MemorySnapshot, corps_calleux=None):
        """Restaure le contexte sauvegardé"""
        if not corps_calleux:
            return
        
        if hasattr(corps_calleux, 'autonomous_mode'):
            corps_calleux.autonomous_mode = snapshot.autonomous_mode
        
        if hasattr(corps_calleux, 'auto_scaffolding_enabled'):
            corps_calleux.auto_scaffolding_enabled = snapshot.auto_scaffolding
        
        if hasattr(corps_calleux, '_thought_history'):
            corps_calleux._thought_history = snapshot.thought_history
        
        if 'left' in snapshot.hemisphere_settings and hasattr(corps_calleux, 'left'):
            if corps_calleux.left:
                settings = snapshot.hemisphere_settings['left']
                if 'temperature' in settings:
                    corps_calleux.left.temperature = settings['temperature']
                if 'top_p' in settings:
                    corps_calleux.left.top_p = settings['top_p']
        
        if 'right' in snapshot.hemisphere_settings and hasattr(corps_calleux, 'right'):
            if corps_calleux.right:
                settings = snapshot.hemisphere_settings['right']
                if 'temperature' in settings:
                    corps_calleux.right.temperature = settings['temperature']
                if 'top_p' in settings:
                    corps_calleux.right.top_p = settings['top_p']
    
    def is_sleeping(self) -> bool:
        """Vérifie si la mémoire est en veille"""
        return self._is_sleeping
    
    def get_sleep_status(self) -> Dict:
        """Retourne le statut de veille"""
        return {
            "is_sleeping": self._is_sleeping,
            "sleep_count": self._sleep_count,
            "last_snapshot": self._snapshot.timestamp if self._snapshot else None
        }


# Instance globale
_memory_sleep_manager: Optional[MemorySleepManager] = None


def get_memory_sleep_manager() -> MemorySleepManager:
    """Récupère le gestionnaire de veille mémoire"""
    global _memory_sleep_manager
    if _memory_sleep_manager is None:
        _memory_sleep_manager = MemorySleepManager()
    return _memory_sleep_manager
