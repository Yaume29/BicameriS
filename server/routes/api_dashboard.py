"""
API Dashboard Routes
====================
Real-time metrics and monitoring endpoints
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["dashboard"])

# Track uptime
_start_time = time.time()


@router.get("/dashboard/metrics")
async def dashboard_metrics():
    """Get real-time dashboard metrics"""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - _start_time,
            "system": await _get_system_metrics(),
            "models": await _get_model_metrics(),
            "cognition": await _get_cognition_metrics(),
            "inference": await _get_inference_metrics()
        }
        return metrics
    except Exception as e:
        return {"error": str(e)}


@router.get("/dashboard/status")
async def dashboard_status():
    """Get overall system status"""
    try:
        from server.routes.api_models import _models_state, get_left_hemisphere, get_right_hemisphere
        
        left = get_left_hemisphere()
        right = get_right_hemisphere()
        
        left_loaded = left is not None and left.is_loaded if left else False
        right_loaded = right is not None and right.is_loaded if right else False
        
        if left_loaded and right_loaded:
            status = "BICAMERAL"
            status_color = "#00e5ff"
        elif left_loaded or right_loaded:
            status = "ACTIVE"
            status_color = "#00ff95"
        else:
            status = "STANDBY"
            status_color = "#666"
        
        return {
            "status": status,
            "status_color": status_color,
            "models": {
                "left": {"loaded": left_loaded},
                "right": {"loaded": right_loaded}
            }
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


@router.get("/dashboard/pulse")
async def dashboard_pulse():
    """Get current system pulse"""
    try:
        from server.extensions import registry
        
        pulse = 0.5
        if registry.entropy:
            try:
                pulse = registry.entropy.pulse if hasattr(registry.entropy, 'pulse') else 0.5
            except:
                pass
        
        return {
            "pulse": pulse,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"pulse": 0.5, "error": str(e)}


@router.get("/dashboard/history")
async def dashboard_history(limit: int = 50):
    """Get system history/metrics over time"""
    try:
        from server.extensions import registry
        
        history = []
        
        # Get Corps Calleux history
        if registry.corps_calleux:
            try:
                for cycle in list(registry.corps_calleux.history)[-limit:]:
                    if hasattr(cycle, '__dict__'):
                        history.append(cycle.__dict__)
                    elif isinstance(cycle, dict):
                        history.append(cycle)
            except:
                pass
        
        return {"history": history}
    except Exception as e:
        return {"history": [], "error": str(e)}


async def _get_system_metrics() -> Dict[str, Any]:
    """Get system-level metrics"""
    metrics = {}
    
    try:
        import psutil
        
        # CPU
        metrics["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        metrics["cpu_count"] = psutil.cpu_count()
        
        # RAM
        mem = psutil.virtual_memory()
        metrics["ram_total_gb"] = round(mem.total / (1024**3), 2)
        metrics["ram_used_gb"] = round(mem.used / (1024**3), 2)
        metrics["ram_percent"] = mem.percent
        
        # Disk
        disk = psutil.disk_usage('/')
        metrics["disk_total_gb"] = round(disk.total / (1024**3), 2)
        metrics["disk_used_gb"] = round(disk.used / (1024**3), 2)
        metrics["disk_percent"] = round(disk.used / disk.total * 100, 1)
        
    except ImportError:
        metrics["error"] = "psutil not available"
    
    return metrics


async def _get_model_metrics() -> Dict[str, Any]:
    """Get model-related metrics"""
    from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
    
    left = get_left_hemisphere()
    right = get_right_hemisphere()
    
    metrics = {
        "left": {
            "loaded": left is not None and left.is_loaded if left else False,
            "name": getattr(left, 'model_path', None) if left else None
        },
        "right": {
            "loaded": right is not None and right.is_loaded if right else False,
            "name": getattr(right, 'model_path', None) if right else None
        }
    }
    
    # Get VRAM usage if available
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu = gpus[0]
            metrics["gpu"] = {
                "name": gpu.name,
                "vram_used_mb": gpu.memoryUsed,
                "vram_total_mb": gpu.memoryTotal,
                "vram_percent": round(gpu.memoryUsed / gpu.memoryTotal * 100, 1),
                "temperature": gpu.temperature
            }
    except:
        pass
    
    return metrics


async def _get_cognition_metrics() -> Dict[str, Any]:
    """Get cognition-related metrics"""
    metrics = {}
    
    try:
        from server.extensions import registry
        
        # Corps Calleux stats
        if registry.corps_calleux:
            metrics["corps_calleux"] = {
                "cycles": len(registry.corps_calleux.history) if hasattr(registry.corps_calleux, 'history') else 0,
                "connected": registry.corps_calleux.left is not None and registry.corps_calleux.right is not None
            }
        
        # Reasoning Kernel stats
        try:
            from core.cognition.reasoning_kernel import get_reasoning_kernel
            kernel = get_reasoning_kernel()
            if kernel:
                metrics["reasoning_kernel"] = kernel.get_stats()
        except:
            pass
        
    except Exception as e:
        metrics["error"] = str(e)
    
    return metrics


async def _get_inference_metrics() -> Dict[str, Any]:
    """Get inference-related metrics"""
    metrics = {}
    
    try:
        from server.extensions import registry
        
        if registry.inference_manager:
            metrics["inference_manager"] = {
                "available": True
            }
        
        # Get inference stats from API if available
        from server.routes.api_models import _models_state
        metrics["models_state"] = _models_state
        
    except Exception as e:
        metrics["error"] = str(e)
    
    return metrics
