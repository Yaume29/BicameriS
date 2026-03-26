"""
BICAMERIS - Hardware Profiler
Scans hardware topology (CPU i9, RAM DDR5, VRAM RTX 4090) for the hybrid allocation.
"""

import os
import subprocess
import logging
import psutil

_hardware_config = {
    "n_gpu_layers": -1,
    "n_threads": 0,
    "os_vram_reserve": 2.0,
    "kv_cache_reserve": 1.5,
    "use_mmap": True,
    "use_mlock": False,
}


def set_hardware_config(config: dict):
    """Update hardware config from API"""
    global _hardware_config
    _hardware_config.update(config)


def get_hardware_config() -> dict:
    """Get current hardware config"""
    return _hardware_config.copy()


class HardwareProfiler:
    def __init__(self):
        self.cpu_cores = os.cpu_count() or 8
        self.ram_total_gb = self._get_system_ram()
        self.vram_total_gb = self._get_nvidia_vram()

        logging.info(
            f"[Profiler] CPU={self.cpu_cores} threads, RAM={self.ram_total_gb:.1f}Go, VRAM={self.vram_total_gb:.1f}Go"
        )

    def _get_system_ram(self) -> float:
        if psutil:
            return psutil.virtual_memory().total / (1024**3)
        return 16.0

    def _get_nvidia_vram(self) -> float:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,nounits,noheader"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return int(result.stdout.strip()) / 1024
        except Exception:
            logging.warning("[Profiler] GPU NVIDIA not found or nvidia-smi missing.")
            return 0.0

    def calculate_llama_config(self, model_size_b: float, is_concurrent: bool = False) -> dict:
        """
        Dynamic layer allocation algorithm for mmap.
        model_size_b : Model size in Billions of parameters (ex: 8.0).
        is_concurrent : True if launching Creuset Mode (Dissonance).
        """
        GB_PER_BILLION_PARAMS = 0.7
        MB_PER_LAYER = 160
        TOTAL_LAYERS = 32

        os_vram_reserve = _hardware_config.get("os_vram_reserve", 2.0)
        kv_cache_reserve = _hardware_config.get("kv_cache_reserve", 1.5)

        config = {
            "n_threads": max(4, self.cpu_threads - 2),
            "use_mmap": _hardware_config.get("use_mmap", True),
            "use_mlock": _hardware_config.get("use_mlock", False),
            "n_gpu_layers": 0,
        }

        if _hardware_config.get("n_threads", 0) > 0:
            config["n_threads"] = _hardware_config["n_threads"]

        if _hardware_config.get("n_gpu_layers", -1) == -1:
            pass
        elif _hardware_config.get("n_gpu_layers", -1) >= 0:
            config["n_gpu_layers"] = _hardware_config["n_gpu_layers"]
            return config

        if self.vram_total_gb == 0:
            return config

        available_vram = self.vram_total_gb - os_vram_reserve

        if is_concurrent:
            available_vram = (available_vram / 2.0) - kv_cache_reserve
        else:
            available_vram -= kv_cache_reserve

        required_vram_for_weights = model_size_b * GB_PER_BILLION_PARAMS

        if available_vram >= required_vram_for_weights:
            config["n_gpu_layers"] = -1

            if available_vram > required_vram_for_weights + 4:
                config["use_mlock"] = True

        elif available_vram > 0:
            layers_that_fit = int((available_vram * 1024) / MB_PER_LAYER)
            config["n_gpu_layers"] = max(0, min(TOTAL_LAYERS, layers_that_fit))

        else:
            config["n_gpu_layers"] = 0

        return config

        available_vram = self.vram_total_gb - OS_VRAM_RESERVE

        if is_concurrent:
            available_vram = (available_vram / 2.0) - KV_CACHE_RESERVE
        else:
            available_vram -= KV_CACHE_RESERVE

        required_vram_for_full_gpu = model_size_b * GB_PER_BILLION_PARAMS

        if available_vram >= required_vram_for_full_gpu:
            config["n_gpu_layers"] = -1
            if available_vram > required_vram_for_full_gpu + 4:
                config["use_mlock"] = True
        elif available_vram > 0:
            layers = int((available_vram * 1024) / MB_PER_LAYER)
            config["n_gpu_layers"] = max(0, min(TOTAL_LAYERS, layers))
        else:
            config["n_gpu_layers"] = 0

        return config


_profiler = None


def get_profiler() -> HardwareProfiler:
    global _profiler
    if _profiler is None:
        _profiler = HardwareProfiler()
    return _profiler
