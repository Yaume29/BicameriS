"""
Diadikos & Palladion - Système Endocrinien Synthétique
==========================================
Gère les états d'urgence, de récompense et d'humeur avec décroissance temporelle (decay).
Transmute la chimie virtuelle en hyperparamètres LLM.
"""

import time
import threading
import logging
from typing import Dict

logger = logging.getLogger(__name__)


class EndocrineSystem:
    """
    Hormone virtuali con decay temporale.
    Modulate les paramètres LLM en temps réel.
    """

    def __init__(self):
        self._lock = threading.Lock()

        self.adrenaline = 0.0
        self.dopamine = 0.0
        self.serotonin = 0.5

        self.last_update = time.time()
        logger.info("[Endocrine] 🧬 Glandes virtuelles synthétisées.")

    def decay(self):
        """
        Appelé par le KernelScheduler à chaque tick().
        Simule la demi-vie temporelle des hormones.
        """
        with self._lock:
            now = time.time()
            dt = now - self.last_update
            self.last_update = now

            self.adrenaline = max(0.0, self.adrenaline - (0.02 * dt))
            self.dopamine = max(0.0, self.dopamine - (0.005 * dt))

            if self.serotonin > 0.5:
                self.serotonin = max(0.5, self.serotonin - (0.001 * dt))
            elif self.serotonin < 0.5:
                self.serotonin = min(0.5, self.serotonin + (0.001 * dt))

    def spike_adrenaline(self, amount: float = 0.4):
        """Appelé en cas d'erreur de la sandbox ou de détection de Trauma."""
        with self._lock:
            self.adrenaline = min(1.0, self.adrenaline + amount)
            self.serotonin = max(0.0, self.serotonin - (amount * 0.5))
            logger.warning(f"[Endocrine] ⚡ Choc Adrénaline ({self.adrenaline:.2f})")

    def spike_dopamine(self, amount: float = 0.3):
        """Appelé en cas de succès d'une forge d'outil ou d'une tâche résolue."""
        with self._lock:
            self.dopamine = min(1.0, self.dopamine + amount)
            self.serotonin = min(1.0, self.serotonin + (amount * 0.2))
            logger.info(f"[Endocrine] 💊 Fix Dopamine ({self.dopamine:.2f})")

    def modulate_llm_params(
        self, base_temp: float = 0.7, base_top_p: float = 0.9
    ) -> Dict[str, float]:
        """
        Transmue la chimie du système en hyperparamètres pour Qwen ou Gemma.
        """
        with self._lock:
            temp = base_temp - (self.adrenaline * 0.5) + (self.dopamine * 0.3)

            top_p = base_top_p - (self.adrenaline * 0.3) + ((self.serotonin - 0.5) * 0.2)

            return {
                "temperature": max(0.01, min(1.5, temp)),
                "top_p": max(0.1, min(1.0, top_p)),
                "presence_penalty": self.dopamine * 0.8,
            }

    def get_status(self) -> Dict[str, float]:
        """Retourne l'état actuel des hormones"""
        with self._lock:
            return {
                "adrenaline": self.adrenaline,
                "dopamine": self.dopamine,
                "serotonin": self.serotonin,
            }


_endocrine = None


def get_endocrine_system() -> EndocrineSystem:
    global _endocrine
    if _endocrine is None:
        _endocrine = EndocrineSystem()
    return _endocrine


def modulate_parameters(base_params: dict, pulse: float) -> dict:
    """Module les paramètres LLM selon le pulse hardware (O(1))"""
    from core.system.switchboard import get_switchboard

    sb = get_switchboard()

    if not sb.hardware_influence_enabled:
        return base_params.copy()

    effective_pulse = pulse * sb.entropy_sensitivity
    temp_shift = (effective_pulse * 0.2) * sb.mood_impact_factor

    new_params = base_params.copy()
    new_params["temperature"] = max(0.1, min(1.5, new_params.get("temperature", 0.7) + temp_shift))
    new_params["top_p"] = max(0.1, min(1.0, new_params.get("top_p", 0.9) - (temp_shift * 0.5)))

    return new_params
