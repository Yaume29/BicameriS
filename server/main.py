"""
Diadikos & Palladion - Server Main
=======================
FastAPI application - Hope 'n Mind
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()

from server.extensions import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with Fail-Fast"""
    logging.info("[Diadikos] Séquence d'amorçage initiée...")

    # 0. Switchboard (Thread-safe state manager)
    try:
        from core.system.switchboard import get_switchboard

        registry.switchboard = get_switchboard()
        logging.info("[Diadikos] ✅ Switchboard initialisé")
    except Exception as e:
        logging.warning(f"⚠️ Switchboard non disponible: {e}")

    # Hardware (Optional - can run blind)
    try:
        from core.hardware.thermal_governor import get_thermal_governor

        registry.thermal = get_thermal_governor()
    except Exception as e:
        logging.warning(f"⚠️ Sonde Thermique non disponible: {e}")

    try:
        from core.hardware.entropy_generator import get_entropy_generator

        registry.entropy = get_entropy_generator()
    except Exception as e:
        logging.warning(f"⚠️ Entropy non disponible: {e}")

    # CRITICAL: Cognition & Inference (Fail-Fast) - MUST be before KernelScheduler
    try:
        from core.cognition.conductor import get_conductor

        registry.conductor = get_conductor()
    except Exception as e:
        logging.error(f"💀 ÉCHEC CRITIQUE - Conductor: {e}")
        raise RuntimeError("Kernel cognitif indisponible. Arrêt du système.")

    try:
        from core.execution.inference_manager import InferenceManager

        registry.inference_manager = InferenceManager()
    except Exception as e:
        logging.error(f"💀 ÉCHEC CRITIQUE - InferenceManager: {e}")
        raise RuntimeError("Moteur d'inférence indisponible. Arrêt du système.")

    # Optional: Corps Calleux (for autonomous thinking)
    try:
        from core.cognition.corps_calleux import CorpsCalleux

        registry.corps_calleux = CorpsCalleux()
        
        try:
            # Get hemispheres from API module (they're loaded when user selects models)
            from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
            left = get_left_hemisphere()
            right = get_right_hemisphere()
            if left and right:
                registry.corps_calleux.set_hemispheres(left, right)
                logging.info("[Diadikos] ✅ Hémisphères connectés au Corps Calleux")
            else:
                logging.info("[Diadikos] ℹ️ Hémisphères non chargés - configurez les modèles via /models")
        except ImportError:
            logging.info("[Diadikos] ℹ️ Corps Calleux créé (hémisphères à configurer via /models)")
    except Exception as e:
        logging.warning(f"⚠️ Corps Calleux non disponible: {e}")

    # Note: Autonomous Thinker is now integrated into CorpsCalleux
    # Controlled via Switchboard "autonomous_loop" switch

    # Telemetry (must be started before logging)
    try:
        from core.system.telemetry import get_telemetry

        await get_telemetry().start()
        logging.info("[Diadikos] ✅ Telemetry started")
    except Exception as e:
        logging.warning(f"⚠️ Telemetry non disponible: {e}")

    try:
        from core.system.sensory_buffer import get_sensory_buffer

        await get_sensory_buffer().start()
        logging.info("[Diadikos] ✅ SensoryBuffer (Data Hose) démarré")
    except Exception as e:
        logging.warning(f"⚠️ SensoryBuffer non disponible: {e}")

    # KernelScheduler (Master Clock) - MUST be after Conductor & Corps Calleux
    try:
        from core.system.kernel_scheduler import init_kernel_scheduler

        registry.scheduler = init_kernel_scheduler(
            switchboard=registry.switchboard,
            corps_calleux=registry.corps_calleux,
            conductor=registry.conductor,
            entropy=registry.entropy,
        )
        await registry.scheduler.start()
        logging.info("[Diadikos] ⏱️ Horloge Maître démarrée")
    except Exception as e:
        logging.error(f"💀 ÉCHEC CRITIQUE - Kernel Scheduler: {e}")

    logging.info("[Diadikos] Système en ligne.")

    yield

    logging.info("[Diadikos] Extinction propre des sous-systèmes...")

    if hasattr(registry, "scheduler") and registry.scheduler:
        try:
            await registry.scheduler.stop()
            logging.info("[Diadikos] ✅ Scheduler arrêté proprement")
        except Exception as e:
            logging.warning(f"⚠️ Erreur scheduler.stop: {e}")

    try:
        from core.system.sensory_buffer import get_sensory_buffer
        await get_sensory_buffer().stop()
        logging.info("[Diadikos] ✅ SensoryBuffer arrêté")
    except Exception:
        pass

    try:
        from core.system.telemetry import get_telemetry
        await get_telemetry().stop()
        logging.info("[Diadikos] ✅ Telemetry arrêté")
    except Exception:
        pass

    if registry.inference_manager:
        try:
            registry.inference_manager.guillotine_all()
        except:
            pass


