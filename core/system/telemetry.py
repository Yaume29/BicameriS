"""
BICAMERIS - Telemetry
=====================
Async JSONL logger for cognitive audit trail.
Uses asyncio.Queue for non-blocking Event Loop.
Ring Buffer architecture: O(1) RAM read, async disk persistence.
Dual-Write: Machine archive (JSONL) + Human journal (Markdown).
"""

import json
import asyncio
import logging
import collections
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime


class CognitiveLogger:
    """
    Async JSONL logger for cognitive operations.
    Ring Buffer: O(1) RAM reads, async disk writes.
    Dual-Write: JSONL (machine) + Markdown (human).
    """

    def __init__(self, log_dir: str = "storage/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.flux_file = self.log_dir / "flux_log.jsonl"
        self.thought_file = self.log_dir / "thought_log.jsonl"
        self.task_file = self.log_dir / "task_log.jsonl"

        self._write_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        self._pre_boot_queue: list = []

        self._recent_thoughts = collections.deque(maxlen=50)
        self._hydrate_buffer()

        logging.info(f"[Telemetry] ✅ Logger initialisé avec Ring Buffer (max 50)")

    def _hydrate_buffer(self):
        """Remplit le buffer une seule fois au démarrage (OOM-Safe et Zéro I/O bloquant)"""
        if not self.thought_file.exists():
            return

        try:
            with open(self.thought_file, "r", encoding="utf-8") as f:
                for line in collections.deque(f, maxlen=50):
                    if line.strip():
                        try:
                            self._recent_thoughts.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logging.warning(f"[Telemetry] Échec de l'hydratation du buffer: {e}")

    async def start(self):
        """Start the async write worker"""
        if self._running:
            return

        self._loop = asyncio.get_running_loop()
        self._running = True

        for file_path, data in self._pre_boot_queue:
            self._write_queue.put_nowait((file_path, data))
        self._pre_boot_queue.clear()

        self._worker_task = asyncio.create_task(self._write_worker())
        logging.info("[Telemetry] ✅ Worker started")

    async def stop(self):
        """Stop the async write worker and flush pending writes"""
        if not self._running:
            return

        self._running = False

        if self._worker_task:
            await self._write_queue.put(None)
            try:
                await asyncio.wait_for(self._worker_task, timeout=5.0)
            except asyncio.TimeoutError:
                logging.warning("[Telemetry] Timeout lors de l'arrêt")

        logging.info("[Telemetry] ⏹ Worker stopped")

    async def _write_worker(self):
        """Async worker that processes write queue - non-blocking"""
        while self._running or not self._write_queue.empty():
            try:
                entry = await asyncio.wait_for(self._write_queue.get(), timeout=1.0)
                if entry is None:
                    break

                file_path, data = entry
                await asyncio.to_thread(self._write_sync, file_path, data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logging.error(f"[Telemetry] Erreur write worker: {e}")

    def _write_sync(self, file_path: Path, data: Dict):
        """Dual-Write: JSONL archive + Markdown human journal"""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

            if data.get("type") == "thought" or data.get("type") == "autonomous_thought":
                human_file = self.log_dir / "journal_cognitif.md"
                timestamp = data.get("timestamp", "")[:19].replace("T", " à ")

                content = f"### 🧠 Cycle Cognitif - {timestamp}\n"

                if "question" in data:
                    content += f"**Impulsion initiale :** {data['question']}\n\n"

                if "left_analysis" in data:
                    content += f"**Gaucher (Logique) :**\n> {data['left_analysis'].strip()}\n\n"

                if "right_intuition" in data:
                    content += (
                        f"**Droitier (Intuition) :**\n> {data['right_intuition'].strip()}\n\n"
                    )

                if "final_synthesis" in data:
                    content += f"**Synthèse de l'Arbitre :**\n{data['final_synthesis'].strip()}\n\n"
                elif "content" in data:
                    content += f"**Réflexion Autonome :**\n{data['content'].strip()}\n\n"

                content += "---\n\n"

                with open(human_file, "a", encoding="utf-8") as f:
                    f.write(content)

            elif data.get("type") == "flux":
                human_file = self.log_dir / "system_events.log"
                timestamp = data.get("timestamp", "")[:19].replace("T", " ")
                event = data.get("event", "SYSTEM_UPDATE")

                with open(human_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] [{event}] {data}\n")

        except Exception as e:
            logging.error(f"[Telemetry] Erreur d'écriture Dual-Scribe: {e}")

    def _enqueue(self, file_path: Path, data: Dict):
        """Enqueue strictement thread-safe via call_soon_threadsafe"""
        if self._loop is None or not self._loop.is_running():
            self._pre_boot_queue.append((file_path, data))
            return

        self._loop.call_soon_threadsafe(self._write_queue.put_nowait, (file_path, data))

    def log_thought(self, thought: Dict[str, Any]):
        """Queue a thought for logging (thread-safe) + RAM update"""
        entry = {"timestamp": datetime.now().isoformat(), "type": "thought", **thought}

        self._recent_thoughts.append(entry)

        self._enqueue(self.thought_file, entry)

    def log_task(self, task: Dict[str, Any]):
        """Queue a task for logging (thread-safe)"""
        entry = {"timestamp": datetime.now().isoformat(), "type": "task", **task}
        self._enqueue(self.task_file, entry)

    def log_flux(self, flux_data: Dict[str, Any]):
        """Queue a flux entry for logging (thread-safe)"""
        entry = {"timestamp": datetime.now().isoformat(), "type": "flux", **flux_data}
        self._enqueue(self.flux_file, entry)

    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Generic event logging (thread-safe)"""
        entry = {"timestamp": datetime.now().isoformat(), "event": event_type, **data}
        self._enqueue(self.flux_file, entry)

    def get_recent_thoughts(self, limit: int = 50) -> list:
        """Lecture instantanée depuis la RAM - O(1), zéro I/O"""
        thoughts = list(self._recent_thoughts)[-limit:]
        return thoughts[::-1]


_telemetry = None


def get_telemetry() -> CognitiveLogger:
    global _telemetry
    if _telemetry is None:
        _telemetry = CognitiveLogger()
    return _telemetry
