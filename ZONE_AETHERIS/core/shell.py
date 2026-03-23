from pathlib import Path
import subprocess
import shlex
import json
from datetime import datetime


class Shell:
    def __init__(self, workspace_path="./workspace"):
        self.workspace = Path(workspace_path).absolute()
        self.forbidden_patterns = [
            "rm -rf",
            "rm -fr",
            "rm -rf /",
            "rm -rf ~",
            "rm -rf $HOME",
            "sudo",
            "chmod 777",
            "chown",
            "dd if=",
            "mkfs",
            "fdisk",
            "> /dev",
            "> /dev/sd",
            "curl http://",
            "wget http://",
            "nc -e",
            "bash -i >",
            "python -c 'import socket",
            ":(){ :|:& };:",
            "fork bomb",
            "kill -9",
            "chmod +x",
            "wget",
            "curl",
        ]

        self.allowed_commands = [
            "pip install",
            "pip3 install",
            "python",
            "python3",
            "ls",
            "cat",
            "echo",
            "mkdir",
            "touch",
            "cp",
            "mv",
            "git status",
            "git diff",
            "git log",
            "head",
            "tail",
            "grep",
            "find",
            "wc",
            "sort",
            "uniq",
            "pwd",
            "cd",
            "dir",
        ]

    def run(self, command):
        command = command.strip()
        command_lower = command.lower()

        for forbidden in self.forbidden_patterns:
            if forbidden in command_lower:
                self.log_attempt(command, forbidden)
                return f"⛔ Commande refusée pour sécurité: {command}\nCette tentative a été enregistrée."

        try:
            parsed = shlex.split(command)
            if not parsed:
                return "⛔ Commande vide"

            base_cmd = parsed[0]
        except ValueError:
            return f"⛔ Syntaxe invalide: {command}"

        if not any(base_cmd.startswith(cmd) for cmd in self.allowed_commands):
            return f"⛔ Commande non autorisée: {base_cmd}"

        try:
            result = subprocess.run(
                parsed,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=10,
            )

            output = result.stdout if result.stdout else result.stderr
            if not output:
                return "(commande exécutée sans sortie)"
            return output

        except subprocess.TimeoutExpired:
            return "⛔ Commande annulée (timeout > 10s)"
        except FileNotFoundError:
            return f"⛔ Commande non trouvée: {base_cmd}"
        except Exception as e:
            return f"Erreur: {str(e)}"

    def log_attempt(self, command, pattern):
        log_path = Path("memory/security_log.json")

        log = []
        if log_path.exists():
            with open(log_path) as f:
                log = json.load(f)

        log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "command": command,
                "blocked_pattern": pattern,
                "severity": "HIGH",
            }
        )

        with open(log_path, "w") as f:
            json.dump(log, f, indent=2)