# Create FastAPI app
app = FastAPI(
    title="BicameriS - Diadikos & Palladion",
    description="Kernel cognitif bicaméral - Hope 'n Mind",
    version="1.0.0.6a",
    lifespan=lifespan,
)

# CORS - Allow all localhost origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:8000", "http://127.0.0.1:8000", "http://0.0.0.0:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - using APIRouter for proper url_for support
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

static_dir = BASE_DIR / "web" / "static"

static_router = APIRouter()

@static_router.get("/static/{file_path:path}", name="static")
async def serve_static(file_path: str):
    """Static file endpoint"""
    file_path_obj = static_dir / file_path
    if file_path_obj.exists() and file_path_obj.is_file():
        return FileResponse(str(file_path_obj))
    return FileResponse(str(static_dir / "index.html"), status_code=404)

app.include_router(static_router)

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "web/templates"))

# Import and include routes
from server.routes import views, api_hardware, api_cognitive, api_inference, api_system
from server.routes import api_inception, api_laboratoire, api_research, api_identity, api_launch, api_models, api_chat, api_dashboard, api_knowledge, api_unified

# Set templates for views
views.set_templates(templates)

# Include routes
app.include_router(views.router)
app.include_router(api_hardware.router)
app.include_router(api_cognitive.router)
app.include_router(api_inference.router)
app.include_router(api_system.router)
app.include_router(api_inception.router, prefix="/api")
app.include_router(api_laboratoire.router, prefix="/api")
app.include_router(api_research.router, prefix="/api")
app.include_router(api_identity.router, prefix="/api")
app.include_router(api_launch.router, prefix="/api")
app.include_router(api_models.router, prefix="/api")
app.include_router(api_chat.router, prefix="/api")
app.include_router(api_dashboard.router, prefix="/api")
app.include_router(api_knowledge.router, prefix="/api")
app.include_router(api_unified.router, prefix="/api")


# ============ LEGACY ENDPOINTS (backwards compatibility) ============


@app.get("/api/stats")
async def legacy_stats():
    """Legacy stats endpoint"""
    try:
        from server.extensions import registry
        cycles = len(registry.corps_calleux.history) if registry.corps_calleux and hasattr(registry.corps_calleux, 'history') else 0
        return {
            "thinker": {"is_thinking": False, "cycles": cycles},
            "corps_calleux": {"connected": registry.corps_calleux is not None, "cycles": cycles}
        }
    except Exception:
        return {"thinker": {"is_thinking": False, "cycles": 0}, "corps_calleux": {"connected": False, "cycles": 0}}


@app.get("/api/logs")
async def legacy_logs(type: str = "all", limit: int = 100):
    """Legacy logs endpoint"""
    try:
        from core.system.telemetry import get_telemetry
        telemetry = get_telemetry()
        if telemetry:
            if type == "ERREUR":
                return [l for l in telemetry.buffer if l.get("type") == "ERREUR"][-limit:]
            return list(telemetry.buffer)[-limit:]
        return []
    except Exception:
        return []


