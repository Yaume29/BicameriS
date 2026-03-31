from dataclasses import dataclass
from typing import Optional

from core.agents.tool_permission import (
    ToolPermissionContext,
    COMMAND_WHITELISTS,
    MODES,
    SAFE_COMMANDS,
)


@dataclass(frozen=True)
class CommandResult:
    command: str
    score: float
    allowed: bool
    needs_confirm: bool
    reason: str


class CommandRouter:

    def __init__(self):
        self._safe_commands = frozenset({
            "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
            "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
        })

    def score(self, command: str, context: ToolPermissionContext) -> float:
        base_cmd = command.split()[0] if command else ""
        whitelist = COMMAND_WHITELISTS.get(context.current_mode, frozenset())

        if command in whitelist:
            return 1.0

        if any(command.startswith(w + " ") for w in whitelist):
            return 0.9

        if base_cmd in self._safe_commands:
            return 0.7

        cfg = MODES.get(context.current_mode, MODES["chat"])
        exec_val = cfg.get("execute", False)

        if exec_val == "confirm":
            if context.auto_confirm:
                return 1.0
            return 0.5

        return 0.0

    def route(self, command: str, context: ToolPermissionContext) -> CommandResult:
        base_cmd = command.split()[0] if command else ""
        whitelist = COMMAND_WHITELISTS.get(context.current_mode, frozenset())

        if context.blocks(command) or context.blocks(base_cmd):
            return CommandResult(
                command=command,
                score=0.0,
                allowed=False,
                needs_confirm=False,
                reason=f"command {command} is blocked",
            )

        if command in whitelist:
            return CommandResult(
                command=command,
                score=1.0,
                allowed=True,
                needs_confirm=False,
                reason="exact whitelist match",
            )

        if any(command.startswith(w + " ") for w in whitelist):
            return CommandResult(
                command=command,
                score=0.9,
                allowed=True,
                needs_confirm=False,
                reason="prefix whitelist match",
            )

        if base_cmd in self._safe_commands:
            return CommandResult(
                command=command,
                score=0.7,
                allowed=True,
                needs_confirm=False,
                reason="safe command",
            )

        cfg = MODES.get(context.current_mode, MODES["chat"])
        exec_val = cfg.get("execute", False)

        if exec_val == "confirm":
            if context.auto_confirm:
                return CommandResult(
                    command=command,
                    score=1.0,
                    allowed=True,
                    needs_confirm=False,
                    reason="auto-confirmed",
                )
            return CommandResult(
                command=command,
                score=0.5,
                allowed=True,
                needs_confirm=True,
                reason="requires confirmation",
            )

        return CommandResult(
            command=command,
            score=0.0,
            allowed=False,
            needs_confirm=False,
            reason=f"command {command} not permitted",
        )

    def is_safe_command(self, command: str) -> bool:
        base_cmd = command.split()[0] if command else ""
        return base_cmd in self._safe_commands


_router_instance: Optional[CommandRouter] = None


def get_command_router() -> CommandRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = CommandRouter()
    return _router_instance
