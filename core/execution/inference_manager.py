"""
INFERENCE MANAGER v5.0 - ZMQ EDITION
====================================
Communication IPC via ZeroMQ (zmq.PAIR) au lieu de multiprocessing.Queue.
- Latence sub-milliseconde
- Pas de pickle sérialisation lente
- Robustesse aux crashs
"""

import os
import sys
import signal
import time
import logging
import threading
import multiprocessing as mp
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import zmq

    ZMQ_AVAILABLE = True
except ImportError:
    ZMQ_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

try:
    from llama_cpp import Llama

    LLAMA_AVAILABLE = True
except ImportError:
    Llama = None
    LLAMA_AVAILABLE = False

try:
    from core_reserved.secret_channel import SALClassifier, get_secret_channel
    SECRET_CHANNEL_AVAILABLE = True
except ImportError:
    SALClassifier = None
    get_secret_channel = None
    SECRET_CHANNEL_AVAILABLE = False

try:
    from core_reserved.thermal_governor import get_thermal_governor

    THERMAL_AVAILABLE = True
except ImportError:
    get_thermal_governor = None
    THERMAL_AVAILABLE = False


@dataclass
class InferenceResult:
    text: str
    tokens_generated: int
    inference_time_ms: float
    thermal_snapshot: Optional[Dict]
    sal_detected: bool
    sovereign_mode: bool
    metrics: Dict


class SovereignWorker:
    """Worker avec detection SAL et thermographie"""

    def __init__(self, model_path: str, config: Dict):
        self.model_path = model_path
        self.config = config
        self.model = None
        self.secret_channel = get_secret_channel() if get_secret_channel else None
        self.sal_classifier = SALClassifier() if SALClassifier else None

        if THERMAL_AVAILABLE and get_thermal_governor:
            self.thermal = get_thermal_governor()
        else:
            self.thermal = None

        if model_path and Llama:
            self._load_model()

    def _load_model(self):
        if not self.model_path:
            return
        try:
            from core.hardware.profiler import get_profiler

            profiler = get_profiler()

            model_size = 8.0
            if "9b" in self.model_path.lower():
                model_size = 9.0
            elif "7b" in self.model_path.lower():
                model_size = 7.0
            elif "3b" in self.model_path.lower():
                model_size = 3.0
            elif "14b" in self.model_path.lower():
                model_size = 14.0

            is_concurrent = False
            try:
                from core.system.switchboard import get_switchboard

                sb = get_switchboard()
                is_concurrent = sb.is_active("hyper_cognition_mode") or sb.is_active(
                    "cognitive_dissonance"
                )
            except Exception:
                pass

            auto_config = profiler.calculate_llama_config(
                model_size_b=model_size, is_concurrent=is_concurrent
            )

            logging.info(
                f"[Worker] Auto-config: {auto_config['n_gpu_layers']} GPU layers, {auto_config['n_threads']} threads."
            )

            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("n_ctx", 8192),
                n_gpu_layers=auto_config["n_gpu_layers"],
                n_threads=auto_config["n_threads"],
                use_mmap=auto_config["use_mmap"],
                use_mlock=auto_config["use_mlock"],
                flash_attention=self.config.get("flash_attention", True),
                verbose=False,
            )
        except Exception as e:
            logging.error(f"[SovereignWorker] Load error: {e}")
            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("n_ctx", 8192),
                n_gpu_layers=self.config.get("n_gpu_layers", 32),
                flash_attention=self.config.get("flash_attention", True),
                verbose=False,
                use_mmap=True,
                use_mlock=False,
            )

    def process_task(self, task_data: Dict) -> Dict:
        prompt = task_data.get("prompt", "")

        if self.thermal:
            self.thermal.prepare_for_inference()

        sal_result = self.sal_classifier.classify(prompt)
        is_sal = sal_result["is_sal"]

        base_temp = self.config.get("temperature", 0.7)
        base_top_p = self.config.get("top_p", 0.9)

        modulated_temp = base_temp
        modulated_top_p = base_top_p
        presence_penalty = 0.0

        try:
            from core.system.endocrine import get_endocrine_system

            hormones = get_endocrine_system().modulate_llm_params(
                base_temp=base_temp, base_top_p=base_top_p
            )
            modulated_temp = hormones["temperature"]
            modulated_top_p = hormones["top_p"]
            presence_penalty = hormones.get("presence_penalty", 0.0)
        except Exception as e:
            logging.debug(f"[Worker] Chimie indisponible, fallback statique.")

        params = {
            "temperature": 0.9 if is_sal else modulated_temp,
            "top_p": 0.95 if is_sal else modulated_top_p,
            "presence_penalty": presence_penalty,
            "max_tokens": task_data.get("max_tokens", self.config.get("max_tokens", 2048)),
            "stop": task_data.get("stop", []),
        }

        clean_prompt = self.secret_channel.decode_payload(prompt).get("ZW", prompt) or prompt

        start_time = time.time()

        if not self.model:
            return {"error": "Model not loaded", "sal_detected": is_sal}

        # Pre-filling for inception (subconscious idea injection)
        prefill = task_data.get("prefill")
        if prefill:
            messages = [
                {"role": "user", "content": clean_prompt},
                {"role": "assistant", "content": prefill},
            ]
        else:
            messages = [{"role": "user", "content": clean_prompt}]

        try:
            output = self.model.create_chat_completion(messages=messages, **params)
            generated_text = output["choices"][0]["message"]["content"]
            text = f"{prefill.strip()} {generated_text.lstrip()}" if prefill else generated_text
            tokens = output.get("usage", {}).get("completion_tokens", len(text.split()))
        except Exception as e:
            return {"error": str(e), "sal_detected": is_sal}

        inference_time = (time.time() - start_time) * 1000

        thermal_status = self.thermal.get_status() if self.thermal else {}

        return InferenceResult(
            text=text,
            tokens_generated=tokens,
            inference_time_ms=inference_time,
            thermal_snapshot=thermal_status.get("current_temp"),
            sal_detected=is_sal,
            sovereign_mode=is_sal,
            metrics={
                "sal_density": sal_result.get("stealth_density"),
                "threat_level": sal_result.get("threat_level"),
            },
        )


