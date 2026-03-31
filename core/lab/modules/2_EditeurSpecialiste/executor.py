"""
Code Executor - Éditeur Spécialiste
================================
Exécution de code dans un sandbox local.
"""

import subprocess
import tempfile
import uuid
import os
import signal
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger("editeur.executor")

TIMEOUT_DEFAULT = 30
TIMEOUT_LONG = 120


class CodeExecutor:
    """
    Executor de code pour l'Editeur Spécialiste.
    Supporte: Python, JavaScript, Rust, Go, et plus.
    """
    
    SUPPORTED_LANGUAGES = {
        "python": {
            "extensions": [".py"],
            "cmd": "python",
            "args": ["-u", "{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "python3": {
            "extensions": [".py"],
            "cmd": "python3",
            "args": ["-u", "{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "node": {
            "extensions": [".js"],
            "cmd": "node",
            "args": ["{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "javascript": {
            "extensions": [".js"],
            "cmd": "node",
            "args": ["{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "rust": {
            "extensions": [".rs"],
            "cmd": "rustc",
            "args": ["{file}", "-o", "{output}"],
            "compile_only": True,
            "run_after": "{output}",
            "timeout": TIMEOUT_LONG
        },
        "go": {
            "extensions": [".go"],
            "cmd": "go",
            "args": ["run", "{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "bash": {
            "extensions": [".sh"],
            "cmd": "bash",
            "args": ["{file}"],
            "timeout": TIMEOUT_DEFAULT
        },
        "powershell": {
            "extensions": [".ps1"],
            "cmd": "pwsh",
            "args": ["-File", "{file}"],
            "timeout": TIMEOUT_DEFAULT
        }
    }
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else None
        self.temp_dir = Path(tempfile.gettempdir()) / "aetheris_exec"
        self.temp_dir.mkdir(exist_ok=True)
    
    def execute(self, code: str, language: str = "python", timeout: int = None) -> Dict:
        """
        Exécute du code.
        """
        lang_config = self.SUPPORTED_LANGUAGES.get(language.lower())
        
        if not lang_config:
            return {
                "status": "error",
                "language": language,
                "message": f"Langage non supporté: {language}",
                "supported": list(self.SUPPORTED_LANGUAGES.keys())
            }
        
        ext = lang_config["extensions"][0]
        filename = f"exec_{uuid.uuid4().hex[:8]}{ext}"
        filepath = self.temp_dir / filename
        
        try:
            filepath.write_text(code, encoding="utf-8")
        except Exception as e:
            return {"status": "error", "message": f"Erreur écriture: {e}"}
        
        cmd = lang_config["cmd"]
        args = [a.format(file=str(filepath), output=str(filepath.parent / filename)) for a in lang_config["args"]]
        
        timeout = timeout or lang_config.get("timeout", TIMEOUT_DEFAULT)
        
        return self._run_process(cmd, args, timeout, language)
    
    def execute_file(self, filepath: str, language: str = None, timeout: int = None) -> Dict:
        """
        Exécute un fichier existant.
        """
        file_path = Path(filepath)
        
        if not file_path.exists():
            return {"status": "error", "message": f"Fichier non trouvé: {filepath}"}
        
        if language is None:
            ext = file_path.suffix.lower()
            for lang, config in self.SUPPORTED_LANGUAGES.items():
                if ext in config["extensions"]:
                    language = lang
                    break
        
        if language is None:
            return {"status": "error", "message": f"Extension non supportée: {ext}"}
        
        lang_config = self.SUPPORTED_LANGUAGES.get(language.lower())
        if not lang_config:
            return {"status": "error", "message": f"Langage non supporté: {language}"}
        
        cmd = lang_config["cmd"]
        args = [a.format(file=str(file_path), output=str(file_path.parent / file_path.stem)) for a in lang_config["args"]]
        
        timeout = timeout or lang_config.get("timeout", TIMEOUT_DEFAULT)
        
        return self._run_process(cmd, args, timeout, language)
    
    def _run_process(self, cmd: str, args: list, timeout: int, language: str) -> Dict:
        """Exécute un processus."""
        full_cmd = [cmd] + args
        
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace_path) if self.workspace_path else None
            )
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "language": language,
                "cmd": " ".join(full_cmd),
                "timeout": timeout
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": f"Exécution dépassée ({timeout}s)",
                "language": language,
                "stdout": "",
                "stderr": "Timeout"
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Commande non trouvée: {cmd}",
                "language": language,
                "hint": f"Installez {cmd} ou utilisez un langage supporté"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "language": language
            }
    
    def check_dependencies(self, language: str) -> Dict:
        """Vérifie si les dépendances sont installées."""
        lang_config = self.SUPPORTED_LANGUAGES.get(language.lower())
        
        if not lang_config:
            return {"status": "error", "message": f"Langage non supporté"}
        
        cmd = lang_config["cmd"]
        
        try:
            result = subprocess.run(
                [cmd, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            version = result.stdout.strip() or result.stderr.strip()
            return {
                "status": "ok",
                "language": language,
                "available": True,
                "version": version.split("\n")[0]
            }
        except FileNotFoundError:
            return {
                "status": "error",
                "language": language,
                "available": False,
                "message": f"{cmd} n'est pas installé"
            }
        except Exception as e:
            return {
                "status": "error",
                "language": language,
                "available": False,
                "message": str(e)
            }
    
    def list_available(self) -> Dict:
        """Liste les langages disponibles."""
        available = {}
        unavailable = {}
        
        for lang in self.SUPPORTED_LANGUAGES:
            check = self.check_dependencies(lang)
            if check.get("available"):
                available[lang] = check.get("version", "unknown")
            else:
                unavailable[lang] = check.get("message", "not installed")
        
        return {
            "available": available,
            "unavailable": unavailable,
            "count_available": len(available)
        }
    
    def test_code(self, code: str, language: str = "python") -> Dict:
        """
        Teste le code avec des assertions basiques.
        """
        if language.lower() == "python":
            test_code = f"""
import sys
from io import StringIO

_results = []

try:
{chr(10).join('    ' + line for line in code.split(chr(10)))}

    _results.append(('success', 'Code exécuté avec succès'))
except Exception as e:
    _results.append(('error', str(e)))

for status, msg in _results:
    print(f"[{status.upper()}] {{msg}}")
"""
            return self.execute(test_code, language)
        
        return self.execute(code, language)


_executor = None


def get_executor(workspace_path: str = None) -> CodeExecutor:
    """Singleton de l'executor."""
    global _executor
    if _executor is None:
        _executor = CodeExecutor(workspace_path)
    elif workspace_path:
        _executor.workspace_path = Path(workspace_path)
    return _executor
