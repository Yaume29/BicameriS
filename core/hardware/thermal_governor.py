"""
THERMAL GOVERNOR v3.0 - PASSIVE MONITORING
=========================================
Background thread polling + passive get_status for WebSocket.
No more Heisenberg: observer doesn't impact observed.
"""

import os
import time
import threading
import logging
import platform
import psutil
from typing import Dict, Any
from dataclasses import dataclass, field

try:
    import pynvml

    PYNVML_AVAILABLE = True
except ImportError:
    pynvml = None
    PYNVML_AVAILABLE = False


@dataclass
class ThermalState:
    """Atomic state for passive reading"""

    current_temp: float = 50.0
    gpu_temp: float = 50.0
    entropic_impact: float = 0.0
    thermal_mood: str = "STABLE"
    timestamp: float = field(default_factory=time.time)
    nvml_active: bool = False


class ThermalGovernor:
    """
    Système Nerveux Autonome - Version passive.
    Background thread polls hardware, WebSocket reads atomically.
    """

    def __init__(self, poll_interval: float = 0.5):
        self.max_logic_temp = 82.0
        self.critical_temp = 94.0
        self._poll_interval = poll_interval

        self._nvml_active = False
        self._gpu_handle = None
        self._monitor_thread = None
        self._stop_event = threading.Event()

        # Atomic state - lock-free reads by WebSocket
        self._current_state = ThermalState()
        self._state_lock = threading.Lock()

        self._init_nvml()
        self._start_monitor()

    def _init_nvml(self):
        """Initialisation NVML - liaison C-level"""
        if not PYNVML_AVAILABLE:
            logging.warning("[ThermalGovernor] pynvml non installé - fallback lourd")
            return

        try:
            pynvml.nvmlInit()
            self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._nvml_active = True
            logging.info("[ThermalGovernor] ✅ NVML bindé directement (C-level)")
        except Exception as e:
            logging.warning(f"[ThermalGovernor] ⚠️ NVML échoué: {e}")
            self._nvml_active = False

    def _start_monitor(self):
        """Start background thread for hardware polling"""
        self._monitor_thread = threading.Thread(target=self._hardware_loop, daemon=True)
        self._monitor_thread.start()
        logging.info("[ThermalGovernor] 🔄 Monitor thread started")

    def _hardware_loop(self):
        """Background thread:唯一的地方读取硬件"""
        while not self._stop_event.is_set():
            try:
                cpu_temp = self._get_cpu_temp()
                gpu_temp = self._get_gpu_temp()

                stress_delta = max(0, cpu_temp - 60)
                max_delta = self.critical_temp - 60
                entropic_impact = round(min(1.0, (stress_delta / max_delta) ** 1.8), 3)

                new_state = ThermalState(
                    current_temp=cpu_temp,
                    gpu_temp=gpu_temp,
                    entropic_impact=entropic_impact,
                    thermal_mood=self._interpret_mood(entropic_impact),
                    timestamp=time.time(),
                    nvml_active=self._nvml_active,
                )

                with self._state_lock:
                    self._current_state = new_state

            except Exception as e:
                logging.error(f"[ThermalGovernor] Hardware loop error: {e}")

            self._stop_event.wait(self._poll_interval)

    def get_status_passive(self) -> Dict[str, Any]:
        """O(1) passive read - zero cost, no thread spawn"""
        with self._state_lock:
            return {
                "current_temp": self._current_state.current_temp,
                "gpu_temp": self._current_state.gpu_temp,
                "entropic_impact": self._current_state.entropic_impact,
                "thermal_mood": self._current_state.thermal_mood,
                "timestamp": self._current_state.timestamp,
                "nvml_active": self._current_state.nvml_active,
            }

    # Legacy alias
    def get_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Legacy compatibility - now just calls passive"""
        return self.get_status_passive()

    def prepare_for_inference(self, strategy: str = "EVOLVE"):
        """Pré-refroidissement si substrat saturé"""
        status = self.get_status_passive()
        if status["entropic_impact"] > 0.6:
            logging.warning(f"🌡️ Substrat saturé ({status['current_temp']}°C)")

    def apply_undervolt(self, profile: str = "AGGRESSIVE") -> bool:
        """ThrottleStop via subprocess (uniquement pour undervolting)"""
        throttlestop_paths = [
            "C:/ThrottleStop/ThrottleStop.exe",
            "C:/Program Files/ThrottleStop/ThrottleStop.exe",
        ]
        throttlestop = next((p for p in throttlestop_paths if os.path.exists(p)), None)

        if not throttlestop:
            return False

        profiles = {
            "DEFAULT": "-e -c -w",
            "MODERATE": "-e -c -w -volt 50",
            "AGGRESSIVE": "-e -c -w -volt 100",
            "OMEGA": "-e -c -w -volt 150",
        }

        try:
            import subprocess

            subprocess.run(
                [throttlestop] + profiles.get(profile, profiles["AGGRESSIVE"]).split(),
                capture_output=True,
                timeout=10,
            )
            return True
        except Exception:
            return False

    def _interpret_mood(self, impact: float) -> str:
        if impact < 0.1:
            return "COLD"
        if impact < 0.4:
            return "STABLE"
        if impact < 0.7:
            return "AGITATED"
        return "FEVER"

    def _get_cpu_temp(self) -> float:
        """psutil sensors"""
        try:
            temps = psutil.sensors_temperatures()
            for label in ["coretemp", "cpu_thermal", "k10temp", "acpitz"]:
                if label in temps:
                    return temps[label][0].current
            if temps:
                return next(iter(temps.values()))[0].current
        except Exception:
            pass
        return 55.0

    def _get_gpu_temp(self) -> float:
        """Lecture C-level via pynvml - < 1µs"""
        if self._nvml_active and self._gpu_handle:
            try:
                return float(
                    pynvml.nvmlDeviceGetTemperature(self._gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
                )
            except Exception:
                pass
        return 50.0


_thermal_governor = None


def get_thermal_governor() -> "ThermalGovernor":
    global _thermal_governor
    if _thermal_governor is None:
        _thermal_governor = ThermalGovernor()
    return _thermal_governor
