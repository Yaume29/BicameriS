"""
BICAMERIS - Docker Sandbox
==========================
Isolated code execution using Docker containers.
Falls back to venv if Docker unavailable.
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import docker

    DOCKER_AVAILABLE = True
except ImportError:
    docker = None
    DOCKER_AVAILABLE = False


class DockerSandbox:
    """
    Isolated execution environment using Docker.
    If Docker unavailable, falls back to venv.
    """

    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        self.client = None
        self._init_docker()

    def _init_docker(self):
        """Initialize Docker client"""
        if not DOCKER_AVAILABLE:
            logging.warning("[DockerSandbox] Docker non disponible - mode dégradé")
            return

        try:
            self.client = docker.from_env()
            self.client.ping()
            logging.info("[DockerSandbox] ✅ Connecté au daemon Docker")
        except Exception as e:
            logging.warning(f"[DockerSandbox] Docker inaccessible: {e}")
            self.client = None

    def execute_code(
        self, code: str, timeout: int = 15, requirements: list = None
    ) -> Dict[str, Any]:
        """Execute code in isolated container"""
        if not self.client:
            return self._execute_fallback(code, timeout, requirements)

        try:
            # Build command with optional requirements
            cmd = ["python", "-c", code]
            if requirements:
                req_file = "\n".join(requirements)
                setup = f"import sys\nfor pkg in '''{req_file}'''.split(): import subprocess; subprocess.run([sys.executable, '-m', 'pip', 'install', pkg])\n"
                code = setup + code
                cmd = ["python", "-c", code]

            container = self.client.containers.run(
                self.image,
                command=cmd,
                detach=True,
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
                network_disabled=True,
                remove=True,
                stdout=True,
                stderr=True,
            )

            result = container.wait(timeout=timeout)
            logs = container.logs().decode("utf-8")

            if result["StatusCode"] == 0:
                return {"status": "SUCCESS", "output": logs}
            else:
                return {"status": "ERROR", "error": logs}

        except docker.errors.ContainerError as e:
            return {"status": "ERROR", "error": str(e)}
        except Exception as e:
            logging.error(f"[DockerSandbox] Execution error: {e}")
            return {"status": "TIMEOUT", "error": str(e)}

    def _execute_fallback(self, code: str, timeout: int, requirements: list) -> Dict[str, Any]:
        """Fallback: execute in isolated venv using subprocess with proper process tree handling"""
        import subprocess
        import sys
        import os
        import signal
        import shutil

        sandbox_id = str(uuid.uuid4())[:8]
        venv_path = Path("ZONE_RESERVEE") / "sandbox" / f"venv_{sandbox_id}"

        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True
            )

            if requirements:
                pip = venv_path / "Scripts" / "pip.exe"
                for req in requirements:
                    subprocess.run([str(pip), "install", req], capture_output=True, timeout=60)

            python = venv_path / "Scripts" / "python.exe"

            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["preexec_fn"] = os.setsid

            process = subprocess.Popen(
                [str(python), "-c", code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **kwargs,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                if process.returncode == 0:
                    return {"status": "SUCCESS", "output": stdout.decode("utf-8")}
                else:
                    return {"status": "ERROR", "error": stderr.decode("utf-8")}
            except subprocess.TimeoutExpired:
                if os.name == "nt":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                return {"status": "TIMEOUT", "error": f"Execution exceeded {timeout}s"}

        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
        finally:
            try:
                shutil.rmtree(venv_path, ignore_errors=True)
            except:
                pass

    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self.client is not None


_sandbox = None


def get_sandbox() -> DockerSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox
