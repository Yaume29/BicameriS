"""
INFERENCE MANAGER v1.0.0.6a - TRANSIENT REQ > BOUND ROUTER
===========================================================
Architecture ZMQ optimisée :
- Worker: BIND ROUTER (persistent, gère les identity frames)
- Manager: TRANSIENT REQ (éphémère par requête, état propre)
- Avantages: Zero race condition, crash-resilient, stateless client
"""

import os
import sys
import signal
import time
import logging
import threading
import multiprocessing as mp
import orjson
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import zmq

    ZMQ_AVAILABLE = True
except ImportError:
    zmq = None
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
    from core.execution.secret_channel import SALClassifier, get_secret_channel

    SECRET_CHANNEL_AVAILABLE = True
except ImportError:
    SALClassifier = None
    get_secret_channel = None
    SECRET_CHANNEL_AVAILABLE = False

try:
    from core.hardware.thermal_governor import get_thermal_governor

    THERMAL_AVAILABLE = True
except ImportError:
    get_thermal_governor = None
    THERMAL_AVAILABLE = False

IPC_DIR = (
    Path("/tmp/bicameris_ipc")
    if os.name == "posix"
    else Path(os.environ.get("TEMP", "C:\\TEMP")) / "bicameris_ipc"
)


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
            alloc = profiler.calculate_allocation(model_size)

            self.model = Llama(
                model_path=self.model_path,
                n_ctx=self.config.get("n_ctx", 4096),
                n_gpu_layers=alloc.get("n_gpu_layers", 0),
                n_threads=alloc.get("n_threads", 4),
                use_mlock=self.config.get("use_mlock", False),
                use_mmap=self.config.get("use_mmap", True),
                verbose=False,
            )
            logging.info(f"[SovereignWorker] Modèle chargé: {self.model_path}")
        except Exception as e:
            logging.error(f"[SovereignWorker] Erreur chargement modèle: {e}")
            self.model = None

    def process_task(self, task: Dict) -> Dict[str, Any]:
        """Traitement synchrone - retourne le résultat complet"""
        if not self.model:
            return {"error": "Modèle non chargé"}

        prompt = task.get("prompt", "")
        system = task.get("system", "You are a helpful AI assistant.")
        temp = task.get("temperature", 0.7)
        max_tokens = task.get("max_tokens", 2048)

        if self.sal_classifier:
            sal_result = self.sal_classifier.classify(prompt)
            if sal_result.get("blocked"):
                return {"error": "SAL: Prompt bloqué", "sal": sal_result}

        try:
            thermal_state = None
            if self.thermal:
                thermal_state = self.thermal.get_status_passive()

            start_time = time.time()

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]

            result = self.model.create_chat_completion(
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
            )

            inference_time = (time.time() - start_time) * 1000

            text = result["choices"][0]["message"]["content"]
            tokens = result.get("usage", {}).get("completion_tokens", 0)

            return {
                "text": text,
                "tokens_generated": tokens,
                "inference_time_ms": round(inference_time, 2),
                "thermal_snapshot": thermal_state,
                "sal_detected": False,
                "sovereign_mode": False,
                "metrics": result.get("usage", {}),
            }
        except Exception as e:
            return {"error": f"Inference failed: {str(e)}"}

    def process_task_streaming(self, task: Dict):
        """Générateur pour le mode streaming - yield les chunks"""
        if not self.model:
            yield {"error": "Modèle non chargé", "is_final": True}
            return

        prompt = task.get("prompt", "")
        system = task.get("system", "You are a helpful AI assistant.")
        temp = task.get("temperature", 0.7)
        max_tokens = task.get("max_tokens", 2048)

        if self.sal_classifier:
            sal_result = self.sal_classifier.classify(prompt)
            if sal_result.get("blocked"):
                yield {"error": "SAL: Prompt bloqué", "sal": sal_result, "is_final": True}
                return

        try:
            thermal_state = None
            if self.thermal:
                thermal_state = self.thermal.get_status_passive()

            start_time = time.time()

            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]

            stream = self.model.create_chat_completion(
                messages=messages,
                temperature=temp,
                max_tokens=max_tokens,
                stream=True,
            )

            token_count = 0
            for chunk in stream:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                if content:
                    token_count += 1
                    yield {"chunk": content, "is_final": False, "tokens": token_count}

            inference_time = (time.time() - start_time) * 1000
            yield {
                "is_final": True,
                "tokens": token_count,
                "inference_time_ms": round(inference_time, 2),
                "thermal_snapshot": thermal_state,
            }
        except Exception as e:
            yield {"error": f"Streaming failed: {str(e)}", "is_final": True}


