"""
Cognitive Hooks for Corps Calleux
==================================
Hooks pour notre système bicaméral.
Gère les événements pre/post pour les opérations cognitives.
"""

import logging
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("cognitive_hooks")


class HookEvent(Enum):
    """Événements cognitifs déclenchant des hooks"""
    PRE_TICK = "pre_tick"
    POST_TICK = "post_tick"
    PRE_DIALOGUE = "pre_dialogue"
    POST_DIALOGUE = "post_dialogue"
    MODE_CHANGE = "mode_change"
    PULSE_CHANGE = "pulse_change"
    RESEARCH_TRIGGER = "research_trigger"
    SPAWN_AGENTS = "spawn_agents"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"


@dataclass
class CognitiveHook:
    """Hook cognitif pour Corps Calleux"""
    id: str
    event: HookEvent
    matcher: Callable[[Dict], bool]
    action: Callable[[Dict], Any]
    priority: str = "standard"  # minimal, standard, strict
    enabled: bool = True
    description: str = ""


class CognitiveHookManager:
    """
    Gestionnaire de hooks cognitifs pour Corps Calleux.
    Intègre les patterns avec notre système bicaméral.
    """
    
    def __init__(self):
        self._hooks: Dict[HookEvent, List[CognitiveHook]] = {
            event: [] for event in HookEvent
        }
        self._history: List[Dict] = []
        self._max_history = 100
    
    def register(
        self,
        event: HookEvent,
        matcher: Callable[[Dict], bool],
        action: Callable[[Dict], Any],
        priority: str = "standard",
        description: str = ""
    ) -> str:
        """Enregistre un hook cognitif"""
        hook_id = f"hook_{event.value}_{len(self._hooks[event])}"
        
        hook = CognitiveHook(
            id=hook_id,
            event=event,
            matcher=matcher,
            action=action,
            priority=priority,
            enabled=True,
            description=description
        )
        
        self._hooks[event].append(hook)
        logger.info(f"[CognitiveHook] Registered: {hook_id} for {event.value}")
        
        return hook_id
    
    def unregister(self, hook_id: str):
        """Désenregistre un hook"""
        for event_hooks in self._hooks.values():
            event_hooks[:] = [h for h in event_hooks if h.id != hook_id]
    
    def execute(self, event: HookEvent, context: Dict) -> List[Any]:
        """Exécute tous les hooks pour un événement"""
        results = []
        
        hooks = self._hooks.get(event, [])
        
        # Trier par priorité
        priority_order = {"strict": 0, "standard": 1, "minimal": 2}
        sorted_hooks = sorted(hooks, key=lambda h: priority_order.get(h.priority, 1))
        
        for hook in sorted_hooks:
            if not hook.enabled:
                continue
            
            try:
                if hook.matcher(context):
                    result = hook.action(context)
                    results.append(result)
                    
                    # Historique
                    self._history.append({
                        "hook_id": hook.id,
                        "event": event.value,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                        "context_keys": list(context.keys()),
                        "result_type": type(result).__name__
                    })
                    
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
                    
            except Exception as e:
                logger.error(f"[CognitiveHook] Error in {hook.id}: {e}")
        
        return results
    
    def get_history(self) -> List[Dict]:
        """Récupère l'historique des hooks exécutés"""
        return self._history.copy()
    
    def enable_hook(self, hook_id: str):
        """Active un hook"""
        for event_hooks in self._hooks.values():
            for hook in event_hooks:
                if hook.id == hook_id:
                    hook.enabled = True
    
    def disable_hook(self, hook_id: str):
        """Désactive un hook"""
        for event_hooks in self._hooks.values():
            for hook in event_hooks:
                if hook.id == hook_id:
                    hook.enabled = False


# Hooks prédéfinis pour Corps Calleux

def create_default_hooks() -> CognitiveHookManager:
    """Crée les hooks par défaut pour Corps Calleux"""
    manager = CognitiveHookManager()
    
    # Pre-tick: Vérifie l'état des hémisphères
    manager.register(
        event=HookEvent.PRE_TICK,
        matcher=lambda ctx: True,
        action=lambda ctx: logger.debug(f"[PreTick] Pulse: {ctx.get('pulse', 0):.2f}"),
        priority="minimal",
        description="Log pre-tick state"
    )
    
    # Post-tick: Analyse la qualité de la synthèse
    manager.register(
        event=HookEvent.POST_TICK,
        matcher=lambda ctx: len(ctx.get("synthesis", "")) < 50,
        action=lambda ctx: logger.warning("[PostTick] Short synthesis detected"),
        priority="standard",
        description="Warn on short synthesis"
    )
    
    # Mode change: Sauvegarde l'état
    manager.register(
        event=HookEvent.MODE_CHANGE,
        matcher=lambda ctx: True,
        action=lambda ctx: logger.info(f"[ModeChange] {ctx.get('old_mode')} -> {ctx.get('new_mode')}"),
        priority="standard",
        description="Log mode changes"
    )
    
    # Pulse extreme: Change de mode
    manager.register(
        event=HookEvent.PULSE_CHANGE,
        matcher=lambda ctx: ctx.get("pulse", 0) > 0.8,
        action=lambda ctx: logger.warning(f"[PulseExtreme] High pulse: {ctx.get('pulse', 0):.2f}"),
        priority="strict",
        description="Handle extreme pulse"
    )
    
    return manager


# Instance globale
_hook_manager: Optional[CognitiveHookManager] = None


def get_cognitive_hook_manager() -> CognitiveHookManager:
    """Récupère le gestionnaire de hooks cognitifs"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = create_default_hooks()
    return _hook_manager
