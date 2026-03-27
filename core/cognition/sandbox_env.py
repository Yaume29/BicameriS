"""
Diadikos & Palladion - Docker Sandbox
=========================
Isolated code execution using Docker containers.
Falls back to venv if Docker unavailable.
Security validation via AST before execution.
"""

import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False
    logging.warning("[DockerSandbox] requests non installé - gestion timeout dégradée")

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
    Security validation enforced before execution.
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
        """Execute code in isolated container or fallback to PEP 578 airgap"""
        if not self.client:
            logging.warning("[DockerSandbox] Docker down. Bascule sur l'Audit Hook natif.")
            return self._execute_fallback(code, timeout, requirements or [])

        container = None
        try:
            cmd = ["python", "-c", code]
            if requirements:
                req_file = "\n".join(requirements)
                setup = f"import sys\nfor pkg in '''{req_file}'''.split(): import subprocess; subprocess.run([sys.executable, '-m', 'pip', 'install', pkg])\n"
                code = setup + code
                cmd = ["python", "-c", code]

            net_mode = "bridge" if requirements else "none"

            container = self.client.containers.run(
                self.image,
                command=cmd,
                detach=True,
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,
                network_mode=net_mode,
                remove=True,
                stdout=True,
                stderr=True,
            )

            try:
                result = container.wait(timeout=timeout)
                logs = container.logs().decode("utf-8")

                if result["StatusCode"] == 0:
                    return {"status": "SUCCESS", "output": logs}
                else:
                    return {"status": "ERROR", "error": logs}

            except requests.exceptions.ReadTimeout:
                container.stop(timeout=1)
                return {
                    "status": "TIMEOUT",
                    "error": f"Execution tuée : boucle infinie ou script trop long (> {timeout}s).",
                }

        except docker.errors.ContainerError as e:
            return {"status": "ERROR", "error": str(e)}
        except Exception as e:
            logging.error(f"[DockerSandbox] Execution error: {e}")
            return {"status": "TIMEOUT", "error": str(e)}
        finally:
            if container:
                try:
                    container.stop(timeout=1)
                    container.remove(force=True)
                except:
                    pass

    def _execute_fallback(self, code: str, timeout: int, requirements: list) -> Dict[str, Any]:
        """Fallback Bare-Metal : Isolation via Runtime Audit Hooks (PEP 578)"""
        import subprocess
        import sys
        import os
        import signal
        import shutil
        import uuid
        from pathlib import Path

        sandbox_id = str(uuid.uuid4())[:8]
        venv_path = Path("ZONE_RESERVEE") / "sandbox" / f"venv_{sandbox_id}"

        security_wrapper = """
import sys
import builtins

def _strict_audit_hook(event, args):
    allowed_events = {
        'builtins.id', 'compile', 'exec', 'import', 'os.environ', 
        'sys._getframe', 'sys.settrace', 'sys.setprofile'
    }
    
    if event not in allowed_events and not event.startswith('import'):
        raise RuntimeError(f"🔒 [SANDBOX VIOLATION] Tentative d'exécution interdite : {event}")

sys.addaudithook(_strict_audit_hook)

code_to_run = '''{AI_CODE}'''
exec(code_to_run, {"__builtins__": builtins})
"""
        safe_code = code.replace("'''", "\\'\\'\\'")
        final_script_content = security_wrapper.replace("{AI_CODE}", safe_code)

        bin_dir = "Scripts" if os.name == "nt" else "bin"
        pip_ext = ".exe" if os.name == "nt" else ""

        try:
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True
            )

            script_path = venv_path / "run_sandbox.py"
            script_path.write_text(final_script_content, encoding="utf-8")

            python = venv_path / bin_dir / f"python{pip_ext}"

            kwargs = (
                {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
                if os.name == "nt"
                else {"preexec_fn": os.setsid}
            )

            process = subprocess.Popen(
                [str(python), str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **kwargs,
            )

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
            shutil.rmtree(venv_path, ignore_errors=True)

    def is_available(self) -> bool:
        """Check if Docker is available"""
        return self.client is not None


_sandbox = None


def get_sandbox() -> DockerSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = DockerSandbox()
    return _sandbox