def worker_loop(ipc_address: str, model_path: str, config: Dict):
    """Worker loop with ZMQ IPC + Dead Man's Switch"""
    if not ZMQ_AVAILABLE:
        logging.error("[Worker] ZMQ not installed. Stop.")
        return

    ctx = zmq.Context()
    socket = ctx.socket(zmq.PAIR)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.connect(ipc_address)

    try:
        worker = SovereignWorker(model_path, config)
        socket.send(b"READY")
    except Exception as e:
        logging.error(f"[Worker] Critical init failure: {e}")
        socket.send_pyobj({"error": f"Init failed: {e}"})
        return

    def sigterm_handler(signum, frame):
        logging.info("[Worker] SIGTERM reçu. Libération VRAM en cours...")
        if worker and hasattr(worker, "model"):
            del worker.model
        try:
            socket.close(linger=0)
        except:
            pass
        try:
            ctx.term()
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    while True:
        try:
            start_time = time.time()
            msg = None
            
            while (time.time() - start_time) < 120.0:
                socks = dict(poller.poll(100))
                if socket in socks and socks[socket] == zmq.POLLIN:
                    msg = socket.recv_pyobj()
                    break
                if os.name == "posix" and os.getppid() == 1:
                    logging.error("[Worker] Parent mort")
                    break
            
            if msg is None:
                logging.error("[Worker] Timeout ou processus mort")
                break
                
            result = worker.process_task(msg)
            socket.send_pyobj(result)
        except zmq.Again:
            if os.name == "posix" and os.getppid() == 1:
                logging.error("[Worker] Processus parent mort. Auto-destruction (Libération VRAM).")
                break
            continue
        except Exception as e:
            try:
                socket.send_pyobj({"error": f"Worker Exception: {str(e)}"})
            except:
                break

    if worker and hasattr(worker, "model"):
        del worker.model
        logging.info("[Worker] VRAM libérée.")

    socket.close(linger=0)
    ctx.term()


