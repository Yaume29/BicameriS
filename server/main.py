"""
BICAMERIS - Server Main
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

logging.basicConfig(level=logging.INFO)

from server.extensions import registry


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events with Fail-Fast"""
    logging.info("[Bicameris] Séquence d'amorçage initiée...")

    # 0. Switchboard (Thread-safe state manager)
    try:
        from core.system.switchboard import get_switchboard

        registry.switchboard = get_switchboard()
        logging.info("[Bicameris] ✅ Switchboard initialisé")
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

        registry.inference_manager = InferenceManager
    except Exception as e:
        logging.error(f"💀 ÉCHEC CRITIQUE - InferenceManager: {e}")
        raise RuntimeError("Moteur d'inférence indisponible. Arrêt du système.")

    # Optional: Corps Calleux (for autonomous thinking)
    try:
        from core.cognition.corps_calleux import CorpsCalleux

        registry.corps_calleux = CorpsCalleux()
        logging.info("[Bicameris] ✅ Corps Calleux chargé")
    except Exception as e:
        logging.warning(f"⚠️ Corps Calleux non disponible: {e}")

    # Note: Autonomous Thinker is now integrated into CorpsCalleux
    # Controlled via Switchboard "autonomous_loop" switch

    # Telemetry (must be started before logging)
    try:
        from core.system.telemetry import get_telemetry

        await get_telemetry().start()
        logging.info("[Bicameris] ✅ Telemetry started")
    except Exception as e:
        logging.warning(f"⚠️ Telemetry non disponible: {e}")

    try:
        from core.system.sensory_buffer import get_sensory_buffer

        await get_sensory_buffer().start()
        logging.info("[Bicameris] ✅ SensoryBuffer (Data Hose) démarré")
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
        logging.info("[Bicameris] ⏱️ Horloge Maître démarrée")
    except Exception as e:
        logging.error(f"💀 ÉCHEC CRITIQUE - Kernel Scheduler: {e}")

    logging.info("[Bicameris] Système en ligne.")

    yield

    logging.info("[Bicameris] Extinction propre des sous-systèmes...")
    # Cleanup
    if registry.inference_manager:
        try:
            registry.inference_manager.guillotine_all()
        except:
            pass


# Create FastAPI app
app = FastAPI(
    title="Bicameris",
    description="Kernel cognitif bicaméral - Hope 'n Mind",
    version="4.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
except:
    pass

# Templates
templates = Jinja2Templates(directory="web/templates")

# Import and include routes
from server.routes import views, api_hardware, api_cognitive, api_inference, api_system

# Set templates for views
views.set_templates(templates)

# Include routes
app.include_router(views.router)
app.include_router(api_hardware.router)
app.include_router(api_cognitive.router)
app.include_router(api_inference.router)
app.include_router(api_system.router)


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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
