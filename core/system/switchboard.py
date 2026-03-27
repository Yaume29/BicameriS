"""
BICAMERIS - Switchboard
=======================
Thread-safe state manager for laboratory features.
Controls ON/OFF states for autonomous loop, auto-forge, docker, debug, etc.
"""

import threading
import logging
from typing import Dict, Any, List
from contextlib import contextmanager


class Switchboard:
    """
    Gestionnaire d'état thread-safe pour les fonctionnalités du laboratoire.
    """

    CONFLICT_MAP = {
        "hyper_cognition_mode": {
            "disables": ["autonomous_loop"],
            "reason": "Le mode Crucible monopolise le GPU. La boucle autonome doit être désactivée.",
        },
        "strict_airgap_mode": {
            "disables": ["auto_forge_agents"],
            "reason": "Le mode Airgap coupe le réseau. L'auto-forge nécessite des téléchargements.",
        },
        "sandbox_docker": {
            "disables": [],
            "requires": [],
            "reason": "",
        },
        "hemisphere_split_mode": {
            "disables": [],
            "reason": "",
        },
    }

    def __init__(self):
        self._states: Dict[str, bool] = {
            "autonomous_loop": False,
            "auto_forge_agents": False,
            "sandbox_docker": True,
            "debug_telemetry": False,
            "thermal_throttling": True,
            "hemisphere_split_mode": False,
            "trauma_filter": True,
            "entropy_tracking": True,
            "strict_airgap_mode": False,
            "cognitive_dissonance": False,
            "hyper_cognition_mode": False,
            "auto_scaffolding": False,
        }
        self.neuroplasticity_rate = 0.5

        self.hardware_influence_enabled = True
        self.entropy_sensitivity = 0.5
        self.mood_impact_factor = 0.5

        self._lock = threading.Lock()
        self._listeners: List[callable] = []
        logging.info("[Switchboard] Matrice de commutation initialisée.")

    def set_endocrine_config(self, enabled: bool, sensitivity: float, impact: float):
        """Verrouille les valeurs dans des bornes saines (0.0 à 1.0)"""
        self.hardware_influence_enabled = enabled
        self.entropy_sensitivity = max(0.0, min(1.0, sensitivity))
        self.mood_impact_factor = max(0.0, min(1.0, impact))

    def get_endocrine_config(self) -> Dict[str, float]:
        """Retourne la configuration endocrine"""
        return {
            "enabled": self.hardware_influence_enabled,
            "sensitivity": self.entropy_sensitivity,
            "impact": self.mood_impact_factor,
        }

    def toggle(self, feature: str, state: bool) -> Dict[str, Any]:
        """Bascule l'état d'une fonctionnalité avec détection de conflits."""
        callbacks_to_run = []
        conflicts = []

        with self._lock:
            if feature not in self._states:
                logging.warning(f"[Switchboard] Option inconnue: {feature}")
                return {"success": False, "error": f"Option '{feature}' inconnue"}

            if self._states[feature] == state:
                return {"success": True, "conflicts": []}

            if state and feature in self.CONFLICT_MAP:
                conflict_info = self.CONFLICT_MAP[feature]
                for disabled_feature in conflict_info.get("disables", []):
                    if self._states.get(disabled_feature, False):
                        conflicts.append({
                            "feature": disabled_feature,
                            "action": "disable",
                            "reason": conflict_info.get("reason", ""),
                        })

            self._states[feature] = state
            for conflict in conflicts:
                self._states[conflict["feature"]] = False

            logging.info(f"[Switchboard] 🎛️ {feature} -> {'ON' if state else 'OFF'}")
            callbacks_to_run = list(self._listeners)

        for listener in callbacks_to_run:
            try:
                listener(feature, state)
            except Exception as e:
                logging.warning(f"[Switchboard] Listener error: {e}")

        return {"success": True, "conflicts": conflicts}

    def check_conflicts(self, feature: str, state: bool) -> List[Dict]:
        """Vérifie les conflits potentiels sans appliquer les changements."""
        if not state or feature not in self.CONFLICT_MAP:
            return []

        conflicts = []
        conflict_info = self.CONFLICT_MAP[feature]
        for disabled_feature in conflict_info.get("disables", []):
            if self._states.get(disabled_feature, False):
                conflicts.append({
                    "feature": disabled_feature,
                    "action": "disable",
                    "reason": conflict_info.get("reason", ""),
                })
        return conflicts

    def is_active(self, feature: str) -> bool:
        """Vérifie l'état d'une fonctionnalité (Thread-Safe)."""
        with self._lock:
            return self._states.get(feature, False)

    def get_all_states(self) -> Dict[str, bool]:
        """Expose l'état complet pour le frontend."""
        with self._lock:
            return self._states.copy()

    def add_listener(self, callback: callable):
        """Ajoute un listener pour les changements d'état."""
        self._listeners.append(callback)

    def remove_listener(self, callback: callable):
        """Retire un listener."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    @contextmanager
    def override_states(self, overrides: Dict[str, bool]):
        """
        Sas de sécurité (Chambre Blanche).
        Force des états temporaires et les restaure infailliblement à la sortie.
        """
        previous_states = {}

        for feature, temp_state in overrides.items():
            with self._lock:
                if feature in self._states:
                    previous_states[feature] = self._states[feature]

            if feature in previous_states and previous_states[feature] != temp_state:
                self.toggle(feature, temp_state)

        logging.warning(f"[Switchboard] 🔒 LOCKDOWN ACTIVÉ : {overrides}")

        try:
            yield
        finally:
            logging.info(f"[Switchboard] 🔓 LOCKDOWN LEVÉ. Restauration des états.")
            for feature, old_state in previous_states.items():
                if self._states.get(feature) != old_state:
                    self.toggle(feature, old_state)


_switchboard = None


def get_switchboard() -> "Switchboard":
    global _switchboard
    if _switchboard is None:
        _switchboard = Switchboard()
    return _switchboard