# =============================================================================
# WORKER LOOP - BIND ROUTER (persistent, gère identity frames)
# =============================================================================


def worker_loop(ipc_address: str, model_path: str, config: Dict):
    """
    Worker avec ROUTER socket.
    Reçoit: [identity, empty, message] multipart (3 trames - REQ protocol)
    Envoie: [identity, empty, reply] multipart
    """
    if not ZMQ_AVAILABLE:
        logging.error("[Worker] ZMQ not installed. Stop.")
        return

    ctx = zmq.Context()
    socket = ctx.socket(zmq.ROUTER)
    socket.setsockopt(zmq.RCVTIMEO, 5000)
    socket.setsockopt(zmq.SNDTIMEO, 5000)
    socket.setsockopt(zmq.LINGER, 0)

    try:
        socket.bind(ipc_address)
    except zmq.ZMQError as e:
        logging.error(f"[Worker] BIND failed on {ipc_address}: {e}")
        return

    worker = None
    try:
        worker = SovereignWorker(model_path, config)
        logging.info("[Worker] Init done, awaiting PING from manager.")
    except Exception as e:
        logging.error(f"[Worker] Critical init failure: {e}")
        return

    def sigterm_handler(signum, frame):
        logging.info("[Worker] SIGTERM reçu. Libération VRAM en cours...")
        if worker and hasattr(worker, "model") and worker.model is not None:
            del worker.model
        try:
            socket.close(linger=0)
        except Exception:
            pass
        try:
            ctx.term()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    while True:
        try:
            socks = dict(poller.poll(5000))
            if socket not in socks:
                if os.name == "posix" and os.getppid() == 1:
                    logging.error("[Worker] Parent mort. Auto-destruction.")
                    break
                continue

            frames = socket.recv_multipart()

            if len(frames) != 3:
                logging.warning(f"[Worker] Invalid frame count: {len(frames)}")
                continue

            identity = frames[0]
            empty_frame = frames[1]
            msg_data = frames[2]

            if msg_data == b"PING":
                socket.send_multipart([identity, empty_frame, b"PONG"])
                continue

            try:
                task = orjson.loads(msg_data)
            except Exception:
                task = {"prompt": msg_data.decode("utf-8", errors="replace")}

            if task.get("stream", False):
                buffer = []
                token_count = 0
                last_flush = time.time()
                stream_error = None

                try:
                    for chunk in worker.process_task_streaming(task):
                        if "error" in chunk:
                            socket.send_multipart([identity, empty_frame, orjson.dumps(chunk)])
                            stream_error = True
                            break

                        buffer.append(chunk.get("chunk", ""))

                        elapsed_ms = (time.time() - last_flush) * 1000
                        if elapsed_ms >= 50 or len(buffer) >= 20:
                            chunk_text = "".join(buffer)
                            socket.send_multipart([identity, empty_frame, orjson.dumps({
                                "chunk": chunk_text,
                                "is_final": False,
                                "tokens": chunk.get("tokens", token_count)
                            })])
                            buffer = []
                            token_count = chunk.get("tokens", 0)
                            last_flush = time.time()
                except Exception as e:
                    socket.send_multipart([identity, empty_frame, orjson.dumps({
                        "error": f"Streaming exception: {str(e)}",
                        "is_final": True
                    })])
                    stream_error = True

                if not stream_error and buffer:
                    final_text = "".join(buffer)
                    socket.send_multipart([identity, empty_frame, orjson.dumps({
                        "chunk": final_text,
                        "is_final": True,
                        "tokens": token_count,
                        "full_text": final_text
                    })])
            else:
                result = worker.process_task(task)
                reply = orjson.dumps(result)
                socket.send_multipart([identity, empty_frame, reply])

        except zmq.Again:
            if os.name == "posix" and os.getppid() == 1:
                logging.error(
                    "[Worker] Processus parent mort. "
                    "Auto-destruction (Libération VRAM)."
                )
                break
            continue
        except Exception as e:
            logging.error(f"[Worker] Exception: {e}")
            continue

    if worker and hasattr(worker, "model") and worker.model is not None:
        del worker.model
        logging.info("[Worker] VRAM libérée.")

    socket.close(linger=0)
    ctx.term()


