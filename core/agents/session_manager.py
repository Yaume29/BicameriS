from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime


@dataclass
class SessionState:
    conversation_id: str
    current_mode: str
    current_theme: Optional[str] = None
    current_subtheme: Optional[str] = None
    workspace_id: Optional[str] = None
    auto_confirm: bool = False
    turn_count: int = 0
    messages: List[dict] = field(default_factory=list)
    pending_tool_calls: List[dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""


class SessionManager:
    def __init__(self, storage_dir: Path):
        self.storage_dir = Path(storage_dir) / "sessions"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, conversation_id: str) -> Path:
        return self.storage_dir / f"{conversation_id}.json"

    def save(self, state: SessionState) -> None:
        now = datetime.now().isoformat()
        if not state.created_at:
            state.created_at = now
        state.updated_at = now
        state.messages = state.messages[-20:]
        path = self._session_path(state.conversation_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(state), f, indent=2, ensure_ascii=False)

    def load(self, conversation_id: str) -> Optional[SessionState]:
        path = self._session_path(conversation_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return SessionState(**data)

    def list_sessions(self) -> List[dict]:
        sessions = []
        for path in self.storage_dir.glob("*.json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "conversation_id": data["conversation_id"],
                "current_mode": data["current_mode"],
                "turn_count": data["turn_count"],
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "message_count": len(data.get("messages", [])),
            })
        sessions.sort(key=lambda s: s["updated_at"], reverse=True)
        return sessions

    def delete(self, conversation_id: str) -> None:
        path = self._session_path(conversation_id)
        if path.exists():
            path.unlink()


_instance: Optional[SessionManager] = None


def get_session_manager(storage_dir: Optional[Path] = None) -> SessionManager:
    global _instance
    if _instance is None:
        if storage_dir is None:
            storage_dir = Path.home() / ".aetheris"
        _instance = SessionManager(storage_dir)
    return _instance
