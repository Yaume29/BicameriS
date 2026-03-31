from pathlib import Path
from typing import Optional
from core.agents.tool_registry import register_tool, get_tool_registry


class SimpleToolSet:
    def __init__(self, workspace_root: Path = None):
        self.workspace_root = workspace_root or Path(".")

    def read_file(self, path: str) -> str:
        try:
            target = self.workspace_root / path if not Path(path).is_absolute() else Path(path)
            return target.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except Exception as e:
            return f"Error: {e}"

    def list_files(self, pattern: str = "*") -> str:
        try:
            matches = sorted(self.workspace_root.glob(pattern))
            if not matches:
                return "No files found."
            lines = []
            for m in matches:
                suffix = "/" if m.is_dir() else ""
                lines.append(f"{m.relative_to(self.workspace_root)}{suffix}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

    def search_content(self, query: str, path: str = ".") -> str:
        try:
            target = self.workspace_root / path
            if target.is_file():
                targets = [target]
            else:
                targets = sorted(target.rglob("*"))
            results = []
            for f in targets:
                if not f.is_file():
                    continue
                try:
                    lines = f.read_text(encoding="utf-8").splitlines()
                except (UnicodeDecodeError, PermissionError):
                    continue
                for i, line in enumerate(lines, 1):
                    if query in line:
                        rel = f.relative_to(self.workspace_root)
                        results.append(f"{rel}:{i}: {line.rstrip()}")
            if not results:
                return "No matches found."
            return "\n".join(results)
        except Exception as e:
            return f"Error: {e}"


def register_simple_tools(registry=None):
    tools = SimpleToolSet()

    register_tool(
        name="read_file",
        description="Read the content of a file by path",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"]
        },
        function=tools.read_file,
        category="simple",
        enabled=False
    )

    register_tool(
        name="list_files",
        description="List files matching a glob pattern",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern", "default": "*"}
            }
        },
        function=tools.list_files,
        category="simple",
        enabled=False
    )

    register_tool(
        name="search_content",
        description="Search for text content in files",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to search for"},
                "path": {"type": "string", "description": "Directory or file to search in", "default": "."}
            },
            "required": ["query"]
        },
        function=tools.search_content,
        category="simple",
        enabled=False
    )
