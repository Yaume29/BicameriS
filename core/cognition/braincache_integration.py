"""
BrainCache Integration
======================
Compression KV cache pour améliorer les performances des modèles locaux.

Basé sur des techniques de compression avancées :
- PolarQuant + Walsh-Hadamard rotation
- Compression 3.8x à 6.4x du cache KV
- Support CUDA (RTX 4090, etc.)

Ce module détecte si BrainCache est disponible et configure
les hémisphères pour l'utiliser.
"""

import logging
import subprocess
import inspect
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("braincache")


@dataclass
class BrainCacheConfig:
    """Configuration BrainCache"""
    enabled: bool = False
    cache_type: str = "braincache3"  # braincache2, braincache3, braincache4
    asymmetric: bool = False  # q8_0-K + braincache-V
    boundary_v: bool = True  # Layer-aware V compression
    block_size: int = 64  # 32, 64 ou 128 (64 = meilleur compromis qualité/compression)


class BrainCacheDetector:
    """Détecte si BrainCache est disponible"""
    
    def __init__(self):
        self._llama_cpp_available = False
        self._braincache_params = False
        self._cuda_available = False
        self._gpu_info = {}
        self._detected = False
    
    def detect(self) -> Dict:
        """Lance la détection complète"""
        if self._detected:
            return self._get_results()
        
        self._check_llama_cpp()
        self._check_braincache_params()
        self._check_cuda()
        self._detected = True
        
        return self._get_results()
    
    def _check_llama_cpp(self):
        """Vérifie si llama-cpp-python est installé"""
        try:
            import llama_cpp
            self._llama_cpp_available = True
            self._llama_cpp_version = getattr(llama_cpp, "__version__", "unknown")
            logger.info(f"[BrainCache] llama-cpp-python v{self._llama_cpp_version} détecté")
        except ImportError:
            self._llama_cpp_available = False
            logger.warning("[BrainCache] llama-cpp-python non installé")
    
    def _check_braincache_params(self):
        """Vérifie si les paramètres BrainCache sont supportés"""
        if not self._llama_cpp_available:
            return
        
        try:
            from llama_cpp import Llama
            init_params = inspect.signature(Llama.__init__).parameters
            param_names = list(init_params.keys())
            
            # BrainCache utilise cache_type_k et cache_type_v
            self._braincache_params = (
                "cache_type_k" in param_names and 
                "cache_type_v" in param_names
            )
            
            if self._braincache_params:
                logger.info("[BrainCache] Paramètres BrainCache détectés!")
            else:
                logger.warning("[BrainCache] Paramètres BrainCache non disponibles")
                
        except Exception as e:
            logger.error(f"[BrainCache] Erreur détection paramètres: {e}")
    
    def _check_cuda(self):
        """Vérifie si CUDA est disponible"""
        try:
            import torch
            if torch.cuda.is_available():
                self._cuda_available = True
                self._gpu_info = {
                    "name": torch.cuda.get_device_name(0),
                    "memory_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
                }
                logger.info(f"[BrainCache] CUDA: {self._gpu_info['name']} ({self._gpu_info['memory_gb']:.1f} GB)")
            return
        except ImportError:
            pass
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines:
                    parts = lines[0].split(', ')
                    if len(parts) >= 2:
                        self._cuda_available = True
                        self._gpu_info = {"name": parts[0], "memory": parts[1]}
        except:
            pass
    
    def _get_results(self) -> Dict:
        """Retourne les résultats de détection"""
        return {
            "llama_cpp_available": self._llama_cpp_available,
            "llama_cpp_version": getattr(self, "_llama_cpp_version", None),
            "braincache_supported": self._braincache_params,
            "cuda_available": self._cuda_available,
            "gpu_info": self._gpu_info,
            "ready": self._llama_cpp_available and self._braincache_params
        }


class BrainCacheOptimizer:
    """Optimise les paramètres BrainCache selon le hardware"""
    
    def __init__(self, config: BrainCacheConfig):
        self.config = config
        self._detector = BrainCacheDetector()
    
    def get_optimal_config(self, model_size_gb: float, target_context: int) -> Dict:
        """
        Retourne la configuration optimale pour un modèle donné.
        
        Args:
            model_size_gb: Taille du modèle en GB
            target_context: Contexte cible (tokens)
        
        Returns:
            Dict avec la configuration optimale
        """
        detection = self._detector.detect()
        
        if not detection["ready"]:
            return {"error": "BrainCache non disponible"}
        
        gpu_memory = detection["gpu_info"].get("memory_gb", 0)
        
        # Calcul de la mémoire disponible
        available_vram = gpu_memory - model_size_gb - 2  # 2 GB de marge
        
        if available_vram < 1:
            return {"error": "VRAM insuffisante"}
        
        # Sélection du type de cache
        if model_size_gb > 30:
            cache_type = "braincache2"  # Max compression
        elif model_size_gb > 15:
            cache_type = "braincache3"  # Balanced
        else:
            cache_type = "braincache4"  # Best quality
        
        # Calcul du contexte max possible
        kv_per_token_gb = 0.0005  # Estimation
        max_context = int(available_vram / kv_per_token_gb)
        
        return {
            "cache_type": cache_type,
            "max_context": min(max_context, target_context),
            "asymmetric": model_size_gb > 10,
            "boundary_v": True,
            "block_size": 64 if model_size_gb > 15 else 128  # 64 = bon compromis pour 64GB RAM
        }
    
    def get_llama_params(self, config: BrainCacheConfig) -> Dict:
        """
        Retourne les paramètres à passer à llama_cpp.Llama()
        """
        params = {}
        
        if config.enabled:
            params["cache_type_k"] = config.cache_type
            params["cache_type_v"] = config.cache_type
            
            if config.asymmetric:
                params["cache_type_k"] = "q8_0"
        
        return params


# Instance globale
_detector: Optional[BrainCacheDetector] = None
_optimizer: Optional[BrainCacheOptimizer] = None


def get_braincache_detector() -> BrainCacheDetector:
    """Retourne le détecteur BrainCache"""
    global _detector
    if _detector is None:
        _detector = BrainCacheDetector()
    return _detector


def get_braincache_optimizer(config: BrainCacheConfig = None) -> BrainCacheOptimizer:
    """Retourne l'optimiseur BrainCache"""
    global _optimizer
    if _optimizer is None:
        if config is None:
            config = BrainCacheConfig()
        _optimizer = BrainCacheOptimizer(config)
    return _optimizer


def detect_braincache() -> Dict:
    """Fonction utilitaire pour détecter BrainCache"""
    return get_braincache_detector().detect()


def is_braincache_ready() -> bool:
    """Vérifie si BrainCache est prêt à être utilisé"""
    return detect_braincache().get("ready", False)
