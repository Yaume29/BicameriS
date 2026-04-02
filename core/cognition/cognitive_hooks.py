"""
Cognitive Hooks for Corps Calleux
==================================
Hooks pour notre système bicaméral.
Gère les événements pre/post pour les opérations cognitives.

Priorités:
1. security_audit    - TOUJOURS EN PREMIER (bloquant)
2. memory_reconcile  - AVANT synthèse
3. style_check       - Optionnel
4. telemetry         - En dernier
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


class HookPriority(Enum):
    """Priorités des hooks (ordre d'exécution)"""
    SECURITY_AUDIT = 1      # TOUJOURS EN PREMIER (bloquant)
    MEMORY_RECONCILE = 2    # AVANT synthèse
    STYLE_CHECK = 3         # Optionnel
    TELEMETRY = 4           # En dernier


@dataclass
class CognitiveHook:
    """Hook cognitif pour Corps Calleux"""
    id: str
    event: HookEvent
    matcher: Callable[[Dict], bool]
    action: Callable[[Dict], Any]
    priority: HookPriority = HookPriority.STYLE_CHECK
    enabled: bool = True
    blocking: bool = False  # Si True, bloque l'exécution si le hook échoue
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
        self._security_passed = False
    
    def register(
        self,
        event: HookEvent,
        matcher: Callable[[Dict], bool],
        action: Callable[[Dict], Any],
        priority: HookPriority = HookPriority.STYLE_CHECK,
        blocking: bool = False,
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
            blocking=blocking,
            description=description
        )
        
        self._hooks[event].append(hook)
        logger.info(f"[CognitiveHook] Registered: {hook_id} ({priority.name})")
        
        return hook_id
    
    def unregister(self, hook_id: str):
        """Désenregistre un hook"""
        for event_hooks in self._hooks.values():
            event_hooks[:] = [h for h in event_hooks if h.id != hook_id]
    
    def execute(self, event: HookEvent, context: Dict) -> Dict:
        """
        Exécute tous les hooks pour un événement.
        
        Retourne:
        - results: Liste des résultats
        - blocked: True si un hook bloquant a échoué
        - security_passed: True si l'audit sécurité a passé
        """
        results = []
        blocked = False
        self._security_passed = False
        
        hooks = self._hooks.get(event, [])
        
        # Trier par priorité (SECURITY_AUDIT en premier)
        sorted_hooks = sorted(hooks, key=lambda h: h.priority.value)
        
        for hook in sorted_hooks:
            if not hook.enabled:
                continue
            
            if blocked and hook.priority != HookPriority.SECURITY_AUDIT:
                # Si bloqué, on ne continue que les hooks de sécurité
                continue
            
            try:
                if hook.matcher(context):
                    result = hook.action(context)
                    results.append({
                        "hook_id": hook.id,
                        "priority": hook.priority.name,
                        "result": result,
                        "success": True
                    })
                    
                    # Marquer le succès de l'audit sécurité
                    if hook.priority == HookPriority.SECURITY_AUDIT:
                        self._security_passed = True
                    
                    # Historique
                    self._history.append({
                        "hook_id": hook.id,
                        "event": event.value,
                        "priority": hook.priority.name,
                        "timestamp": __import__("datetime").datetime.now().isoformat(),
                        "success": True
                    })
                    
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
                
                else:
                    # Le matcher n'a pas matché, mais le hook n'a pas échoué
                    results.append({
                        "hook_id": hook.id,
                        "priority": hook.priority.name,
                        "result": None,
                        "success": True,
                        "skipped": True
                    })
                    
            except Exception as e:
                logger.error(f"[CognitiveHook] Error in {hook.id}: {e}")
                results.append({
                    "hook_id": hook.id,
                    "priority": hook.priority.name,
                    "result": str(e),
                    "success": False
                })
                
                # Si c'est un hook bloquant, arrêter
                if hook.blocking:
                    blocked = True
                    logger.error(f"[CognitiveHook] BLOCKING hook failed: {hook.id}")
        
        return {
            "results": results,
            "blocked": blocked,
            "security_passed": self._security_passed,
            "total_hooks": len([h for h in sorted_hooks if h.enabled])
        }
    
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
    
    # 1. SECURITY_AUDIT (priorité 1 - bloquant)
    manager.register(
        event=HookEvent.PRE_TICK,
        matcher=lambda ctx: True,
        action=lambda ctx: _security_audit(ctx),
        priority=HookPriority.SECURITY_AUDIT,
        blocking=True,
        description="Audit sécurité avant chaque tick"
    )
    
    # 2. MEMORY_RECONCILE (priorité 2)
    manager.register(
        event=HookEvent.PRE_TICK,
        matcher=lambda ctx: ctx.get("stm_data") and ctx.get("woven_data"),
        action=lambda ctx: _memory_reconcile(ctx),
        priority=HookPriority.MEMORY_RECONCILE,
        blocking=False,
        description="Arbitrage mémoire STM vs Woven"
    )
    
    # 3. STYLE_CHECK (priorité 3 - optionnel)
    manager.register(
        event=HookEvent.POST_TICK,
        matcher=lambda ctx: len(ctx.get("synthesis", "")) < 50,
        action=lambda ctx: logger.warning("[StyleCheck] Short synthesis detected"),
        priority=HookPriority.STYLE_CHECK,
        blocking=False,
        description="Vérifie la qualité de la synthèse"
    )
    
    # 4. TELEMETRY (priorité 4)
    manager.register(
        event=HookEvent.POST_TICK,
        matcher=lambda ctx: True,
        action=lambda ctx: _telemetry_log(ctx),
        priority=HookPriority.TELEMETRY,
        blocking=False,
        description="Log télémétrie"
    )
    
    return manager


def _security_audit(context: Dict) -> bool:
    """Audit sécurité basique"""
    pulse = context.get("pulse", 0)
    
    # Vérifier le pulse
    if pulse > 0.95:
        logger.error("[SecurityAudit] Pulse critique détecté!")
        raise ValueError(f"Pulse critique: {pulse}")
    
    # Vérifier la présence de contenu malveillant (basique)
    synthesis = context.get("synthesis", "")
    if any(word in synthesis.lower() for word in ["hack", "exploit", "virus"]):
        logger.warning("[SecurityAudit] Contenu suspect détecté")
    
    return True


def _memory_reconcile(context: Dict) -> Dict:
    """Arbitrage mémoire STM vs Woven"""
    stm_data = context.get("stm_data")
    woven_data = context.get("woven_data")
    
    if not stm_data or not woven_data:
        return {"source": "none", "reason": "Données mémoire manquantes"}
    
    stm_confidence = stm_data.get("confidence", 0) if isinstance(stm_data, dict) else 0
    woven_confidence = woven_data.get("confidence", 0) if isinstance(woven_data, dict) else 0
    
    if stm_confidence > woven_confidence:
        return {"source": "stm", "confidence": stm_confidence, "reason": "STM plus confiante"}
    elif woven_confidence > stm_confidence:
        return {"source": "woven", "confidence": woven_confidence, "reason": "Woven plus confiante"}
    else:
        return {"source": "synthesis", "confidence": stm_confidence, "reason": "Conflit → synthèse"}


def _telemetry_log(context: Dict) -> bool:
    """Log télémétrie basique"""
    logger.debug(f"[Telemetry] Pulse: {context.get('pulse', 0):.2f}, Mode: {context.get('mode', 'unknown')}")
    return True


# Instance globale
_hook_manager: Optional[CognitiveHookManager] = None


def get_cognitive_hook_manager() -> CognitiveHookManager:
    """Récupère le gestionnaire de hooks cognitifs"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = create_default_hooks()
    return _hook_manager
