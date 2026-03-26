"""
BICAMERIS - Sandbox Security Validator
=======================================
AST-based security validation for sandbox code execution.
Used only when Docker is unavailable (fallback mode).
"""

import ast
import logging
from typing import List, Set, Optional, Tuple

logger = logging.getLogger(__name__)


BLOCKED_MODULES = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "imaplib",
    "smtplib",
    "telnetlib",
    "threading",
    "_thread",
    "multiprocessing",
    "ctypes",
    "fcntl",
    "pty",
    "tty",
    "termios",
    "resource",
    "signal",
    "pwd",
    "grp",
    "crypt",
    "platform",
    "importlib",
    "__import__",
    "pkgutil",
    "modulefinder",
    "code",
    "codeop",
    "compile",
    "exec",
    "eval",
    "open",
    "file",
}

BLOCKED_FUNCTIONS = {
    "system",
    "popen",
    "spawn",
    "exec",
    "eval",
    "compile",
    "__import__",
    "load_module",
    "find_module",
    "open",
    "file",
    "popener",
    "urlopen",
    "urlretrieve",
}

BLOCKED_ATTRIBUTES = {
    "os.system",
    "os.popen",
    "os.spawn",
    "os.exec",
    "os.kill",
    "os.killpg",
    "subprocess.call",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.check_output",
}


class SecurityValidator:
    """AST-based security validator for Python code (fallback mode)."""

    def __init__(self, allowed_modules: Optional[List[str]] = None):
        self.allowed_modules = set(allowed_modules) if allowed_modules else set()

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        self.errors = []

        if not code or not code.strip():
            return False, ["Empty code"]

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        for node in ast.walk(tree):
            self._check_node(node)

        return len(self.errors) == 0, self.errors

    def _check_node(self, node: ast.AST):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base = alias.name.split(".")[0]
                if base in BLOCKED_MODULES and base not in self.allowed_modules:
                    self.errors.append(f"Blocked module: {alias.name}")

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base = node.module.split(".")[0]
                if base in BLOCKED_MODULES and base not in self.allowed_modules:
                    self.errors.append(f"Blocked module: {node.module}")

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_FUNCTIONS:
                    self.errors.append(f"Blocked function: {node.func.id}")
            elif isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    attr = f"{node.func.value.id}.{node.func.attr}"
                    if attr in BLOCKED_ATTRIBUTES:
                        self.errors.append(f"Blocked attribute: {attr}")

        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                attr = f"{node.value.id}.{node.attr}"
                if attr in BLOCKED_ATTRIBUTES:
                    self.errors.append(f"Blocked attribute: {attr}")


def validate_code_sandbox(
    code: str, allowed_modules: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """Validate code for sandbox execution in fallback mode."""
    validator = SecurityValidator(allowed_modules=allowed_modules)
    return validator.validate(code)
