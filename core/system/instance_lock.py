"""
BICAMERIS - Instance Lock Manager
=================================
Prevents conflicts when multiple instances are running.
Implements sleep/awakening instead of killing tasks.
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class LockStatus:
    """Status of an instance lock"""
    acquired: bool
    owner_pid: Optional[int] = None
    owner_instance_id: Optional[str] = None
    wait_time: float = 0.0
    message: str = ""


class InstanceLock:
    """
    File-based instance lock with sleep/awakening support.
    
    Usage:
        lock = InstanceLock("storage/locks/master.lock")
        status = lock.acquire_or_sleep()
        
        if not status.acquired:
            print(f"Waiting for instance {status.owner_pid}...")
            # Enter sleep mode, wait for wake signal
            lock.wait_for_wake(timeout=30)
    """

    def __init__(self, lock_path: str = "storage/locks/master.lock", timeout: float = 30.0):
        self.lock_path = Path(lock_path)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.instance_id = f"{os.getpid()}_{int(time.time())}"
        self.acquired = False
        self._wake_signal = threading.Event()

    def acquire_or_sleep(self) -> LockStatus:
        """
        Try to acquire lock. If another instance holds it, return sleep status.
        
        Returns:
            LockStatus with acquired=True if lock obtained
            LockStatus with acquired=False and wait info if sleeping
        """
        if self._check_ownership():
            self.acquired = True
            return LockStatus(acquired=True, owner_pid=os.getpid())

        if not self._is_owner_alive():
            self._clean_stale_lock()
            return self._write_lock()

        owner_info = self._read_owner_info()
        return LockStatus(
            acquired=False,
            owner_pid=owner_info.get("pid"),
            owner_instance_id=owner_info.get("instance_id"),
            wait_time=self._estimate_wait(owner_info),
            message=f"Instance {owner_info.get('pid', '?')} is active. Entering sleep mode."
        )

    def release(self) -> None:
        """Release the lock and clean up"""
        if self.lock_path.exists():
            try:
                owner_info = self._read_owner_info()
                if owner_info.get("pid") == os.getpid():
                    self.lock_path.unlink()
                    self.acquired = False
                    logger.info("[InstanceLock] Lock released")
            except Exception as e:
                logger.warning(f"[InstanceLock] Error releasing lock: {e}")

    def wait_for_wake(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for wake signal from another instance.
        
        Returns:
            True if woken, False if timeout
        """
        wait_time = timeout or self.timeout
        logger.info(f"[InstanceLock] Sleeping for {wait_time}s...")

        start = time.time()
        while time.time() - start < wait_time:
            if self._wake_signal.wait(timeout=1.0):
                logger.info("[InstanceLock] Wake signal received!")
                return True
            elapsed = int(time.time() - start)
            remaining = int(wait_time - elapsed)
            if elapsed % 10 == 0:
                logger.info(f"[InstanceLock] Still sleeping... {remaining}s remaining")

        logger.warning("[InstanceLock] Wake timeout exceeded")
        return False

    def send_wake(self) -> bool:
        """Signal another instance to wake up"""
        wake_file = self.lock_path.with_suffix(".wake")
        try:
            wake_file.write_text(str(time.time()), encoding="utf-8")
            logger.info("[InstanceLock] Wake signal sent")
            return True
        except Exception as e:
            logger.error(f"[InstanceLock] Failed to send wake: {e}")
            return False

    def _check_ownership(self) -> bool:
        """Check if we own the lock"""
        if not self.lock_path.exists():
            return False
        try:
            owner_info = self._read_owner_info()
            return owner_info.get("pid") == os.getpid()
        except Exception:
            return False

    def _is_owner_alive(self) -> bool:
        """Check if the lock owner process is still alive"""
        if not self.lock_path.exists():
            return False

        try:
            owner_info = self._read_owner_info()
            pid = owner_info.get("pid")
            if not pid:
                return False

            if os.name == "nt":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(1, 0, pid)
                if handle:
                    kernel32.CloseHandle(handle)
                    return True
                return False
            else:
                os.kill(pid, 0)
                return True
        except (ProcessLookupError, OSError):
            return False
        except Exception:
            return False

    def _clean_stale_lock(self) -> None:
        """Remove stale lock file"""
        if self.lock_path.exists():
            self.lock_path.unlink()
            logger.info("[InstanceLock] Cleaned stale lock")

    def _write_lock(self) -> LockStatus:
        """Write lock file with our PID"""
        try:
            lock_data = f"{os.getpid()}|{self.instance_id}|{datetime.now().isoformat()}"
            self.lock_path.write_text(lock_data, encoding="utf-8")
            self.acquired = True
            logger.info(f"[InstanceLock] Lock acquired (PID: {os.getpid()})")
            return LockStatus(acquired=True, owner_pid=os.getpid())
        except Exception as e:
            logger.error(f"[InstanceLock] Failed to write lock: {e}")
            return LockStatus(
                acquired=False,
                message=f"Failed to acquire lock: {e}"
            )

    def _read_owner_info(self) -> Dict[str, Any]:
        """Read owner info from lock file"""
        try:
            content = self.lock_path.read_text(encoding="utf-8")
            parts = content.strip().split("|")
            return {
                "pid": int(parts[0]) if parts else None,
                "instance_id": parts[1] if len(parts) > 1 else None,
                "timestamp": parts[2] if len(parts) > 2 else None,
            }
        except Exception:
            return {}

    def _estimate_wait(self, owner_info: Dict) -> float:
        """Estimate wait time based on owner info"""
        timestamp_str = owner_info.get("timestamp", "")
        if timestamp_str:
            try:
                owner_time = datetime.fromisoformat(timestamp_str)
                elapsed = (datetime.now() - owner_time).total_seconds()
                return max(0, self.timeout - elapsed)
            except Exception:
                pass
        return self.timeout

    def __enter__(self):
        return self.acquire_or_sleep()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


_instance_lock = None


def get_instance_lock() -> InstanceLock:
    global _instance_lock
    if _instance_lock is None:
        _instance_lock = InstanceLock()
    return _instance_lock