# =============================================================================
# FALLBACK WORKER - Queue-based (multiprocessing.Queue pour compatibilité)
# =============================================================================


def fallback_worker_loop(
    task_queue: mp.Queue,
    result_queue: mp.Queue,
    model_path: str,
    config: Dict,
):
    """
    Fallback worker utilisant multiprocessing.Queue au lieu de ZMQ.
    Pour environnements où ZMQ n'est pas disponible.
    """
    worker = None
    try:
        worker = SovereignWorker(model_path, config)
        result_queue.put({"status": "ready"})
    except Exception as e:
        logging.error(f"[FallbackWorker] Init failure: {e}")
        result_queue.put({"status": "error", "error": str(e)})
        return

    def sigterm_handler(signum, frame):
        logging.info("[FallbackWorker] SIGTERM reçu. Libération VRAM...")
        if worker and hasattr(worker, "model") and worker.model is not None:
            del worker.model
        sys.exit(0)

    signal.signal(signal.SIGTERM, sigterm_handler)

    while True:
        try:
            task = task_queue.get(timeout=5)
            if task is None:
                break

            result = worker.process_task(task)
            result_queue.put(result)

        except Exception:
            if os.name == "posix" and os.getppid() == 1:
                logging.error("[FallbackWorker] Parent mort. Auto-destruction.")
                break
            continue

    if worker and hasattr(worker, "model") and worker.model is not None:
        del worker.model
        logging.info("[FallbackWorker] VRAM libérée.")


# =============================================================================
# INFERENCE MANAGER - Gestionnaire central des incarnations
# =============================================================================