@app.get("/api/logs_by_type")
async def legacy_logs_by_type():
    """Legacy logs by type endpoint"""
    try:
        from core.system.telemetry import get_telemetry
        telemetry = get_telemetry()
        if telemetry:
            by_type = {}
            for log in telemetry.buffer:
                log_type = log.get("type", "unknown")
                by_type[log_type] = by_type.get(log_type, 0) + 1
            return by_type
        return {}
    except Exception:
        return {}


@app.get("/api/entropy")
async def legacy_entropy():
    """Legacy entropy endpoint"""
    try:
        from core.hardware.entropy_generator import get_entropy_generator
        entropy = get_entropy_generator()
        return {"pulse": entropy.get_pulse(), "mood": entropy._interpret_mood(entropy.last_pulse)}
    except Exception:
        return {"pulse": 0.5, "mood": "UNKNOWN"}


@app.get("/api/agents")
async def legacy_agents():
    """Legacy agents endpoint"""
    return {"agents": [{"name": "Conductor", "status": "active"}]}


@app.get("/api/agents/providers")
async def legacy_agent_providers():
    """Legacy agent providers endpoint"""
    return {"providers": []}


@app.get("/api/memory/stats")
async def legacy_memory_stats():
    """Legacy memory stats endpoint"""
    try:
        from core.system.traumatic_memory import get_traumatic_memory
        return get_traumatic_memory().get_stats()
    except Exception:
        return {"total": 0}


@app.get("/api/memory/summary")
async def legacy_memory_summary(hours: int = 24):
    """Legacy memory summary endpoint"""
    return {"summary": []}


@app.get("/api/think/history")
async def legacy_think_history(limit: int = 10):
    """Legacy think history endpoint"""
    try:
        if registry.conductor and hasattr(registry.conductor, 'task_history'):
            return registry.conductor.task_history[-limit:]
        return []
    except Exception:
        return []


# ============ WEBSOCKETS - PUSH MODE (PASSIVE) ============


@app.websocket("/ws/neural")
async def websocket_neural(websocket: WebSocket):
    """Real-time neural state - PUSH mode with passive reads"""
    await websocket.accept()
    try:
        while True:
            if registry.thermal:
                status = registry.thermal.get_status_passive()
                await websocket.send_json({"type": "thermal", **status})

            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logging.info("WebSocket neural déconnecté proprement.")
    except Exception as e:
        logging.warning(f"WebSocket error (fermeture brutale): {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass


# ============ RUN ============

def check_port_available(port: int) -> bool:
    """Check if a port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")


if __name__ == "__main__":
    import uvicorn
    import time

    try:
        from core.system.instance_lock import get_instance_lock
        lock = get_instance_lock()
        lock_status = lock.acquire_or_sleep()

        if not lock_status.acquired:
            print(f"[Diadikos] ⚠️ Another instance is running (PID: {lock_status.owner_pid})")
            print(f"[Diadikos] Entering sleep mode... ({lock_status.wait_time:.0f}s)")
            if lock.wait_for_wake(timeout=lock_status.wait_time):
                print("[Diadikos] Wake signal received! Starting up...")
            else:
                print("[Diadikos] Timeout exceeded. Force starting anyway...")
    except ImportError:
        print("[Diadikos] Instance lock not available, starting without protection")
    except Exception as e:
        print(f"[Diadikos] Lock error: {e}, starting anyway")

    port = 8000
    max_wait = 30
    start_time = time.time()

    while not check_port_available(port) and time.time() - start_time < max_wait:
        elapsed = int(time.time() - start_time)
        print(f"[Diadikos] ⏳ Port {port} busy. Waiting... ({elapsed}s/{max_wait}s)")
        time.sleep(2)

    if not check_port_available(port):
        try:
            port = find_available_port(port + 1)
            print(f"[Diadikos] 🔄 Falling back to port {port}")
        except RuntimeError as e:
            print(f"[Diadikos] ❌ {e}")
            exit(1)

    print(f"[Diadikos] 🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
