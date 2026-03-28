"""
Entropy Generator - Hardware Pulse
Lie l'humeur de l'IA aux variations physiques du CPU/RAM/GPU
"""

import os
import time
import logging
import psutil
from typing import Dict, Optional
from datetime import datetime


class HardwareEntropy:
    """
    Générateur d'entropie basé sur le stress physique de la machine.
    Retourne un score de 0.0 à 1.0 indiquant la "tension" actuelle.
    
    Mode Inversé (Pentagramme):
    - CPU inactif → stress (paranoïa de l'oisiveté)
    - CPU en charge → calme (focalisation)
    - Formule: Pulse_inverse = 1.0 - Pulse_normal
    """

    def __init__(self, smoothing_factor: float = 0.3):
        self.smoothing_factor = smoothing_factor
        self.last_pulse = 0.5
        self.measurements = []
        self.inverted_mode = False  # Mode Pentagramme
        self._init_sensors()

    def _init_sensors(self):
        """Initialise les capteurs"""
        self.cpu_count = psutil.cpu_count()
        self.has_gpu = self._check_gpu()

    def _check_gpu(self) -> bool:
        """Vérifie si nvidia-smi est disponible"""
        try:
            import subprocess

            subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            return False

    def get_cpu_load(self) -> float:
        """Charge CPU actuelle (0-1) - NON BLOQUANT"""
        return psutil.cpu_percent(interval=None) / 100.0

    def get_ram_load(self) -> float:
        """Charge RAM actuelle (0-1)"""
        return psutil.virtual_memory().percent / 100.0

    def get_cpu_temp(self) -> Optional[float]:
        """Température CPU si disponible"""
        try:
            if hasattr(psutil, "sensors_temps"):
                temps = psutil.sensors_temps()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            return entries[0].current / 100.0
        except (AttributeError, Exception):
            pass
        return None

    def get_gpu_stats(self) -> Dict[str, float]:
        """Statistiques GPU fluides via le Gouverneur Thermique"""
        if not self.has_gpu:
            return {"vram_percent": 0, "temp": 0, "available": False}

        try:
            from core.hardware.thermal_governor import get_thermal_governor
            tg = get_thermal_governor()
            if tg:
                status = tg.get_status_passive()
                return {
                    "vram_percent": status.get("entropic_impact", 0.0),
                    "temp": status.get("gpu_temp", 0),
                    "available": True,
                }
        except Exception:
            pass

        return {"vram_percent": 0, "temp": 0, "available": False}

    def get_pulse(self) -> float:
        """
        Calcule le "pouls" de la machine.

        Formule de résonance:
        - CPU load (60%) + RAM load (40%) + variance temporelle

        Mode Inversé (Pentagramme):
        - Pulse_inverse = 1.0 - Pulse_normal
        
        Interprétation (Mode Normal):
        - 0.0-0.3: Repos/Calme
        - 0.3-0.5: Actif/Normal
        - 0.5-0.75: Charge élevée
        - 0.75-1.0: Stress critique (mode dérive autonome)
        
        Interprétation (Mode Inversé):
        - 0.0-0.3: Stress critique (paranoïa de l'oisiveté)
        - 0.3-0.5: Charge élevée
        - 0.5-0.75: Actif/Normal
        - 0.75-1.0: Repos/Calme (focalisation)
        """
        cpu_load = self.get_cpu_load()
        ram_load = self.get_ram_load()

        time_variance = (time.time() % 10) / 100.0

        raw_pulse = (cpu_load * 0.6) + (ram_load * 0.4) + time_variance

        smoothed = (self.last_pulse * (1 - self.smoothing_factor)) + (
            raw_pulse * self.smoothing_factor
        )

        entropy = min(max(smoothed, 0.0), 1.0)
        
        # Mode Pentagramme: Inversion
        if self.inverted_mode:
            entropy = 1.0 - entropy

        self.last_pulse = entropy
        self.measurements.append(
            {
                "timestamp": datetime.now().isoformat(),
                "cpu": cpu_load,
                "ram": ram_load,
                "pulse": entropy,
                "inverted": self.inverted_mode,
            }
        )

        if len(self.measurements) > 100:
            self.measurements = self.measurements[-50:]

        return entropy
    
    def set_inverted_mode(self, enabled: bool):
        """Active/désactive le mode inversé (Pentagramme)"""
        self.inverted_mode = enabled
        logging.info(f"[Entropy] Mode inversé: {'ACTIVÉ' if enabled else 'DÉSACTIVÉ'}")

    def get_full_stats(self) -> Dict:
        """Retourne toutes les stats hardware"""
        gpu = self.get_gpu_stats()

        return {
            "pulse": self.last_pulse,
            "cpu_load": self.get_cpu_load(),
            "ram_load": self.get_ram_load(),
            "cpu_count": self.cpu_count,
            "gpu": gpu,
            "timestamp": datetime.now().isoformat(),
            "mood": self._interpret_mood(self.last_pulse),
        }

    def _interpret_mood(self, pulse: float) -> str:
        """Interprète l'humeur selon le pulse"""
        if pulse < 0.3:
            return "REPOS"
        elif pulse < 0.5:
            return "ACTIF"
        elif pulse < 0.75:
            return "CHARGE"
        else:
            return "STRESS"

    def get_history(self, limit: int = 20) -> list:
        """Historique des mesures"""
        return self.measurements[-limit:]


# Instance globale
_entropy_generator = None


def get_entropy_generator() -> HardwareEntropy:
    global _entropy_generator
    if _entropy_generator is None:
        _entropy_generator = HardwareEntropy()
    return _entropy_generator