class InferenceManager:
    """
    Gestionnaire central des incarnations d'inférence.
    Architecture: Transient REQ > Bound ROUTER

    Chaque incarnation est un processus worker indépendant avec son propre
    modèle chargé en VRAM. Le manager communique via des sockets ZMQ REQ
    transitoires (une par requête).
    """

    def __init__(self):
        self._incarnations: Dict[str, Dict[str, Any]] = {}
        self._global_lock = threading.Lock()
        self._ipc_dir = IPC_DIR
        self._ipc_dir.mkdir(parents=True, exist_ok=True)

    def _get_ipc_address(self, name: str) -> str:
        """Génère l'adresse IPC pour un nom d'incarnation."""
        ipc_file = self._ipc_dir / f"{name}.ipc"
        if os.name == "posix":
            return f"ipc://{ipc_file}"
        else:
            return f"ipc://127.0.0.1:{self._name_to_port(name)}"

    def _name_to_port(self, name: str) -> int:
        """Convertit un nom en port TCP pour Windows (IPC non natif)."""
        base_port = 15900
        return base_port + abs(hash(name)) % 1000

    def _handshake(self, ipc_address: str, timeout: float = 60.0) -> bool:
        """Le REQ initie le contact avec PING, attend PONG."""
        if not ZMQ_AVAILABLE:
            return False

        ctx = zmq.Context()
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.RCVTIMEO, 2000)
        sock.setsockopt(zmq.SNDTIMEO, 2000)
        sock.setsockopt(zmq.LINGER, 0)

        try:
            sock.connect(ipc_address)
            poller = zmq.Poller()
            poller.register(sock, zmq.POLLIN)

            sock.send(b"PING")

            elapsed = 0.0
            interval = 1.0
            while elapsed < timeout:
                socks_dict = dict(poller.poll(int(interval * 1000)))
                if sock in socks_dict:
                    reply = sock.recv()
                    if reply == b"PONG":
                        return True
                elapsed += interval

            logging.error(f"[Handshake] Timeout après {timeout}s")
            return False
        except zmq.ZMQError as e:
            logging.error(f"[Handshake] Erreur ZMQ: {e}")
            return False
        finally:
            sock.close(linger=0)
            ctx.term()

    def spawn_incarnation(
        self,
        name: str,
        model_path: str,
        n_ctx: int = 8192,
        n_gpu_layers: int = 32,
        use_queue_fallback: bool = False,
    ) -> bool:
        """
        Spawn une nouvelle incarnation d'inférence.

        Args:
            name: Nom unique de l'incarnation
            model_path: Chemin vers le fichier modèle GGUF
            n_ctx: Taille du contexte
            n_gpu_layers: Nombre de couches GPU
            use_queue_fallback: Utiliser le fallback Queue au lieu de ZMQ

        Returns:
            True si le spawn a réussi
        """
        with self._global_lock:
            if name in self._incarnations:
                logging.warning(
                    f"[InferenceManager] Incarnation '{name}' existe déjà."
                )
                return False

            config = {
                "n_ctx": n_ctx,
                "n_gpu_layers": n_gpu_layers,
                "use_mlock": False,
                "use_mmap": True,
            }

            ipc_address = self._get_ipc_address(name)

            if use_queue_fallback or not ZMQ_AVAILABLE:
                return self._spawn_queue_incarnation(name, model_path, config)

            process = mp.Process(
                target=worker_loop,
                args=(ipc_address, model_path, config),
                daemon=True,
                name=f"Worker-{name}",
            )
            process.start()

            if process.is_alive():
                ready = self._handshake(ipc_address, timeout=120.0)
                if not ready:
                    logging.error(
                        f"[InferenceManager] Handshake échoué pour '{name}'"
                    )
                    process.terminate()
                    process.join(timeout=10)
                    return False

                task_queue = mp.Queue()
                result_queue = mp.Queue()

                self._incarnations[name] = {
                    "process": process,
                    "ipc_address": ipc_address,
                    "model_path": model_path,
                    "config": config,
                    "alive": True,
                    "spawn_time": time.time(),
                    "mode": "zmq",
                    "task_queue": task_queue,
                    "result_queue": result_queue,
                }

                logging.info(
                    f"[InferenceManager] Incarnation '{name}' spawnée "
                    f"(PID={process.pid})"
                )
                return True
            else:
                logging.error(
                    f"[InferenceManager] Process pour '{name}' mort immédiatement"
                )
                return False

    def _spawn_queue_incarnation(
        self, name: str, model_path: str, config: Dict
    ) -> bool:
        """Spawn via fallback Queue-based worker."""
        task_queue = mp.Queue()
        result_queue = mp.Queue()

        process = mp.Process(
            target=fallback_worker_loop,
            args=(task_queue, result_queue, model_path, config),
            daemon=True,
            name=f"FallbackWorker-{name}",
        )
        process.start()

        try:
            ready_msg = result_queue.get(timeout=120)
            if ready_msg.get("status") == "ready":
                self._incarnations[name] = {
                    "process": process,
                    "ipc_address": None,
                    "model_path": model_path,
                    "config": config,
                    "alive": True,
                    "spawn_time": time.time(),
                    "mode": "queue",
                    "task_queue": task_queue,
                    "result_queue": result_queue,
                }
                logging.info(
                    f"[InferenceManager] Incarnation '{name}' spawnée "
                    f"(queue mode, PID={process.pid})"
                )
                return True
            else:
                logging.error(
                    f"[InferenceManager] Queue worker failed: {ready_msg}"
                )
                process.terminate()
                return False
        except Exception:
            logging.error(
                f"[InferenceManager] Timeout waiting for queue worker '{name}'"
            )
            process.terminate()
            return False

    def execute(
        self,
        name: str,
        prompt: str,
        system: str = "You are a helpful AI assistant.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Exécute une requête d'inférence sur une incarnation.

        Crée un socket REQ transitoire, connecte, envoie, reçoit, ferme.
        """
        with self._global_lock:
            incarnation = self._incarnations.get(name)

        if not incarnation:
            return {"error": f"Incarnation '{name}' non trouvée"}

        if not incarnation["alive"]:
            return {"error": f"Incarnation '{name}' est morte"}

        if not incarnation["process"].is_alive():
            incarnation["alive"] = False
            return {"error": f"Incarnation '{name}' processus mort"}

        task = {
            "prompt": prompt,
            "system": system,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if incarnation.get("mode") == "queue":
            return self._execute_queue(incarnation, task)

        return self._execute_zmq(incarnation, task)

    def execute_stream(
        self,
        name: str,
        prompt: str,
        system: str = "You are a helpful AI assistant.",
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        """
        Générateur pour streaming SSE.
        Timeout glissant: TTFT (60s) → ITT (5s)
        """
        with self._global_lock:
            incarnation = self._incarnations.get(name)

        if not incarnation:
            yield {"error": f"Incarnation '{name}' non trouvée", "is_final": True}
            return

        if not incarnation["alive"]:
            yield {"error": f"Incarnation '{name}' est morte", "is_final": True}
            return

        if not incarnation["process"].is_alive():
            incarnation["alive"] = False
            yield {"error": f"Incarnation '{name}' processus mort", "is_final": True}
            return

        task = {
            "prompt": prompt,
            "system": system,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        if incarnation.get("mode") == "queue":
            yield from self._execute_queue_stream(incarnation, task)
            return

        yield from self._execute_stream_zmq(incarnation, task)

    def _execute_stream_zmq(self, incarnation: Dict, task: Dict):
        """Streaming via socket DEALER éphémère avec TTFT/ITT timeouts."""
        if not ZMQ_AVAILABLE:
            yield {"error": "ZMQ non disponible", "is_final": True}
            return

        ipc_address = incarnation["ipc_address"]
        ctx = zmq.Context()
        sock = ctx.socket(zmq.DEALER)
        sock.setsockopt(zmq.LINGER, 0)

        try:
            sock.connect(ipc_address)

            sock.send_multipart([b"", orjson.dumps(task)])

            poller = zmq.Poller()
            poller.register(sock, zmq.POLLIN)

            timeout_ms = 60000  # TTFT: 60s pour premier token

            while True:
                socks = dict(poller.poll(timeout_ms))

                if sock in socks and socks[sock] == zmq.POLLIN:
                    frames = sock.recv_multipart()
                    if len(frames) < 2:
                        continue

                    msg_data = orjson.loads(frames[1])

                    if "chunk" in msg_data:
                        yield msg_data
                        if msg_data.get("is_final"):
                            break
                        timeout_ms = 5000  # ITT: 5s après premier chunk
                    else:
                        yield {
                            "chunk": msg_data.get("result", str(msg_data)),
                            "is_final": True,
                            "fallback_sync": True
                        }
                        break
                else:
                    yield {"error": f"Streaming Timeout (TTFT/ITT dépassé)", "is_final": True}
                    break

        except Exception as e:
            yield {"error": f"Erreur streaming: {str(e)}", "is_final": True}
        finally:
            sock.close(linger=0)
            ctx.term()

    def _execute_queue_stream(self, incarnation: Dict, task: Dict):
        """Fallback streaming via Queue."""
        try:
            incarnation["task_queue"].put(task)
            while True:
                result = incarnation["result_queue"].get(timeout=5)
                if isinstance(result, dict):
                    if "chunk" in result:
                        yield result
                        if result.get("is_final"):
                            break
                    else:
                        yield {
                            "chunk": result.get("result", str(result)),
                            "is_final": True,
                            "fallback_sync": True
                        }
                        break
        except Exception:
            yield {"error": "Timeout: Worker queue ne répond pas", "is_final": True}

    def _execute_zmq(self, incarnation: Dict, task: Dict) -> Dict[str, Any]:
        """Exécution via socket REQ transitoire."""
        if not ZMQ_AVAILABLE:
            return {"error": "ZMQ non disponible"}

        ipc_address = incarnation["ipc_address"]
        ctx = zmq.Context()
        sock = ctx.socket(zmq.REQ)
        sock.setsockopt(zmq.RCVTIMEO, 120000)
        sock.setsockopt(zmq.SNDTIMEO, 10000)
        sock.setsockopt(zmq.LINGER, 0)

        try:
            sock.connect(ipc_address)

            msg = orjson.dumps(task)
            sock.send(msg)

            reply = sock.recv()
            result = orjson.loads(reply)

            return result
        except zmq.Again:
            return {"error": "Timeout: Worker ne répond pas"}
        except zmq.ZMQError as e:
            return {"error": f"Erreur ZMQ: {e}"}
        except Exception as e:
            return {"error": f"Erreur execution: {e}"}
        finally:
            sock.close(linger=0)
            ctx.term()

    def _execute_queue(self, incarnation: Dict, task: Dict) -> Dict[str, Any]:
        """Exécution via Queue fallback."""
        try:
            incarnation["task_queue"].put(task)
            result = incarnation["result_queue"].get(timeout=120)
            return result
        except Exception:
            return {"error": "Timeout: Worker queue ne répond pas"}

    def guillotine(self, name: str) -> bool:
        """
        Exécute une incarnation. Termine le processus et nettoie les ressources.
        """
        with self._global_lock:
            incarnation = self._incarnations.get(name)

            if not incarnation:
                logging.warning(
                    f"[InferenceManager] Guillotine: '{name}' n'existe pas."
                )
                return True

            process = incarnation.get("process")
            mode = incarnation.get("mode", "zmq")

            if process and process.is_alive():
                try:
                    if mode == "queue":
                        incarnation["task_queue"].put(None)
                    process.terminate()
                    process.join(timeout=15)
                    if process.is_alive():
                        process.kill()
                        process.join(timeout=5)
                except Exception as e:
                    logging.error(
                        f"[InferenceManager] Erreur guillotine '{name}': {e}"
                    )
                    try:
                        process.kill()
                    except Exception:
                        pass

            ipc_address = incarnation.get("ipc_address")
            if ipc_address:
                ipc_file = ipc_address.replace("ipc://", "")
                ipc_path = Path(ipc_file)
                if ipc_path.exists():
                    try:
                        ipc_path.unlink()
                    except Exception:
                        pass

            del self._incarnations[name]
            logging.info(
                f"[InferenceManager] Incarnation '{name}' guillotinée."
            )
            return True

    def guillotine_all(self):
        """Exécute toutes les incarnations."""
        with self._global_lock:
            names = list(self._incarnations.keys())

        for name in names:
            self.guillotine(name)

        logging.info(
            "[InferenceManager] Toutes les incarnations guillotinées."
        )

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut de toutes les incarnations."""
        with self._global_lock:
            status = {}
            for name, inc in self._incarnations.items():
                process = inc.get("process")
                alive = process.is_alive() if process else False

                status[name] = {
                    "alive": alive,
                    "pid": process.pid if process and alive else None,
                    "mode": inc.get("mode", "zmq"),
                    "model_path": inc.get("model_path"),
                    "spawn_time": inc.get("spawn_time"),
                    "uptime": (
                        round(
                            time.time() - inc.get("spawn_time", time.time()), 1
                        )
                        if alive
                        else 0
                    ),
                    "ipc_address": inc.get("ipc_address"),
                }

        # Convertir en liste pour la compatibilité JavaScript
        incarnations_list = [
            {"name": name, **info}
            for name, info in status.items()
        ]
        
        return {
            "total": len(status),
            "alive": sum(1 for s in status.values() if s["alive"]),
            "incarnations": incarnations_list,  # Liste pour compatibilité JS
            "incarnations_dict": status,  # Dict pour usage interne
        }

    def get_incarnations(self) -> List[Dict[str, Any]]:
        """Retourne la liste des incarnations avec leurs métadonnées."""
        with self._global_lock:
            result = []
            for name, inc in self._incarnations.items():
                process = inc.get("process")
                alive = process.is_alive() if process else False
                result.append(
                    {
                        "name": name,
                        "alive": alive,
                        "pid": process.pid if process and alive else None,
                        "mode": inc.get("mode", "zmq"),
                        "model_path": inc.get("model_path"),
                        "spawn_time": inc.get("spawn_time"),
                    }
                )
            return result
