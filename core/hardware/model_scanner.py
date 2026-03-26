import os
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict


class ModelScanner:
    def __init__(self):
        self.blacklist = {
            "$Recycle.Bin",
            "System Volume Information",
            "Windows",
            "AppData",
            "Program Files",
            "Program Files (x86)",
            "ProgramData",
            "Recovery",
            "PerfLogs",
        }
        self.found_models = []
        self.models_found = self.found_models
        self.is_scanning = False
        self.scan_start_time = None
        self.scan_path = None
        self._scan_thread = None
        self._stop_event = threading.Event()

    def _is_gguf_file(self, filename: str) -> bool:
        """Check if file is a GGUF model"""
        return filename.lower().endswith(".gguf")

    def scan(self, root_path: str):
        """Lance le scan dans un thread séparé pour Flask."""
        if self.is_scanning:
            return {"status": "already_scanning"}

        # Normalize path for Windows
        import os

        root_path = os.path.normpath(root_path)

        self.is_scanning = True
        self.found_models = []
        self.scan_start_time = time.time()
        self.scan_path = root_path

        self._scan_thread = threading.Thread(target=self._run_scan, args=(root_path,))
        self._scan_thread.daemon = True
        self._scan_thread.start()

        return {"status": "started", "path": root_path}

    def _run_scan(self, root_path: str):
        """Scan récursif avec os.walk et blacklist"""
        target = Path(root_path)

        if not target.exists():
            self.is_scanning = False
            print(f"[ModelScanner] Chemin introuvable: {root_path}")
            return

        try:
            for root, dirs, files in os.walk(target, topdown=True):
                # Filtrer les dossiers interdits (in-place)
                dirs[:] = [d for d in dirs if d not in self.blacklist]

                for file in files:
                    if file.lower().endswith(".gguf"):
                        try:
                            full_path = os.path.join(root, file)
                            stats = os.stat(full_path)

                            model_info = {
                                "name": file,
                                "path": full_path,
                                "size_gb": round(stats.st_size / (1024**3), 2),
                                "size_mb": round(stats.st_size / (1024**2), 1),
                                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                                "folder": os.path.dirname(full_path),
                            }
                            self.found_models.append(model_info)
                        except (OSError, PermissionError):
                            continue

            # Tri par date modification (plus récents en premier)
            self.found_models.sort(key=lambda x: x["modified"], reverse=True)

        except Exception as e:
            print(f"[ModelScanner] Erreur: {e}")

        finally:
            self.is_scanning = False

    def get_status(self):
        """Retourne l'état du scan"""
        elapsed = 0
        if self.scan_start_time:
            elapsed = round(time.time() - self.scan_start_time, 1)

        return {
            "is_scanning": self.is_scanning,
            "path": self.scan_path,
            "elapsed_seconds": elapsed,
            "count": len(self.found_models),
            "models": self.found_models,
            "models_found": self.found_models,
        }

    def stop(self):
        """Arrête le scan (ne stoppe que le flag, le thread继续)"""
        self.is_scanning = False

    def get_model_by_path(self, path: str):
        """Récupère un modèle par son chemin"""
        for m in self.found_models:
            if m["path"] == path:
                return m
        return None


# Instance globale
scanner = ModelScanner()


def get_scanner() -> ModelScanner:
    return scanner