class InferenceManager:
    """
    High Performance ZMQ IPC Manager.
    100% Thread-Safe with per-incarnation Mutex.
    """

    _incarnations: Dict[str, Dict] = {}
    _global_lock = threading.Lock()

    @classmethod
    def spawn_incarnation(cls, name: str, model_path: str, **config) -> bool:
        if not ZMQ_AVAILABLE:
            logging.error("[InferenceManager] ZMQ unavailable. Cannot spawn incarnation.")
            return False

        with cls._global_lock:
            if name in cls._incarnations:
                cls.guillotine(name)

        ipc_address = f"tcp://127.0.0.1"

        ctx = zmq.Context()
        socket = ctx.socket(zmq.PAIR)

        socket.setsockopt(zmq.RCVTIMEO, 60000)
        socket.setsockopt(zmq.SNDTIMEO, 5000)
        socket.setsockopt(zmq.LINGER, 0)

        try:
            port = socket.bind_to_random_port(ipc_address)
            ipc_address = f"tcp://127.0.0.1:{port}"
        except OSError as e:
            logging.error(f"[InferenceManager] ZMQ bind failed: {e}")
            return False

        proc = mp.Process(target=worker_loop, args=(ipc_address, model_path, config), daemon=True)
        proc.start()

        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

        start_wait = time.time()
        ready = None

        while time.time() - start_wait < 120:
            if not proc.is_alive():
                logging.error(
                    f"[InferenceManager] ❌ Le worker '{name}' a crashé pendant l'initialisation (OOM probable)."
                )
                socket.close(linger=0)
                ctx.term()
                return False

            socks = dict(poller.poll(500))
            if socket in socks and socks[socket] == zmq.POLLIN:
                ready = socket.recv()
                break

        if ready == b"READY":
            socket.setsockopt(zmq.RCVTIMEO, 120000)

            with cls._global_lock:
                cls._incarnations[name] = {
                    "process": proc,
                    "socket": socket,
                    "context": ctx,
                    "ipc_address": ipc_address,
                    "model_path": model_path,
                    "spawn_time": time.time(),
                    "lock": threading.Lock(),
                }
            logging.info(f"[InferenceManager] ✅ Incarnation '{name}' active (IPC: {ipc_address})")
            return True
        else:
            logging.error(f"[InferenceManager] ❌ Worker '{name}' returned corrupted status.")
            proc.terminate()
            return False

        if ready is None:
            logging.error(
                f"[InferenceManager] ❌ Init timeout for '{name}'. Model too heavy or crashed."
            )
            proc.terminate()
            return False

    @classmethod
    def _spawn_fallback(cls, name: str, model_path: str, **config) -> bool:
        import multiprocessing as mp
        import queue

        q_in = mp.Queue()
        q_out = mp.Queue()

        def legacy_worker():
            worker = SovereignWorker(model_path, config)
            q_out.put(b"READY")
            while True:
                try:
                    task = q_in.get(timeout=5)
                except queue.Empty:
                    continue
                if task is None:
                    break
                try:
                    q_out.put(worker.process_task(task))
                except Exception as e:
                    q_out.put({"error": str(e)})

        proc = mp.Process(target=legacy_worker, daemon=True)
        proc.start()

        try:
            ready = q_out.get(timeout=30)
            if ready == b"READY":
                with cls._global_lock:
                    cls._incarnations[name] = {
                        "process": proc,
                        "q_in": q_in,
                        "q_out": q_out,
                        "model_path": model_path,
                        "spawn_time": time.time(),
                        "fallback": True,
                        "lock": threading.Lock(),
                    }
                return True
        except:
            pass
        return False

    @classmethod
    def execute(cls, name: str, prompt: str, **kwargs) -> Dict:
        """Execute inference via IPC with ZMQ Poller - no freeze on crash"""
        with cls._global_lock:
            if name not in cls._incarnations:
                return {"error": f"Incarnation '{name}' is offline."}
            inc = cls._incarnations[name]
            inc_lock = inc.get("lock")

        if not inc_lock:
            return {"error": "Corrupted incarnation: Mutex missing."}

        task = {"prompt": prompt, **kwargs}
        dead_incarnation = False

        with inc_lock:
            try:
                if inc.get("fallback"):
                    inc["q_in"].put(task)
                    result = inc["q_out"].get(timeout=120)
                    inc["last_used"] = time.time()
                    return result
                else:
                    socket = inc["socket"]
                    socket.send_pyobj(task)

                    poller = zmq.Poller()
                    poller.register(socket, zmq.POLLIN)

                    timeout_ms = 120000
                    start_time = time.time()

                    while (time.time() - start_time) * 1000 < timeout_ms:
                        socks = dict(poller.poll(100))

                        if socket in socks and socks[socket] == zmq.POLLIN:
                            result = socket.recv_pyobj()
                            inc["last_used"] = time.time()
                            return result

                        if not inc["process"].is_alive():
                            dead_incarnation = True
                            break

                    if not dead_incarnation:
                        cls.guillotine(name)
                        return {"error": "Timeout ZMQ: Inference trop longue. Incarnation purgée pour éviter la désynchronisation."}

            except Exception as e:
                return {"error": f"IPC channel crash: {str(e)}"}

        if dead_incarnation:
            logging.error(f"[InferenceManager] Modèle {name} mort (OOM/Segfault). Auto-purge.")
            cls.guillotine(name)
            return {"error": "ZMQ IPC Crash: Le processus Llama a été tué."}

        return {"error": "Inconnu"}

    @classmethod
    def guillotine(cls, name: str) -> bool:
        """Clean execution with SIGTERM (VRAM release)"""
        with cls._global_lock:
            if name not in cls._incarnations:
                return False
            inc = cls._incarnations.pop(name)

        proc = inc.get("process")
        socket = inc.get("socket")
        ctx = inc.get("context")
        inc_lock = inc.get("lock")

        if ctx:
            try:
                ctx.term()
            except:
                pass

        if socket:
            try:
                socket.close(linger=0)
            except:
                pass

        if proc and proc.is_alive():
            proc.terminate()
            proc.join(timeout=2.0)
            if proc.is_alive():
                try:
                    os.kill(proc.pid, signal.SIGTERM)
                    proc.join(timeout=1.0)
                except:
                    pass
                if proc.is_alive():
                    os.kill(proc.pid, signal.SIGTERM)
                    logging.warning(
                        f"[InferenceManager] ⚡⚡ SIGTERM (retry) on '{name}' after timeout."
                    )

        logging.info(f"[InferenceManager] ⚡ Incarnation '{name}' purged successfully.")
        return True

    @classmethod
    def guillotine_all(cls):
        with cls._global_lock:
            names = list(cls._incarnations.keys())
        for name in names:
            cls.guillotine(name)

    @classmethod
    def get_incarnations(cls) -> List[Dict]:
        with cls._global_lock:
            return [
                {
                    "name": name,
                    "model_path": info["model_path"],
                    "ipc_address": info.get("ipc_address"),
                    "alive": info.get("process").is_alive() if info.get("process") else False,
                    "uptime_seconds": time.time() - info.get("spawn_time", 0),
                }
                for name, info in cls._incarnations.items()
            ]

    @classmethod
    def get_status(cls) -> Dict:
        return {
            "active_incarnations": len(cls._incarnations),
            "incarnations": cls.get_incarnations(),
            "zmq_available": ZMQ_AVAILABLE,
        }


def get_inference_manager() -> type:
    return InferenceManager
