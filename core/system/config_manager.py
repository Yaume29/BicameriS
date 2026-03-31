"""
Centralized Configuration Module
================================
Single source of truth for all application configuration.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
CONFIG_DIR = BASE_DIR / "storage" / "config"


@dataclass
class ServerConfig:
    """Server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    workers: int = 1
    cors_origins: list = field(default_factory=lambda: [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ])


@dataclass
class HemisphereConfig:
    """Configuration for a single hemisphere"""
    name: str = ""
    path: str = ""
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    n_ctx: int = 16384
    max_tokens: int = 2048
    n_gpu_layers: int = -1


@dataclass
class ModelsConfig:
    """Models configuration"""
    left_hemisphere: HemisphereConfig = field(default_factory=lambda: HemisphereConfig(
        name="",
        path="",
        temperature=0.7,
        top_p=0.9,
        repeat_penalty=1.1,
        n_ctx=16384,
        max_tokens=2048,
        n_gpu_layers=-1
    ))
    right_hemisphere: HemisphereConfig = field(default_factory=lambda: HemisphereConfig(
        name="",
        path="",
        temperature=1.2,
        top_p=0.9,
        repeat_penalty=1.0,
        n_ctx=4096,
        max_tokens=512,
        n_gpu_layers=-1
    ))


@dataclass
class CognitionConfig:
    """Cognition settings"""
    autonomous_loop: bool = False
    autonomous_interval: int = 30
    pulse_high: float = 0.75
    pulse_low: float = 0.25
    dreamer_interval: int = 300
    mcts_iterations: int = 1000
    mcts_exploration: float = 1.41


@dataclass
class SecurityConfig:
    """Security settings"""
    sandbox_docker: bool = True
    trauma_filter: bool = True
    max_execution_time: int = 30
    max_memory_mb: int = 512
    sal_classifier_enabled: bool = True


@dataclass
class HardwareConfig:
    """Hardware settings"""
    thermal_monitoring: bool = True
    entropy_tracking: bool = True
    vr_guillotine: bool = True
    max_cpu_temp: int = 85
    max_gpu_temp: int = 83
    min_free_vram_gb: float = 2.0
    n_gpu_layers: int = -1
    n_threads: int = 0  # Auto


@dataclass
class SystemConfig:
    """System settings"""
    initialized: bool = False
    persistent_autothink: bool = False
    auto_start_scheduler: bool = False
    tot_enabled: bool = False
    tool_registry_enabled: bool = False
    screenpipe_enabled: bool = False
    gaming_enabled: bool = False
    # Three levels of auto-control:
    auto_scaffolding_full: bool = False    # Level 1: Full (docker, execute, web)
    auto_scaffolding_limited: bool = False # Level 2: File creation + web tools
    auto_optimization: bool = False        # Level 3: LLM params only


@dataclass
class AppConfig:
    """Main application configuration"""
    server: ServerConfig = field(default_factory=ServerConfig)
    models: ModelsConfig = field(default_factory=ModelsConfig)
    cognition: CognitionConfig = field(default_factory=CognitionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    system: SystemConfig = field(default_factory=SystemConfig)


class ConfigManager:
    """
    Centralized configuration manager.
    Loads configuration from file, environment variables, and defaults.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else CONFIG_DIR / "app_config.json"
        self.config: AppConfig = AppConfig()
        self._load()
    
    def _load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._apply_dict(data)
                logging.info(f"[Config] Loaded from {self.config_file}")
            except Exception as e:
                logging.warning(f"[Config] Failed to load: {e}")
    
    def _apply_dict(self, data: Dict[str, Any]):
        """Apply dictionary to config"""
        if "server" in data:
            for k, v in data["server"].items():
                if hasattr(self.config.server, k):
                    setattr(self.config.server, k, v)
        
        if "models" in data:
            if "left_hemisphere" in data["models"]:
                for k, v in data["models"]["left_hemisphere"].items():
                    if hasattr(self.config.models.left_hemisphere, k):
                        setattr(self.config.models.left_hemisphere, k, v)
            if "right_hemisphere" in data["models"]:
                for k, v in data["models"]["right_hemisphere"].items():
                    if hasattr(self.config.models.right_hemisphere, k):
                        setattr(self.config.models.right_hemisphere, k, v)
        
        if "cognition" in data:
            for k, v in data["cognition"].items():
                if hasattr(self.config.cognition, k):
                    setattr(self.config.cognition, k, v)
        
        if "security" in data:
            for k, v in data["security"].items():
                if hasattr(self.config.security, k):
                    setattr(self.config.security, k, v)
        
        if "hardware" in data:
            for k, v in data["hardware"].items():
                if hasattr(self.config.hardware, k):
                    setattr(self.config.hardware, k, v)
        
        if "system" in data:
            for k, v in data["system"].items():
                if hasattr(self.config.system, k):
                    setattr(self.config.system, k, v)
    
    def save(self):
        """Save configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = asdict(self.config)
        
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logging.info(f"[Config] Saved to {self.config_file}")
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get config value by dot path (e.g., 'server.port')"""
        parts = path.split(".")
        obj = self.config
        
        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default
        
        return obj
    
    def set(self, path: str, value: Any):
        """Set config value by dot path"""
        parts = path.split(".")
        obj = self.config
        
        for part in parts[:-1]:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return
        
        if hasattr(obj, parts[-1]):
            setattr(obj, parts[-1], value)
    
    def get_hemisphere_config(self, hemisphere: str) -> HemisphereConfig:
        """Get configuration for a specific hemisphere"""
        if hemisphere in ["left", "left_hemisphere"]:
            return self.config.models.left_hemisphere
        elif hemisphere in ["right", "right_hemisphere"]:
            return self.config.models.right_hemisphere
        else:
            raise ValueError(f"Unknown hemisphere: {hemisphere}")
    
    def update_hemisphere(self, hemisphere: str, **kwargs):
        """Update hemisphere configuration"""
        hemi = self.get_hemisphere_config(hemisphere)
        for k, v in kwargs.items():
            if hasattr(hemi, k):
                setattr(hemi, k, v)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self.config)


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_app_config() -> AppConfig:
    """Get application configuration"""
    return get_config().config
