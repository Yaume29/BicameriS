"""
LLM Load Balancer
=================
Allows using multiple LLM providers simultaneously with:
- Round-robin distribution
- Cap on concurrent requests
- Fallback on failure
- Local + Cloud hybrid mode
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("llm.load_balancer")


@dataclass
class ProviderConfig:
    name: str
    priority: int = 1
    max_concurrent: int = 1
    enabled: bool = True
    config: Dict = field(default_factory=dict)


@dataclass
class RequestStats:
    provider: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    avg_latency: float = 0.0
    last_used: Optional[str] = None


class LLMLoadBalancer:
    """
    Load balancer for multiple LLM providers.
    Allows round-robin, fallback, and rate limiting.
    """
    
    def __init__(self):
        self._providers: Dict[str, ProviderConfig] = {}
        self._stats: Dict[str, RequestStats] = {}
        self._active_requests: Dict[str, int] = {}
        self._round_robin_index: int = 0
        self._cap_enabled: bool = False
        self._max_concurrent: int = 2
        self._current_provider: Optional[str] = None
        
    def add_provider(self, name: str, priority: int = 1, max_concurrent: int = 1, **config):
        """Add a provider to the pool"""
        self._providers[name] = ProviderConfig(
            name=name,
            priority=priority,
            max_concurrent=max_concurrent,
            config=config
        )
        self._stats[name] = RequestStats(provider=name)
        self._active_requests[name] = 0
        logger.info(f"[LoadBalancer] Provider added: {name}")
    
    def remove_provider(self, name: str):
        """Remove a provider"""
        if name in self._providers:
            del self._providers[name]
            if name in self._stats:
                del self._stats[name]
            if name in self._active_requests:
                del self._active_requests[name]
    
    def enable_cap(self, max_concurrent: int = 2):
        """Enable the cap to limit concurrent requests"""
        self._cap_enabled = True
        self._max_concurrent = max_concurrent
        logger.info(f"[LoadBalancer] Cap enabled: max {max_concurrent} concurrent requests")
    
    def disable_cap(self):
        """Disable the cap"""
        self._cap_enabled = False
        logger.info("[LoadBalancer] Cap disabled")
    
    def set_active_provider(self, name: str):
        """Force use of a specific provider (disable load balancing)"""
        if name in self._providers:
            self._current_provider = name
            logger.info(f"[LoadBalancer] Forced provider: {name}")
    
    def enable_round_robin(self):
        """Enable round-robin mode between all providers"""
        self._current_provider = None
        self._round_robin_index = 0
        logger.info("[LoadBalancer] Round-robin enabled")
    
    def get_next_provider(self) -> Optional[str]:
        """Get next provider in round-robin"""
        enabled = [p for p in self._providers.values() if p.enabled]
        
        if not enabled:
            return None
        
        if self._current_provider:
            return self._current_provider
        
        provider = enabled[self._round_robin_index % len(enabled)].name
        self._round_robin_index += 1
        return provider
    
    def _can_use_provider(self, provider: str) -> bool:
        """Check if provider can be used (respects cap)"""
        if not self._cap_enabled:
            return True
        
        if provider not in self._active_requests:
            return True
        
        return self._active_requests[provider] < self._providers[provider].max_concurrent
    
    def _record_request(self, provider: str, success: bool, latency: float):
        """Record request statistics"""
        if provider not in self._stats:
            self._stats[provider] = RequestStats(provider=provider)
        
        stats = self._stats[provider]
        stats.total_requests += 1
        
        if success:
            stats.successful += 1
            stats.avg_latency = (stats.avg_latency * (stats.successful - 1) + latency) / stats.successful
        else:
            stats.failed += 1
        
        stats.last_used = datetime.now().isoformat()
    
    async def call(
        self, 
        prompt: str, 
        provider: str = None,
        fallback: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call LLM with load balancing.
        
        Args:
            prompt: The prompt to send
            provider: Specific provider (optional, uses round-robin if None)
            fallback: Try other providers if one fails
            **kwargs: Additional parameters (temperature, etc.)
        
        Returns:
            {"status": "success", "provider": "...", "response": "...", "latency": ...}
        """
        providers_to_try = []
        
        if provider:
            if provider in self._providers:
                providers_to_try = [provider]
        else:
            providers_to_try = [p.name for p in self._providers.values() if p.enabled]
        
        if not providers_to_try:
            return {"status": "error", "error": "No providers available"}
        
        errors = []
        
        for p in providers_to_try:
            if not self._can_use_provider(p):
                if fallback and len(providers_to_try) > 1:
                    continue
                return {"status": "error", "error": f"Cap reached for {p}"}
            
            self._active_requests[p] = self._active_requests.get(p, 0) + 1
            
            try:
                start = datetime.now()
                result = await self._call_provider(p, prompt, **kwargs)
                latency = (datetime.now() - start).total_seconds()
                
                self._record_request(p, True, latency)
                
                if result.get("status") == "error":
                    errors.append(f"{p}: {result.get('error')}")
                    if fallback and len(providers_to_try) > 1:
                        continue
                    return result
                
                return {
                    "status": "success",
                    "provider": p,
                    "response": result.get("response"),
                    "latency": latency
                }
                
            except Exception as e:
                self._record_request(p, False, 0)
                errors.append(f"{p}: {str(e)}")
                
            finally:
                self._active_requests[p] = max(0, self._active_requests.get(p, 1) - 1)
        
        return {"status": "error", "error": f"All providers failed: {errors}"}
    
    async def _call_provider(self, provider: str, prompt: str, **kwargs) -> Dict:
        """Call a specific provider"""
        from core.cognition.auto_optimizer import get_auto_optimizer
        
        optimizer = get_auto_optimizer()
        config = optimizer.get_provider_config(provider)
        
        if not config:
            return {"status": "error", "error": f"Provider {provider} not configured"}
        
        if provider == "local":
            return await self._call_local(prompt, **kwargs)
        elif provider == "openai":
            return await self._call_openai(prompt, config, **kwargs)
        elif provider == "anthropic":
            return await self._call_anthropic(prompt, config, **kwargs)
        elif provider == "ollama":
            return await self._call_ollama(prompt, config, **kwargs)
        else:
            return {"status": "error", "error": f"Provider {provider} not implemented"}
    
    async def _call_local(self, prompt: str, **kwargs) -> Dict:
        """Call local hemisphere"""
        try:
            from core.cognition.left_hemisphere import get_left_hemisphere
            left = get_left_hemisphere()
            
            if not left:
                return {"status": "error", "error": "Local model not loaded"}
            
            response = await asyncio.to_thread(left.think, prompt, **kwargs)
            return {"status": "success", "response": response}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _call_openai(self, prompt: str, config: Dict, **kwargs) -> Dict:
        """Call OpenAI API"""
        try:
            import aiohttp
            
            api_key = config.get("api_key")
            endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
            model = config.get("model", "gpt-4")
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", config.get("temperature", 0.7)),
                "max_tokens": kwargs.get("max_tokens", config.get("max_tokens", 2048))
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", "response": data["choices"][0]["message"]["content"]}
                    else:
                        return {"status": "error", "error": f"API error: {resp.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _call_anthropic(self, prompt: str, config: Dict, **kwargs) -> Dict:
        """Call Anthropic API"""
        try:
            import aiohttp
            
            api_key = config.get("api_key")
            endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
            model = config.get("model", "claude-3-opus-20240229")
            
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": model,
                "max_tokens": kwargs.get("max_tokens", config.get("max_tokens", 4096)),
                "messages": [{"role": "user", "content": prompt}]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", "response": data["content"][0]["text"]}
                    else:
                        return {"status": "error", "error": f"API error: {resp.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _call_ollama(self, prompt: str, config: Dict, **kwargs) -> Dict:
        """Call Ollama API"""
        try:
            import aiohttp
            
            base_url = config.get("base_url", "http://localhost:11434")
            model = config.get("model", "llama2")
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get("temperature", config.get("temperature", 0.7)),
                    "top_p": kwargs.get("top_p", config.get("top_p", 0.9))
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {"status": "success", "response": data.get("response", "")}
                    else:
                        return {"status": "error", "error": f"API error: {resp.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def get_stats(self) -> Dict:
        """Get statistics for all providers"""
        stats = {}
        for name, s in self._stats.items():
            stats[name] = {
                "total_requests": s.total_requests,
                "successful": s.successful,
                "failed": s.failed,
                "success_rate": s.successful / s.total_requests if s.total_requests > 0 else 0,
                "avg_latency": s.avg_latency,
                "active_requests": self._active_requests.get(name, 0),
                "last_used": s.last_used
            }
        
        return {
            "providers": list(self._providers.keys()),
            "cap_enabled": self._cap_enabled,
            "max_concurrent": self._max_concurrent,
            "current_mode": "single" if self._current_provider else "round_robin",
            "stats": stats
        }


_load_balancer: Optional[LLMLoadBalancer] = None


def get_load_balancer() -> LLMLoadBalancer:
    """Get global load balancer instance"""
    global _load_balancer
    if _load_balancer is None:
        _load_balancer = LLMLoadBalancer()
    return _load_balancer
