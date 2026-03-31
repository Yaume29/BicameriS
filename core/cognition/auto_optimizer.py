"""
Auto-Optimization Module
=======================
Allows the AI to modify LLM parameters at runtime.
Level 3 auto-control: Can change temperature, top_p, etc.

Supported providers:
- local (llama.cpp): modify temperature, top_p, max_tokens, repeat_penalty
- ollama: modify model, temperature, top_p
- lmstudio: modify model, temperature, top_p, endpoint
- openai: modify api_key, endpoint, model
- anthropic (Claude): modify api_key, model
- kimi: modify api_key, endpoint, model
"""

import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
CONFIG_DIR = BASE_DIR / "storage" / "config"


@dataclass
class OptimizationLog:
    timestamp: str
    param: str
    old_value: Any
    new_value: Any
    reason: str


class AutoOptimizer:
    """
    Level 3 auto-optimization.
    Allows the AI to modify LLM parameters with immediate effect.
    """

    def __init__(self):
        self.optimization_history: list[OptimizationLog] = []
        
    def can_optimize(self) -> bool:
        """Check if auto-optimization is enabled"""
        try:
            from core.system.switchboard import get_switchboard
            return get_switchboard().is_active("auto_optimization")
        except:
            return False
    
    def _save_api_config(self, provider: str, config: Dict):
        """Save API configuration to file"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config_file = CONFIG_DIR / "api_config.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                all_configs = json.load(f)
        else:
            all_configs = {}
        
        all_configs[provider] = config
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(all_configs, f, indent=2)
    
    def get_provider_config(self, provider: str) -> Dict:
        """Get current provider configuration"""
        config_file = CONFIG_DIR / "api_config.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                all_configs = json.load(f)
                return all_configs.get(provider, {})
        return {}
    
    def list_providers(self) -> Dict:
        """List all configured providers"""
        config_file = CONFIG_DIR / "api_config.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                all_configs = json.load(f)
                return {
                    provider: {k: v for k, v in config.items() if k != "api_key"} 
                    for provider, config in all_configs.items()
                }
        return {}

    def optimize_provider(self, provider: str, **kwargs) -> Dict:
        """Optimize settings for ANY provider (generic)"""
        if not self.can_optimize():
            return {"status": "ERROR", "error": "Auto-optimization not enabled"}
        
        if not provider:
            return {"status": "ERROR", "error": "Provider name required"}
        
        reason = kwargs.pop("reason", "")
        
        if provider == "local":
            return self.optimize_local(**kwargs)
        
        config = self.get_provider_config(provider)
        old = config.copy()
        
        for key, value in kwargs.items():
            if value is not None:
                config[key] = value
        
        self._save_api_config(provider, config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param=provider,
            old_value=old,
            new_value=config,
            reason=reason
        ))
        
        logger.info(f"[AutoOptimizer] {provider} optimized: {old} -> {config}")
        
        safe_config = {k: v for k, v in config.items() if k not in ["api_key", "api-key", "key", "secret", "password"]}
        
        return {"status": "SUCCESS", "provider": provider, "old": old, "new": safe_config, "reason": reason}
    
    def switch_provider(self, provider: str, **kwargs) -> Dict:
        """Switch to a different provider with given configuration"""
        if not self.can_optimize():
            return {"status": "ERROR", "error": "Auto-optimization not enabled"}
        
        result = self.optimize_provider(provider, reason=f"Switch to {provider}", **kwargs)
        
        if result.get("status") == "SUCCESS":
            from core.system.switchboard import get_switchboard
            try:
                sb = get_switchboard()
                sb.set_active_provider(provider)
            except:
                pass
        
        return result
    
    def set_active_provider(self, provider: str) -> Dict:
        """Set the currently active provider"""
        if not self.can_optimize():
            return {"status": "ERROR", "error": "Auto-optimization not enabled"}
        
        config = self.get_provider_config(provider)
        if not config:
            return {"status": "ERROR", "error": f"Provider {provider} not configured"}
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="active_provider",
            old_value="",
            new_value=provider,
            reason="Provider switched"
        ))
        
        return {"status": "SUCCESS", "active_provider": provider}
    
    def get_available_providers(self) -> Dict:
        """Get all configured providers and their status"""
        providers = self.list_providers()
        
        active = None
        try:
            from core.system.switchboard import get_switchboard
            sb = get_switchboard()
            active = getattr(sb, "_active_provider", None)
        except:
            pass
        
        return {
            "configured": providers,
            "active": active,
            "count": len(providers)
        }
    
    def optimize_local(self, temperature: float = None, top_p: float = None, repeat_penalty: float = None, max_tokens: int = None, reason: str = "") -> Dict:
        """Optimize local llama.cpp settings"""
        from datetime import datetime
        try:
            from core.cognition.left_hemisphere import get_left_hemisphere
            left = get_left_hemisphere()
            
            old = {}
            new_vals = {}
            if left:
                if temperature is not None:
                    old["temperature"] = left.temperature
                    left.temperature = temperature
                    new_vals["temperature"] = temperature
                if top_p is not None:
                    old["top_p"] = left.top_p
                    left.top_p = top_p
                    new_vals["top_p"] = top_p
                if repeat_penalty is not None:
                    old["repeat_penalty"] = left.repeat_penalty
                    left.repeat_penalty = repeat_penalty
                    new_vals["repeat_penalty"] = repeat_penalty
                if max_tokens is not None:
                    old["max_tokens"] = left.max_tokens
                    left.max_tokens = max_tokens
                    new_vals["max_tokens"] = max_tokens
            
            self.optimization_history.append(OptimizationLog(
                timestamp=datetime.now().isoformat(),
                param="local",
                old_value=old,
                new_value=new_vals,
                reason=reason
            ))
            
            return {"status": "SUCCESS", "provider": "local", "old": old, "new": new_vals, "reason": reason}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def optimize_ollama(self, model: str = None, temperature: float = None, top_p: float = None, base_url: str = None, reason: str = "") -> Dict:
        """Optimize Ollama settings"""
        config = self.get_provider_config("ollama")
        old = config.copy()
        
        if model: config["model"] = model
        if temperature is not None: config["temperature"] = temperature
        if top_p is not None: config["top_p"] = top_p
        if base_url: config["base_url"] = base_url
        
        self._save_api_config("ollama", config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="ollama",
            old_value=old,
            new_value=config,
            reason=reason
        ))
        
        return {"status": "SUCCESS", "provider": "ollama", "old": old, "new": config, "reason": reason}
    
    def optimize_lmstudio(self, model: str = None, temperature: float = None, top_p: float = None, endpoint: str = None, reason: str = "") -> Dict:
        """Optimize LM Studio settings"""
        config = self.get_provider_config("lmstudio")
        old = config.copy()
        
        if model: config["model"] = model
        if temperature is not None: config["temperature"] = temperature
        if top_p is not None: config["top_p"] = top_p
        if endpoint: config["endpoint"] = endpoint
        
        self._save_api_config("lmstudio", config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="lmstudio",
            old_value=old,
            new_value=config,
            reason=reason
        ))
        
        return {"status": "SUCCESS", "provider": "lmstudio", "old": old, "new": config, "reason": reason}
    
    def optimize_openai(self, api_key: str = None, endpoint: str = None, model: str = None, temperature: float = None, reason: str = "") -> Dict:
        """Optimize OpenAI settings"""
        config = self.get_provider_config("openai")
        old = config.copy()
        
        if api_key: config["api_key"] = api_key
        if endpoint: config["endpoint"] = endpoint
        if model: config["model"] = model
        if temperature is not None: config["temperature"] = temperature
        
        self._save_api_config("openai", config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="openai",
            old_value=old,
            new_value={k: v for k, v in config.items() if k != "api_key"},
            reason=reason
        ))
        
        return {"status": "SUCCESS", "provider": "openai", "old": old, "new": {k: v for k, v in config.items() if k != "api_key"}, "reason": reason}
    
    def optimize_anthropic(self, api_key: str = None, model: str = None, temperature: float = None, reason: str = "") -> Dict:
        """Optimize Anthropic (Claude) settings"""
        config = self.get_provider_config("anthropic")
        old = config.copy()
        
        if api_key: config["api_key"] = api_key
        if model: config["model"] = model
        if temperature is not None: config["temperature"] = temperature
        
        self._save_api_config("anthropic", config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="anthropic",
            old_value=old,
            new_value={k: v for k, v in config.items() if k != "api_key"},
            reason=reason
        ))
        
        return {"status": "SUCCESS", "provider": "anthropic", "old": old, "new": {k: v for k, v in config.items() if k != "api_key"}, "reason": reason}
    
    def optimize_kimi(self, api_key: str = None, endpoint: str = None, model: str = None, temperature: float = None, reason: str = "") -> Dict:
        """Optimize Kimi (Moonshot AI) settings"""
        config = self.get_provider_config("kimi")
        old = config.copy()
        
        if api_key: config["api_key"] = api_key
        if endpoint: config["endpoint"] = endpoint
        if model: config["model"] = model
        if temperature is not None: config["temperature"] = temperature
        
        self._save_api_config("kimi", config)
        
        from datetime import datetime
        self.optimization_history.append(OptimizationLog(
            timestamp=datetime.now().isoformat(),
            param="kimi",
            old_value=old,
            new_value={k: v for k, v in config.items() if k != "api_key"},
            reason=reason
        ))
        
        return {"status": "SUCCESS", "provider": "kimi", "old": old, "new": {k: v for k, v in config.items() if k != "api_key"}, "reason": reason}
    
    def optimize_left_hemisphere(
        self, 
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Optimize left hemisphere parameters"""
        if not self.can_optimize():
            return {"status": "ERROR", "error": "Auto-optimization not enabled"}
        
        try:
            from core.cognition.left_hemisphere import get_left_hemisphere
            left = get_left_hemisphere()
            
            if not left:
                return {"status": "ERROR", "error": "Left hemisphere not loaded"}
            
            old_params = {}
            if temperature is not None:
                old_params["temperature"] = left.temperature
                left.temperature = temperature
            if top_p is not None:
                old_params["top_p"] = left.top_p
                left.top_p = top_p
            if repeat_penalty is not None:
                old_params["repeat_penalty"] = left.repeat_penalty
                left.repeat_penalty = repeat_penalty
            if max_tokens is not None:
                old_params["max_tokens"] = left.max_tokens
                left.max_tokens = max_tokens
            
            from datetime import datetime
            self.optimization_history.append(OptimizationLog(
                timestamp=datetime.now().isoformat(),
                param="left_hemisphere",
                old_value=old_params,
                new_value={"temperature": temperature, "top_p": top_p, "repeat_penalty": repeat_penalty, "max_tokens": max_tokens},
                reason=reason
            ))
            
            logger.info(f"[AutoOptimizer] Left hemisphere optimized: {old_params} -> {reason}")
            
            return {
                "status": "SUCCESS", 
                "hemisphere": "left",
                "old_values": old_params,
                "new_values": {"temperature": temperature, "top_p": top_p, "repeat_penalty": repeat_penalty, "max_tokens": max_tokens},
                "reason": reason
            }
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def optimize_right_hemisphere(
        self, 
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        repeat_penalty: Optional[float] = None,
        max_tokens: Optional[int] = None,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Optimize right hemisphere parameters"""
        if not self.can_optimize():
            return {"status": "ERROR", "error": "Auto-optimization not enabled"}
        
        try:
            from core.cognition.right_hemisphere import get_right_hemisphere
            right = get_right_hemisphere()
            
            if not right:
                return {"status": "ERROR", "error": "Right hemisphere not loaded"}
            
            old_params = {}
            if temperature is not None:
                old_params["temperature"] = right.temperature
                right.temperature = temperature
            if top_p is not None:
                old_params["top_p"] = right.top_p
                right.top_p = top_p
            if repeat_penalty is not None:
                old_params["repeat_penalty"] = right.repeat_penalty
                right.repeat_penalty = repeat_penalty
            if max_tokens is not None:
                old_params["max_tokens"] = right.max_tokens
                right.max_tokens = max_tokens
            
            from datetime import datetime
            self.optimization_history.append(OptimizationLog(
                timestamp=datetime.now().isoformat(),
                param="right_hemisphere",
                old_value=old_params,
                new_value={"temperature": temperature, "top_p": top_p, "repeat_penalty": repeat_penalty, "max_tokens": max_tokens},
                reason=reason
            ))
            
            logger.info(f"[AutoOptimizer] Right hemisphere optimized: {old_params} -> {reason}")
            
            return {
                "status": "SUCCESS", 
                "hemisphere": "right",
                "old_values": old_params,
                "new_values": {"temperature": temperature, "top_p": top_p, "repeat_penalty": repeat_penalty, "max_tokens": max_tokens},
                "reason": reason
            }
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def get_optimization_history(self) -> list:
        """Get optimization history"""
        return [
            {
                "timestamp": log.timestamp,
                "param": log.param,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "reason": log.reason
            }
            for log in self.optimization_history
        ]


_optimizer_instance: Optional[AutoOptimizer] = None


def get_auto_optimizer() -> AutoOptimizer:
    """Get global auto optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = AutoOptimizer()
    return _optimizer_instance
