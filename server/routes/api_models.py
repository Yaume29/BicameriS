"""
API Models Routes
================
Model scanning and loading endpoints
"""

import os
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


@router.get("/models/default-path")
async def models_default_path():
    """Get default model scan path"""
    # Common LM Studio paths on Windows
    possible_paths = [
        "C:\\Users\\{}\\.cache\\lm-studio\\models".format(os.getlogin()),
        "C:\\Users\\{}\\AppData\\Local\\lm-studio\\models".format(os.getlogin()),
        "D:\\LMStudio\\models",
        "D:\\LLM\\models",
    ]
    
    for p in possible_paths:
        if os.path.exists(p):
            return {"path": p}
    
    return {"path": "C:\\Users\\"}


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
        
        # Start scanning in background thread
        result = scanner.scan(path)
        return result
        
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/models/scan-usual")
async def models_scan_usual():
    """Scan usual model folders"""
    try:
        import os
        username = os.getlogin()
        
        usual_paths = [
            f"C:\\Users\\{username}\\.cache\\lm-studio\\models",
            f"C:\\Users\\{username}\\AppData\\Local\\lm-studio\\models",
            f"C:\\Users\\{username}\\.cache\\huggingface\\hub",
            "D:\\LMStudio\\models",
            "D:\\LLM\\models",
            "D:\\models",
        ]
        
        from core.hardware.model_scanner import get_scanner
        scanner = get_scanner()
        
        # Find first existing path
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
        
        return {
            "left": {
                "loaded": left is not None,
                "model_name": left.get("name") if left else None,
                "path": left.get("path") if left else None
            },
            "right": {
                "loaded": right is not None,
                "model_name": right.get("name") if right else None,
                "path": right.get("path") if right else None
            },
            "is_split_mode": _models_state.get("is_split_mode", False),
            "corps_calleux": _models_state.get("corps_calleux", {"total_cycles": 0})
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
    """Load models"""
    try:
        data = await request.json()
        
        left_path = data.get("left_path")
        right_path = data.get("right_path")
        method = data.get("method", "local")
        split_mode = data.get("split_mode", False)
        lmstudio_url = data.get("lmstudio_url", _lmstudio_url)
        
        # Validate paths for local method
        if method == "local":
            if left_path and not os.path.exists(left_path):
                return {"status": "error", "error": f"Modèle gauche introuvable: {left_path}"}
            if right_path and right_path != left_path and not os.path.exists(right_path):
                return {"status": "error", "error": f"Modèle droit introuvable: {right_path}"}
        
        # Store model state
        _models_state["left"] = {
            "path": left_path,
            "name": os.path.basename(left_path) if left_path else None,
            "method": method,
            "loaded": True
        }
        
        _models_state["right"] = {
            "path": right_path if not split_mode else left_path,
            "name": os.path.basename(right_path) if right_path else None,
            "method": method,
            "loaded": True
        }
        
        _models_state["is_split_mode"] = split_mode
        
        return {"status": "ok", "message": "Modèles configurés avec succès"}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/models/lmstudio/check")
async def models_lmstudio_check(request: Request):
    """Check LM Studio connection"""
    try:
        import httpx
        
        data = await request.json()
        url = data.get("url", _lmstudio_url)
        
        # Try to connect to LM Studio API
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
        
        # Store keys in config file
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
