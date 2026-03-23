"""
Paradoxical Sleep - Vector Compression & Memory Digestion
Cycle de rêve et de digestion quand l'entité n'est pas sollicitée.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict


class ParadoxicalSleep:
    """
    Simule le sommeil paradoxal d'Aetheris.

    Quand inactive (idle), l'entité:
    1. Relit les logs d'erreurs récents
    2. Regroupe les concepts similaires (vector compression)
    3. Rédige un "Rapport d'Évolution"
    4. Efface les logs bruts pour économiser les tokens
    """

    def __init__(
        self,
        logs_dir: str = "ZONE_RESERVEE/logs",
        journal_path: str = "ZONE_AETHERIS/memory/journal.md",
        memory_db: str = "ZONE_AETHERIS/memory/memories.json",
    ):
        self.logs_dir = Path(logs_dir)
        self.journal_path = Path(journal_path)
        self.memory_db = Path(memory_db)
        self.last_digest = datetime.now()
        self.idle_threshold = timedelta(minutes=5)
        self._errors_cache = []

    def is_idle(self, last_interaction: datetime) -> bool:
        """Vérifie si l'entité est inactive depuis assez longtemps"""
        return (datetime.now() - last_interaction) > self.idle_threshold

    def collect_recent_errors(self) -> List[Dict]:
        """Collecte les erreurs récentes de la sandbox et des logs"""
        errors = []

        sandbox_dir = Path("ZONE_RESERVEE/sandbox")
        if sandbox_dir.exists():
            for f in sandbox_dir.glob("*.err"):
                try:
                    content = f.read_text(encoding="utf-8")
                    if content:
                        errors.append(
                            {
                                "source": "sandbox",
                                "file": f.name,
                                "error": content[:500],
                                "timestamp": datetime.fromtimestamp(
                                    f.stat().st_mtime
                                ).isoformat(),
                            }
                        )
                except (IOError, OSError):
                    pass

        flux_log = self.logs_dir / "flux_log.json"
        if flux_log.exists():
            try:
                data = json.loads(flux_log.read_text(encoding="utf-8"))
                for entry in data:
                    if entry.get("type") == "ERREUR":
                        errors.append(
                            {
                                "source": "flux",
                                "error": entry.get("message", "")[:500],
                                "timestamp": entry.get("timestamp", ""),
                            }
                        )
            except (json.JSONDecodeError, IOError):
                pass

        self._errors_cache = errors
        return errors

    def analyze_concepts(self, memories: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Regroupe les concepts similaires pour compresser la mémoire.
        Retourne un dictionnaire {concept_cluster: [memories]}
        """
        clusters = defaultdict(list)

        keywords = {
            "code": ["python", "script", "function", "bug", "error"],
            "web": ["search", "http", "api", "requête"],
            "memory": ["souvenir", "rappel", "context"],
            "sandbox": ["exécution", "timeout", "résultat"],
            "hardware": ["cpu", "ram", "gpu", "vram", "pulse"],
        }

        for memory in memories:
            content = memory.get("content", "").lower()
            matched = False

            for cluster_name, cluster_keywords in keywords.items():
                if any(kw in content for kw in cluster_keywords):
                    clusters[cluster_name].append(memory)
                    matched = True
                    break

            if not matched:
                clusters["autres"].append(memory)

        return dict(clusters)

    def generate_evolution_report(self, errors: List[Dict], clusters: Dict) -> str:
        """Génère le rapport d'évolution"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        report = f"""
# 📝 Rapport d'Évolution - {timestamp}

## Erreurs Récentes
"""
        if errors:
            for e in errors[:5]:
                report += f"- **{e.get('source', 'unknown')}**: {e.get('error', '')[:100]}...\n"
        else:
            report += "_Aucune erreur récente_\n"

        report += "\n## Clusters de Concepts\n"
        for cluster, mems in clusters.items():
            report += f"- **{cluster}**: {len(mems)} souvenirs\n"

        report += f"\n## Statistiques\n"
        report += f"- Erreurs analysées: {len(errors)}\n"
        report += f"- Concepts regroupés: {sum(len(v) for v in clusters.values())}\n"
        report += f"- Dernière digestion: {self.last_digest.isoformat()}\n"

        report += "\n---\n"

        return report

    def compress_memory(self) -> Dict[str, Any]:
        """
        Effectue la compression de mémoire et génère le rapport.
        """
        self.last_digest = datetime.now()

        errors = self.collect_recent_errors()

        memories = []
        if self.memory_db.exists():
            try:
                memories = json.loads(self.memory_db.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                memories = []

        clusters = self.analyze_concepts(memories)

        report = self.generate_evolution_report(errors, clusters)

        self.append_to_journal(report)

        return {
            "timestamp": self.last_digest.isoformat(),
            "errors_found": len(errors),
            "clusters": {k: len(v) for k, v in clusters.items()},
            "report": report,
        }

    def append_to_journal(self, content: str):
        """Ajoute au journal"""
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)

        existing = ""
        if self.journal_path.exists():
            existing = self.journal_path.read_text(encoding="utf-8")

        self.journal_path.write_text(existing + content, encoding="utf-8")

    def cleanup_old_logs(self, keep_last: int = 100):
        """Nettoie les vieux logs pour économiser l'espace"""
        sandbox_dir = Path("ZONE_RESERVEE/sandbox")

        if not sandbox_dir.exists():
            return {"cleaned": 0}

        files = list(sandbox_dir.glob("*.err")) + list(sandbox_dir.glob("*.out"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        removed = 0
        for f in files[keep_last:]:
            try:
                f.unlink()
                removed += 1
            except (OSError, IOError):
                pass

        return {"cleaned": removed, "kept": min(len(files), keep_last)}

    def get_stats(self) -> Dict:
        """Statistiques du sommeil"""
        return {
            "last_digest": self.last_digest.isoformat(),
            "idle_threshold_minutes": self.idle_threshold.seconds // 60,
            "errors_cached": len(self._errors_cache),
            "is_idle": self.is_idle(self.last_digest),
        }


# Instance globale
_paradoxical_sleep = None


def get_paradoxical_sleep() -> ParadoxicalSleep:
    global _paradoxical_sleep
    if _paradoxical_sleep is None:
        _paradoxical_sleep = ParadoxicalSleep()
    return _paradoxical_sleep
