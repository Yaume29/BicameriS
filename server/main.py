"""
Diadikos & Palladion
"""

import asyncio
import logging
import signal
import socket
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).parent.parent.absolute()

from server.extensions import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("[DIADIKOS] Séquence d'amorçage initiée...")
    
    from core.system.config_manager import get_config
    config = get_config()
    is_initialized = config.config.system.initialized
    persistent_autothink = config.config.system.persistent_autothink
    
    models_loaded = False
    if is_initialized and persistent_autothink:
        try:
            from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
            left = get_left_hemisphere()
            right = get_right_hemisphere()
            if left and right:
                models_loaded = True
                logging.info("[DIADIKOS] ✅ Modèles chargés (mode persistant)")
        except:
            pass

    try:
        from core.system.switchboard import get_switchboard
        registry.switchboard = get_switchboard()
        if not is_initialized:
            registry.switchboard.toggle("autonomous_loop", False)
            registry.switchboard.toggle("auto_scaffolding_full", False)
        logging.info("[DIADIKOS] ✅ Switchboard initialisé")
    except Exception as e:
        logging.warning(f"⚠️ Switchboard non disponible: {e}")

    if is_initialized:
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

        try:
            from core.cognition.corps_calleux import CorpsCalleux
            registry.corps_calleux = CorpsCalleux()
            
            if models_loaded:
                from server.routes.api_models import get_left_hemisphere, get_right_hemisphere
                left = get_left_hemisphere()
                right = get_right_hemisphere()
                if left and right:
                    registry.corps_calleux.set_hemispheres(left, right)
                    logging.info("[DIADIKOS] ✅ Hémisphères connectés au Corps Calleux")
            
            if persistent_autothink and models_loaded:
                registry.switchboard.toggle("autonomous_loop", True)
                logging.info("[DIADIKOS] 🔄 Boucle autonome activée (mode persistant)")
            
        except Exception as e:
            logging.warning(f"⚠️ Corps Calleux non disponible: {e}")

        try:
            from core.system.telemetry import get_telemetry
            await get_telemetry().start()
            logging.info("[DIADIKOS] ✅ Telemetry started")
        except Exception as e:
            logging.warning(f"⚠️ Telemetry non disponible: {e}")

        try:
            from core.system.sensory_buffer import get_sensory_buffer
            await get_sensory_buffer().start()
            logging.info("[DIADIKOS] ✅ SensoryBuffer (Data Hose) démarré")
        except Exception as e:
            logging.warning(f"⚠️ SensoryBuffer non disponible: {e}")

        try:
            from core.system.kernel_scheduler import init_kernel_scheduler
            registry.scheduler = init_kernel_scheduler(
                switchboard=registry.switchboard,
                corps_calleux=registry.corps_calleux,
                conductor=registry.conductor,
                entropy=registry.entropy,
            )
            await registry.scheduler.start()
            logging.info("[DIADIKOS] ⏱️ Horloge Maître démarrée")
        except Exception as e:
            logging.error(f"💀 ÉCHEC CRITIQUE - Kernel Scheduler: {e}")

        logging.info("[DIADIKOS] Système en ligne (initialisé)")
    else:
        logging.info("[DIADIKOS] ⚠️ Système en mode inerte - cliquez sur INITIALISER pour démarrer")

    yield

    from core.system.config_manager import get_config
    config = get_config()
    is_initialized = config.config.system.initialized
    
    logging.info("[DIADIKOS] ═══ EXTINCTION PROPRE DU SYSTÈME ═══")

    if hasattr(registry, "corps_calleux") and registry.corps_calleux:
        try:
            logging.info("[DIADIKOS] 🛏️ Appel du sommeil gracieux...")
            sleep_result = registry.corps_calleux.sleep(target_mode="arrêt")
            logging.info(f"[DIADIKOS] {sleep_result.get('message', 'Sommeil terminé')}")
        except Exception as e:
            logging.warning(f"⚠️ Erreur sommeil Corps Calleux: {e}")

    if hasattr(registry, "scheduler") and registry.scheduler:
        try:
            await registry.scheduler.stop()
            logging.info("[DIADIKOS] ✅ Scheduler arrêté proprement")
        except Exception as e:
            logging.warning(f"⚠️ Erreur scheduler.stop: {e}")

    try:
        import importlib.util
        from pathlib import Path
        module_path = str(BASE_DIR / "core" / "lab" / "modules" / "2_EditeurSpecialiste" / "executor.py")
        spec = importlib.util.spec_from_file_location("editeur_executor", module_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            executor = mod.get_executor()
            if executor:
                logging.info("[DIADIKOS] ✅ Executor arrêté")
    except Exception as e:
        logging.warning(f"⚠️ Erreur executor shutdown: {e}")

    try:
        from core.system.sensory_buffer import get_sensory_buffer
        await get_sensory_buffer().stop()
        logging.info("[DIADIKOS] ✅ SensoryBuffer arrêté")
    except Exception:
        pass

    try:
        from core.system.telemetry import get_telemetry
        await get_telemetry().stop()
        logging.info("[DIADIKOS] ✅ Telemetry arrêté")
    except Exception:
        pass

    if registry.inference_manager:
        try:
            registry.inference_manager.guillotine_all()
            logging.info("[DIADIKOS] ✅ InferenceManager guillotiné")
        except:
            pass

    try:
        from core.agents.super_agent import get_super_agent
        super_agent = get_super_agent()
        if super_agent:
            super_agent.disable()
            logging.info("[DIADIKOS] ✅ SuperAgent désactivé")
    except Exception:
        pass

    try:
        from core.system.instance_lock import get_instance_lock
        lock = get_instance_lock()
        lock.release()
        logging.info("[DIADIKOS] ✅ Instance lock libéré")
    except Exception:
        pass
    
    logging.info("[DIADIKOS] ═══ ARRÊT TERMINÉ ═══")


app = FastAPI(
    title="BicameriS - Diadikos & Palladion",
    description="Kernel cognitif bicaméral",
    version="1.0.0.6a",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://localhost:8000", "http://127.0.0.1:8000", "http://0.0.0.0:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = BASE_DIR / "web" / "static"
static_router = APIRouter()

@static_router.get("/static/{file_path:path}", name="static")
async def serve_static(file_path: str):
    file_path_obj = static_dir / file_path
    if file_path_obj.exists() and file_path_obj.is_file():
        return FileResponse(str(file_path_obj))
    return FileResponse(str(static_dir / "index.html"), status_code=404)

app.include_router(static_router)

templates = Jinja2Templates(directory=str(BASE_DIR / "web/templates"))

from server.routes import views, api_hardware, api_cognitive, api_inference, api_system
from server.routes import api_inception, api_laboratoire, api_research, api_identity, api_launch, api_models, api_chat, api_dashboard, api_knowledge, api_agents, api_lab
from server.routes import api_skills, api_specialist_editor

views.set_templates(templates)

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
app.include_router(api_agents.router, prefix="/api")
app.include_router(api_lab.router, prefix="/api")
app.include_router(api_skills.router, prefix="/api")
app.include_router(api_specialist_editor.router, prefix="/api")
app.include_router(views.router)


@app.get("/api/stats")
async def legacy_stats():
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
    try:
        from core.hardware.entropy_generator import get_entropy_generator
        entropy = get_entropy_generator()
        return {"pulse": entropy.get_pulse(), "mood": entropy._interpret_mood(entropy.last_pulse)}
    except Exception:
        return {"pulse": 0.5, "mood": "UNKNOWN"}


@app.get("/api/agents")
async def legacy_agents():
    return {"agents": [{"name": "Conductor", "status": "active"}]}


@app.get("/api/agents/providers")
async def legacy_agent_providers():
    return {"providers": []}


@app.get("/api/memory/stats")
async def legacy_memory_stats():
    try:
        from core.system.traumatic_memory import get_traumatic_memory
        return get_traumatic_memory().get_stats()
    except Exception:
        return {"total": 0}


@app.get("/api/memory/summary")
async def legacy_memory_summary(hours: int = 24):
    return {"summary": []}


@app.get("/api/think/history")
async def legacy_think_history(limit: int = 10):
    try:
        if registry.conductor and hasattr(registry.conductor, 'task_history'):
            return registry.conductor.task_history[-limit:]
        return []
    except Exception:
        return []


@app.websocket("/ws/neural")
async def websocket_neural(websocket: WebSocket):
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


def check_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        if check_port_available(port):
            return port
    raise RuntimeError(f"No available ports found in range {start_port}-{start_port + max_attempts}")


if __name__ == "__main__":
    import uvicorn

    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        logging.info(f"[DIADIKOS] Signal {signal_name} reçu, préparation de l'arrêt...")
        shutdown_event.set()
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logging.info("[DIADIKOS] Signal handlers enregistrés")
    except Exception as e:
        logging.warning(f"[DIADIKOS] Impossible d'enregistrer les signal handlers: {e}")

    try:
        from core.system.instance_lock import get_instance_lock
        lock = get_instance_lock()
        lock_status = lock.acquire_or_sleep()

        if not lock_status.acquired:
            print(f"[DIADIKOS] ⚠️ Another instance is running (PID: {lock_status.owner_pid})")
            print(f"[DIADIKOS] Entering sleep mode... ({lock_status.wait_time:.0f}s)")
            if lock.wait_for_wake(timeout=lock_status.wait_time):
                print("[DIADIKOS] Wake signal received! Starting up...")
            else:
                print("[DIADIKOS] Timeout exceeded. Force starting anyway...")
    except ImportError:
        print("[DIADIKOS] Instance lock not available, starting without protection")
    except Exception as e:
        print(f"[DIADIKOS] Lock error: {e}, starting anyway")

    port = 8000
    max_wait = 30
    start_time = time.time()

    while not check_port_available(port) and time.time() - start_time < max_wait:
        elapsed = int(time.time() - start_time)
        print(f"[DIADIKOS] ⏳ Port {port} busy. Waiting... ({elapsed}s/{max_wait}s)")
        time.sleep(2)

    if not check_port_available(port):
        try:
            port = find_available_port(port + 1)
            print(f"[DIADIKOS] 🔄 Falling back to port {port}")
        except RuntimeError as e:
            print(f"[DIADIKOS] ❌ {e}")
            exit(1)

    print(f"[DIADIKOS] 🚀 Starting server on port {port}")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        workers=1,
        timeout_graceful_shutdown=10,
        timeout_keep_alive=5
    )
