"""
Async Task Queue for Aetheris
==============================
Simple async task system to prevent Flask from blocking.

Usage:
    from core_reserved.task_queue import get_task_queue, queue_task

    # Queue a heavy task
    task_id = queue_task('heavy_computation', {'param': value})

    # Check status
    status = get_task_queue().get_status(task_id)
"""

import logging
import threading
import time
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from queue import Queue, Empty

_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    id: str
    name: str
    params: Dict[str, Any]
    status: str = "pending"
    result: Any = None
    error: str = None
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    progress: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


class TaskQueue:
    """
    Queue de tâches asynchrones avec workers threads.

    Caractéristiques:
    - Workers threads pour tâches CPU-bound
    - Progression en temps réel
    - Annulation possible
    - Persistence optionnelle
    """

    def __init__(self, max_workers: int = 4, persist_path: str = None):
        self.max_workers = max_workers
        self.persist_path = persist_path

        self._tasks: Dict[str, Task] = {}
        self._task_queue: Queue = Queue()
        self._workers: list = []
        self._running = False
        self._lock = threading.Lock()

        if persist_path:
            self._load_tasks()

    def _load_tasks(self):
        """Charge les tâches persistantes"""
        if self.persist_path and Path(self.persist_path).exists():
            try:
                with open(self.persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for task_data in data.get("tasks", []):
                        if task_data["status"] in ["pending", "running"]:
                            task_data["status"] = "pending"
                        self._tasks[task_data["id"]] = Task(**task_data)
            except Exception:
                pass

    def _save_tasks(self):
        """Sauvegarde les tâches"""
        if not self.persist_path:
            return

        try:
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"tasks": [t.to_dict() for t in self._tasks.values()]},
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception:
            pass

    def start(self):
        """Démarre les workers"""
        if self._running:
            return

        self._running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"TaskWorker-{i}")
            worker.start()
            self._workers.append(worker)

    def stop(self):
        """Arrête les workers"""
        self._running = False
        for _ in range(self.max_workers):
            self._task_queue.put(None)

    def _worker(self):
        """Worker thread qui traite les tâches"""
        while self._running:
            try:
                task_id = self._task_queue.get(timeout=1)
                if task_id is None:
                    break

                self._execute_task(task_id)

            except Empty:
                continue
            except Exception as e:
                print(f"[TaskQueue] Worker error: {e}")

    def _execute_task(self, task_id: str):
        """Exécute une tâche"""
        with self._lock:
            if task_id not in self._tasks:
                return

            task = self._tasks[task_id]
            task.status = TaskStatus.RUNNING.value
            task.started_at = datetime.now().isoformat()

        try:
            result = self._run_task(task.name, task.params, task)

            with self._lock:
                task.result = result
                task.status = TaskStatus.COMPLETED.value
                task.completed_at = datetime.now().isoformat()
                task.progress = 100

        except Exception as e:
            with self._lock:
                task.error = str(e)
                task.status = TaskStatus.FAILED.value
                task.completed_at = datetime.now().isoformat()

        self._save_tasks()

    def _run_task(self, name: str, params: Dict, task: Task) -> Any:
        """Route vers le bon handler"""
        handlers = {
            "heavy_computation": self._handler_heavy_computation,
            "agent_delegate": self._handler_agent_delegate,
            "memory_compress": self._handler_memory_compress,
            "web_search": self._handler_web_search,
        }

        handler = handlers.get(name)
        if handler:
            return handler(params, task)

        return {"error": f"Unknown task: {name}"}

    def _handler_heavy_computation(self, params: Dict, task: Task) -> Any:
        """Handler pour calculs lourds"""
        for i in range(10):
            time.sleep(0.5)
            with self._lock:
                task.progress = (i + 1) * 10
        return {"result": "computation done", "params": params}

    def _handler_agent_delegate(self, params: Dict, task: Task) -> Any:
        """Handler pour délégation agent"""
        agent_name = params.get("agent_name", "")
        task_desc = params.get("task_description", "")

        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ZONE_AETHERIS"))

        try:
            from core.agent_manager import get_agent_manager

            manager = get_agent_manager()
            return manager.delegate_task(agent_name, task_desc)
        except ImportError as e:
            return {"error": str(e)}

    def _handler_memory_compress(self, params: Dict, task: Task) -> Any:
        """Handler pour compression mémoire (Graceful Degradation)"""
        try:
            from core_reserved.paradoxical_sleep import get_paradoxical_sleep
            ps = get_paradoxical_sleep()
            return ps.compress_memory()
        except ImportError:
            logging.warning("[TaskQueue] ⚠️ paradoxical_sleep non disponible (ZONE_RESERVEE)")
            return {"error": "MODULE ABSENT : paradoxical_sleep n'est pas disponible (ZONE_RESERVEE)."}
        except Exception as e:
            return {"error": f"Erreur compression mémoire: {str(e)}"}

    def _handler_web_search(self, params: Dict, task: Task) -> Any:
        """Handler pour recherche web (Graceful Degradation)"""
        try:
            from core_reserved.web_search import get_web_searcher
            ws = get_web_searcher()
            query = params.get("query", "")
            return {"results": ws.search(query)}
        except ImportError:
            logging.warning("[TaskQueue] ⚠️ web_search non disponible (ZONE_RESERVEE)")
            return {"error": "MODULE ABSENT : web_search n'est pas disponible (ZONE_RESERVEE)."}
        except Exception as e:
            return {"error": f"Erreur recherche web: {str(e)}"}

    def queue_task(self, name: str, params: Dict[str, Any]) -> str:
        """Ajoute une tâche à la queue"""
        task_id = str(uuid.uuid4())[:8]

        task = Task(id=task_id, name=name, params=params)

        with self._lock:
            self._tasks[task_id] = task

        self._task_queue.put(task_id)

        if not self._running:
            self.start()

        return task_id

    def get_status(self, task_id: str) -> Optional[Dict]:
        """Retourne le statut d'une tâche"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task:
                return task.to_dict()
        return None

    def cancel_task(self, task_id: str) -> bool:
        """Annule une tâche (si pas encore démarrée)"""
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING.value:
                task.status = TaskStatus.CANCELLED.value
                return True
        return False

    def get_all_tasks(self, status: str = None, limit: int = 50) -> list:
        """Retourne toutes les tâches"""
        with self._lock:
            tasks = list(self._tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [t.to_dict() for t in tasks[:limit]]

    def clear_completed(self):
        """Supprime les tâches terminées"""
        with self._lock:
            to_remove = [
                tid
                for tid, t in self._tasks.items()
                if t.status
                in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value, TaskStatus.CANCELLED.value]
            ]
            for tid in to_remove:
                del self._tasks[tid]
        self._save_tasks()


_task_queue = None


def get_task_queue() -> TaskQueue:
    """Singleton du task queue"""
    global _task_queue
    if _task_queue is None:
        persist_path = _BASE_DIR / "ZONE_RESERVEE" / "logs" / "tasks.json"
        _task_queue = TaskQueue(max_workers=2, persist_path=str(persist_path))
    return _task_queue


def queue_task(name: str, params: Dict[str, Any]) -> str:
    """Helper pour ajouter une tâche"""
    return get_task_queue().queue_task(name, params)


# Legacy compatibility
class TaskManager:
    """Wrapper pour l'ancien TaskManager"""

    def __init__(self):
        self.queue = get_task_queue()

    def add_task(self, name: str, params: Dict) -> str:
        return self.queue.queue_task(name, params)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        return self.queue.get_status(task_id)

    def list_tasks(self) -> list:
        return self.queue.get_all_tasks()
