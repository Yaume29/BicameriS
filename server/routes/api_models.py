"""
API Models Routes
================
Model scanning and loading endpoints with real GGUF loading
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["models"])

# Global state for loaded models
_models_state = {
    "left": None,
    "right": None,
    "is_split_mode": False,
    "corps_calleux": {"total_cycles": 0}
}

# LM Studio URL
_lmstudio_url = "http://localhost:1234/v1"

# Global hemisphere instances (accessible from other modules)
_left_hemisphere = None
_right_hemisphere = None


def get_left_hemisphere():
    """Get the loaded left hemisphere instance"""
    global _left_hemisphere
    return _left_hemisphere


def get_right_hemisphere():
    """Get the loaded right hemisphere instance"""
    global _right_hemisphere
    return _right_hemisphere


def get_models_state():
    """Get current models state"""
    return _models_state.copy()


@router.get("/models/default-path")
async def models_default_path():
    """Get default model scan path"""
    username = os.environ.get("USERNAME", "user")
    possible_paths = [
        f"C:\\Users\\{username}\\.lmstudio\\models",
        f"C:\\Users\\{username}\\AppData\\Local\\.lmstudio\\models",
        str(Path.home() / "models"),
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            return {"path": p}
    
    return {"path": str(Path.home())}


@router.post("/models/scan")
async def models_scan(request: Request):
    """Start model scan"""
    try:
        data = await request.json()
        path = data.get("path", "")
        
        if not path or not os.path.exists(path):
            return {"status": "error", "message": "Chemin invalide ou introuvable"}
        
        from core.hardware.model_scanner import get_scanner
        scanner = get_scanner()
        
        result = scanner.scan(path)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/models/scan-usual")
async def models_scan_usual():
    """Scan usual model folders"""
    try:
        username = os.environ.get("USERNAME", "user")
        
        usual_paths = [
            str(Path(__file__).parent.parent.parent / "models"),
            f"C:\\Users\\{username}\\.lmstudio\\models",
            f"C:\\Users\\{username}\\AppData\\Local\\.lmstudio\\models",
        ]
        
        from core.hardware.model_scanner import get_scanner
        scanner = get_scanner()
        
        for p in usual_paths:
            if os.path.exists(p):
                scanner.scan(p)
                return {"status": "started", "path": p}
        
        return {"status": "error", "message": "Aucun dossier habituel trouvé"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/models/results")
async def models_results():
    """Get scan results"""
    try:
        from core.hardware.model_scanner import get_scanner
        scanner = get_scanner()
        
        status = scanner.get_status()
        
        return {
            "is_scanning": status["is_scanning"],
            "count": status["count"],
            "models": status["models"],
            "path": status["path"],
            "elapsed_seconds": status["elapsed_seconds"]
        }
        
    except Exception as e:
        return {"is_scanning": False, "count": 0, "models": [], "error": str(e)}


@router.get("/models/status")
async def models_status():
    """Get loaded models status"""
    try:
        left = _models_state.get("left")
        right = _models_state.get("right")
        
        # Get real loaded status from hemisphere instances
        left_loaded = _left_hemisphere is not None and _left_hemisphere.is_loaded
        right_loaded = _right_hemisphere is not None and _right_hemisphere.is_loaded
        
        # Get Corps Calleux cycle count
        cycles = 0
        try:
            from server.extensions import registry
            if registry.corps_calleux:
                cycles = len(registry.corps_calleux.history)
        except:
            pass
        
        return {
            "left": {
                "loaded": left_loaded,
                "model_name": left.get("name") if left else None,
                "path": left.get("path") if left else None
            },
            "right": {
                "loaded": right_loaded,
                "model_name": right.get("name") if right else None,
                "path": right.get("path") if right else None
            },
            "is_split_mode": _models_state.get("is_split_mode", False),
            "corps_calleux": {"total_cycles": cycles}
        }
        
    except Exception as e:
        return {
            "left": {"loaded": False},
            "right": {"loaded": False},
            "is_split_mode": False,
            "corps_calleux": {"total_cycles": 0},
            "error": str(e)
        }


@router.post("/models/load")
async def models_load(request: Request):
    """Load models with real GGUF loading"""
    global _left_hemisphere, _right_hemisphere, _models_state
    
    try:
        data = await request.json()
        
        left_path = data.get("left_path")
        right_path = data.get("right_path")
        method = data.get("method", "local")
        split_mode = data.get("split_mode", False)
        
        # Get parameters from config
        left_n_ctx = data.get("left_n_ctx", 16384)
        left_temp = data.get("left_temperature", 0.7)
        left_top_p = data.get("left_top_p", 0.9)
        left_repeat = data.get("left_repeat_penalty", 1.1)
        left_max_tokens = data.get("left_max_tokens", 2048)
        left_gpu_layers = data.get("left_n_gpu_layers", -1)
        
        right_n_ctx = data.get("right_n_ctx", 4096)
        right_temp = data.get("right_temperature", 1.2)
        right_top_p = data.get("right_top_p", 0.9)
        right_repeat = data.get("right_repeat_penalty", 1.0)
        right_max_tokens = data.get("right_max_tokens", 512)
        right_gpu_layers = data.get("right_n_gpu_layers", -1)
        
        # Validate paths for local method
        if method == "local":
            if left_path and not os.path.exists(left_path):
                return {"status": "error", "error": f"Modèle gauche introuvable: {left_path}"}
            if right_path and right_path != left_path and not os.path.exists(right_path):
                return {"status": "error", "error": f"Modèle droit introuvable: {right_path}"}
        
        # Unload existing models first
        if _left_hemisphere:
            try:
                _left_hemisphere.unload()
            except:
                pass
        if _right_hemisphere:
            try:
                _right_hemisphere.unload()
            except:
                pass
        
        _left_hemisphere = None
        _right_hemisphere = None
        
        # Load left hemisphere
        if left_path:
            logging.info(f"[Models] Chargement DIA (Gauche): {left_path}")
            try:
                from core.cognition.left_hemisphere import LeftHemisphere
                _left_hemisphere = LeftHemisphere(
                    model_path=left_path,
                    n_ctx=left_n_ctx,
                    n_gpu_layers=left_gpu_layers,
                    temperature=left_temp,
                    max_tokens=left_max_tokens,
                    top_p=left_top_p,
                    repeat_penalty=left_repeat
                )
                
                if not _left_hemisphere.is_loaded:
                    return {"status": "error", "error": "Échec du chargement du modèle gauche"}
                    
                logging.info(f"[Models] ✅ DIA chargé: {os.path.basename(left_path)}")
            except Exception as e:
                logging.error(f"[Models] Erreur chargement DIA: {e}")
                return {"status": "error", "error": f"Erreur DIA: {str(e)}"}
        
        # Load right hemisphere
        actual_right_path = right_path if not split_mode and right_path else left_path
        if actual_right_path:
            logging.info(f"[Models] Chargement PAL (Droit): {actual_right_path}")
            try:
                from core.cognition.right_hemisphere import RightHemisphere
                _right_hemisphere = RightHemisphere(
                    model_path=actual_right_path,
                    n_ctx=right_n_ctx,
                    n_gpu_layers=right_gpu_layers,
                    temperature=right_temp,
                    max_tokens=right_max_tokens,
                    top_p=right_top_p,
                    repeat_penalty=right_repeat
                )
                
                if not _right_hemisphere.is_loaded:
                    return {"status": "error", "error": "Échec du chargement du modèle droit"}
                    
                logging.info(f"[Models] ✅ PAL chargé: {os.path.basename(actual_right_path)}")
            except Exception as e:
                logging.error(f"[Models] Erreur chargement PAL: {e}")
                return {"status": "error", "error": f"Erreur PAL: {str(e)}"}
        
        # Connect to Corps Calleux
        try:
            from server.extensions import registry
            if registry.corps_calleux and _left_hemisphere and _right_hemisphere:
                registry.corps_calleux.set_hemispheres(_left_hemisphere, _right_hemisphere)
                registry.left_hemisphere = _left_hemisphere
                registry.right_hemisphere = _right_hemisphere
                logging.info("[Models] ✅ Hémisphères connectés au Corps Calleux")
        except Exception as e:
            logging.warning(f"[Models] Corps Calleux connection: {e}")
        
        # Store model state
        _models_state = {
            "left": {
                "path": left_path,
                "name": os.path.basename(left_path) if left_path else None,
                "method": method,
                "loaded": True
            },
            "right": {
                "path": actual_right_path,
                "name": os.path.basename(actual_right_path) if actual_right_path else None,
                "method": method,
                "loaded": True
            },
            "is_split_mode": split_mode,
            "corps_calleux": {"total_cycles": 0}
        }
        
        return {
            "status": "ok",
            "message": "Modèles chargés avec succès",
            "left": {"loaded": _left_hemisphere is not None},
            "right": {"loaded": _right_hemisphere is not None},
            "is_split_mode": split_mode
        }
        
    except Exception as e:
        logging.error(f"[Models] Erreur chargement: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/models/unload")
async def models_unload():
    """Unload all models"""
    global _left_hemisphere, _right_hemisphere, _models_state
    
    try:
        if _left_hemisphere:
            _left_hemisphere.unload()
            _left_hemisphere = None
        
        if _right_hemisphere:
            _right_hemisphere.unload()
            _right_hemisphere = None
        
        _models_state = {
            "left": None,
            "right": None,
            "is_split_mode": False,
            "corps_calleux": {"total_cycles": 0}
        }
        
        # Disconnect from Corps Calleux
        try:
            from server.extensions import registry
            if registry.corps_calleux:
                registry.corps_calleux.left = None
                registry.corps_calleux.right = None
        except:
            pass
        
        return {"status": "ok", "message": "Modèles déchargés"}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/models/lmstudio/check")
async def models_lmstudio_check(request: Request):
    """Check LM Studio connection"""
    try:
        import httpx
        
        data = await request.json()
        url = data.get("url", _lmstudio_url)
        
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{url}/models")
            
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("data", [])
                return {
                    "status": "ok",
                    "models": [{"id": m.get("id")} for m in models]
                }
            else:
                return {"status": "error", "error": f"Connection failed: {response.status_code}"}
                
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/models/keys/save")
async def models_keys_save(request: Request):
    """Save API keys"""
    try:
        data = await request.json()
        
        keys_file = Path("storage/config/api_keys.json")
        keys_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(keys_file, "w", encoding="utf-8") as f:
            json.dump({
                "gemini": data.get("gemini", ""),
                "groq": data.get("groq", ""),
                "openrouter": data.get("openrouter", "")
            }, f, indent=2)
        
        return {"status": "ok"}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}
