from dataclasses import dataclass, field


SAFE_COMMANDS = frozenset({
    "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
    "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
})


MODES = {
    "chat": {
        "agents": False,
        "file_read": True,
        "file_write": False,
        "execute": False,
        "web": True,
    },
    "planifier": {
        "agents": False,
        "file_read": True,
        "file_write": True,
        "file_write_exts": frozenset({".md", ".txt", ".json", ".yaml", ".yml", ".toml"}),
        "execute": False,
        "web": True,
    },
    "construire": {
        "agents": True,
        "file_read": True,
        "file_write": True,
        "execute": "confirm",
        "web": True,
    },
    "etudier": {
        "agents": True,
        "file_read": True,
        "file_write": True,
        "file_write_exts": frozenset({".md"}),
        "execute": False,
        "web": True,
    },
}


COMMAND_WHITELISTS = {
    "chat": frozenset({
        "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
        "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
    }),
    "planifier": frozenset({
        "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
        "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
        "git", "git status", "git log", "git diff", "git branch",
        "git show", "git blame", "git remote",
    }),
    "construire": frozenset({
        "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
        "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
        "git", "git status", "git log", "git diff", "git branch",
        "git show", "git blame", "git remote",
        "git add", "git commit", "git push", "git pull", "git checkout",
        "git merge", "git rebase", "git stash", "git fetch",
        "npm", "npm install", "npm run", "npm test", "npm build",
        "npm start", "npm init", "npm ci",
        "yarn", "yarn install", "yarn build", "yarn test", "yarn start",
        "pnpm", "pnpm install", "pnpm run", "pnpm test", "pnpm build",
        "pip", "pip install", "pip uninstall", "pip list", "pip freeze",
        "python", "python3", "node", "npx", "cargo", "cargo build",
        "cargo test", "cargo run", "cargo check", "cargo clippy",
        "make", "cmake", "gcc", "g++", "javac", "java",
        "docker", "docker build", "docker run", "docker ps", "docker stop",
        "docker compose", "docker-compose",
        "mkdir", "touch", "cp", "mv",
    }),
    "etudier": frozenset({
        "cd", "ls", "dir", "pwd", "cat", "type", "head", "tail",
        "grep", "find", "where", "echo", "date", "time", "whoami", "hostname",
        "git", "git status", "git log", "git diff", "git branch",
        "git show", "git blame", "git remote",
        "python", "python3", "node", "pytest", "cargo test",
        "pip list", "pip show",
        "npm test", "npm run",
    }),
}


@dataclass(frozen=True)
class ToolPermissionContext:
    current_mode: str
    auto_confirm: bool = False
    denied_tools: frozenset[str] = field(default_factory=frozenset)
    denied_prefixes: frozenset[str] = field(default_factory=frozenset)
    denied_commands: frozenset[str] = field(default_factory=frozenset)

    def blocks(self, tool_name: str) -> bool:
        if tool_name in self.denied_tools:
            return True
        if tool_name in SAFE_COMMANDS:
            return False
        for prefix in self.denied_prefixes:
            if tool_name.startswith(prefix):
                return True
        return False

    def check(self, action: str, target: str = None) -> dict:
        mode_cfg = MODES.get(self.current_mode, MODES["chat"])
        action_key = action

        if action_key == "agents":
            if mode_cfg.get("agents", False):
                return {"allowed": True, "reason": "agents permitted in this mode", "score": 1.0}
            return {"allowed": False, "reason": "agents not available in this mode", "score": 0.0}

        if action_key == "file_read":
            if mode_cfg.get("file_read", False):
                return {"allowed": True, "reason": "file read permitted", "score": 1.0}
            return {"allowed": False, "reason": "file read denied in this mode", "score": 0.0}

        if action_key == "file_write":
            fw = mode_cfg.get("file_write", False)
            if not fw:
                return {"allowed": False, "reason": "file write denied in this mode", "score": 0.0}
            if target:
                from pathlib import Path
                ext = Path(target).suffix.lower()
                allowed_exts = mode_cfg.get("file_write_exts", None)
                if allowed_exts and ext and ext not in allowed_exts:
                    return {"allowed": False, "reason": f"extension {ext} not permitted in {self.current_mode}", "score": 0.0}
            return {"allowed": True, "reason": "file write permitted", "score": 1.0}

        if action_key == "execute":
            exec_val = mode_cfg.get("execute", False)
            if exec_val is False:
                return {"allowed": False, "reason": "command execution denied in this mode", "score": 0.0}
            if exec_val == "confirm":
                if self.auto_confirm:
                    return {"allowed": True, "reason": "auto-confirmed", "score": 1.0}
                return {"allowed": "confirm", "reason": "command execution requires confirmation", "score": 0.5}
            return {"allowed": True, "reason": "command execution permitted", "score": 1.0}

        if action_key == "web":
            if mode_cfg.get("web", False):
                return {"allowed": True, "reason": "web access permitted", "score": 1.0}
            return {"allowed": False, "reason": "web access denied in this mode", "score": 0.0}

        return {"allowed": False, "reason": f"unknown action: {action}", "score": 0.0}

    def allows_file_extension(self, ext: str) -> bool:
        mode_cfg = MODES.get(self.current_mode, MODES["chat"])
        if not mode_cfg.get("file_write", False):
            return False
        ext_lower = ext.lower() if not ext.startswith(".") else ext.lower()
        allowed_exts = mode_cfg.get("file_write_exts", None)
        if allowed_exts is None:
            return True
        return ext_lower in allowed_exts

    def get_command_permission(self, cmd: str) -> dict:
        if self.blocks(cmd):
            return {"allowed": False, "reason": f"command {cmd} is blocked", "score": 0.0}
        base_cmd = cmd.split()[0] if cmd else ""
        if base_cmd in SAFE_COMMANDS or cmd in SAFE_COMMANDS:
            return {"allowed": True, "reason": "safe command", "score": 1.0}
        whitelist = COMMAND_WHITELISTS.get(self.current_mode, frozenset())
        if cmd in whitelist or base_cmd in whitelist:
            mode_cfg = MODES.get(self.current_mode, MODES["chat"])
            exec_val = mode_cfg.get("execute", False)
            if exec_val == "confirm":
                if self.auto_confirm:
                    return {"allowed": True, "reason": "auto-confirmed whitelisted command", "score": 1.0}
                return {"allowed": "confirm", "reason": f"whitelisted command requires confirmation", "score": 0.5}
            if exec_val is False:
                return {"allowed": False, "reason": "execution disabled in this mode", "score": 0.0}
            return {"allowed": True, "reason": "whitelisted command", "score": 1.0}
        return {"allowed": False, "reason": f"command {cmd} not in whitelist", "score": 0.0}


_permission_context: ToolPermissionContext = None


def get_permission_context(current_mode: str = "chat", auto_confirm: bool = False) -> ToolPermissionContext:
    global _permission_context
    _permission_context = ToolPermissionContext(
        current_mode=current_mode,
        auto_confirm=auto_confirm
    )
    return _permission_context
