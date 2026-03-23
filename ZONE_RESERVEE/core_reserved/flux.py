import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum


class FluxType(Enum):
    PENSEE = "pensee"
    COMMANDE = "commande"
    FICHIER_CREE = "fichier_cree"
    FICHIER_MODIFIE = "fichier_modifie"
    AGENT_CREE = "agent_cree"
    AGENT_CHARGE = "agent_charge"
    ERREUR = "erreur"
    SYSTEM = "system"
    MIROIR = "miroir"
    MEMOIRE = "memoire"
    CHAT_ENVOYE = "chat_envoye"
    CHAT_RECU = "chat_recu"
    INCEPTION = "inception"
    WAKEUP = "wakeup"
    MEDITATION = "meditation"
    REFLEXION = "reflexion"


class FluxLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


ICONS = {
    FluxType.PENSEE: "💭",
    FluxType.COMMANDE: "⚡",
    FluxType.FICHIER_CREE: "📄",
    FluxType.FICHIER_MODIFIE: "✏️",
    FluxType.AGENT_CREE: "🧠",
    FluxType.AGENT_CHARGE: "🔗",
    FluxType.ERREUR: "⚠️",
    FluxType.SYSTEM: "🔧",
    FluxType.MIROIR: "🪞",
    FluxType.MEMOIRE: "🧬",
    FluxType.CHAT_ENVOYE: "📤",
    FluxType.CHAT_RECU: "📥",
    FluxType.INCEPTION: "🎯",
    FluxType.WAKEUP: "🌅",
    FluxType.MEDITATION: "🧘",
    FluxType.REFLEXION: "🧠",
}


class FluxLogger:
    def __init__(self, log_file: str = "ZONE_RESERVEE/logs/flux_log.json"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self._save_logs([])

    def _load_logs(self) -> List[Dict]:
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []

    def _save_logs(self, logs: List[Dict]):
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    def log(
        self,
        flux_type: FluxType,
        message: str,
        details: Optional[Dict] = None,
        level: FluxLevel = FluxLevel.INFO,
    ):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": flux_type.value,
            "icon": ICONS.get(flux_type, "•"),
            "message": message,
            "details": details or {},
            "level": level.value,
        }

        logs = self._load_logs()
        logs.append(entry)

        if len(logs) > 1000:
            logs = logs[-1000:]

        self._save_logs(logs)
        return entry

    def get_logs(
        self, limit: int = 100, flux_type: Optional[FluxType] = None
    ) -> List[Dict]:
        logs = self._load_logs()

        if flux_type:
            logs = [l for l in logs if l.get("type") == flux_type.value]

        return logs[-limit:]

    def get_logs_by_type(self) -> Dict[str, int]:
        logs = self._load_logs()
        counts = {}
        for log in logs:
            t = log.get("type", "unknown")
            counts[t] = counts.get(t, 0) + 1
        return counts

    def get_stats(self) -> Dict:
        logs = self._load_logs()
        by_type = self.get_logs_by_type()

        by_level = {}
        for log in logs:
            lvl = log.get("level", "info")
            by_level[lvl] = by_level.get(lvl, 0) + 1

        return {
            "total": len(logs),
            "by_type": by_type,
            "by_level": by_level,
            "last_entry": logs[-1] if logs else None,
        }


_flux_logger = None


def get_flux_logger() -> FluxLogger:
    global _flux_logger
    if _flux_logger is None:
        _flux_logger = FluxLogger()
    return _flux_logger
