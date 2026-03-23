import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List


class EvolvingJournal:
    """
    Journal évolutif: Aetheris peut le relire, l'annotater, le réécrire.
    """

    def __init__(self, journal_path="./memory/journal.md"):
        self.journal_path = Path(journal_path)
        self.annotations_path = self.journal_path.parent / "journal_annotations.json"
        self.annotations = self._load_annotations()

    def _load_annotations(self) -> dict:
        """Charge les annotations existantes"""
        if self.annotations_path.exists():
            with open(self.annotations_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_annotations(self):
        """Sauvegarde les annotations"""
        with open(self.annotations_path, "w", encoding="utf-8") as f:
            json.dump(self.annotations, f, indent=2, ensure_ascii=False)

    def read(self) -> str:
        """Lit le journal entier"""
        if self.journal_path.exists():
            return self.journal_path.read_text(encoding="utf-8")
        return ""

    def append(self, entry: str):
        """Ajoute une entrée au journal"""
        timestamp = datetime.now().isoformat()
        with open(self.journal_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {timestamp}\n{entry}\n")
        return f"Entrée ajoutée: {timestamp}"

    def annotate_entry(self, entry_index: int, annotation: str):
        """Annotate une entrée spécifique"""
        key = f"entry_{entry_index}"
        if key not in self.annotations:
            self.annotations[key] = []

        self.annotations[key].append(
            {"timestamp": datetime.now().isoformat(), "annotation": annotation}
        )

        self._save_annotations()
        return f"Annotation ajoutée à l'entrée {entry_index}"

    def get_annotations(self, entry_index: int) -> List[dict]:
        """Récupère les annotations d'une entrée"""
        key = f"entry_{entry_index}"
        return self.annotations.get(key, [])

    def rewrite_entry(self, entry_index: int, new_content: str):
        """Réécrit une entrée (ajoute une note de correction)"""
        correction = {
            "timestamp": datetime.now().isoformat(),
            "original_index": entry_index,
            "new_content": new_content,
        }

        key = "corrections"
        if key not in self.annotations:
            self.annotations[key] = []

        self.annotations[key].append(correction)
        self._save_annotations()

        entry_marker = f"## "
        lines = self.journal_path.read_text(encoding="utf-8").splitlines()

        if 0 <= entry_index < len(lines):
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(f"\n### Correction #{entry_index}\n{new_content}\n")

        return f"Correction ajoutée pour entrée {entry_index}"

    def get_history(self) -> List[dict]:
        """Retourne l'historique du journal"""
        history = []
        lines = (
            self.journal_path.read_text(encoding="utf-8").splitlines()
            if self.journal_path.exists()
            else []
        )

        current_entry = {}
        for i, line in enumerate(lines):
            if line.startswith("## "):
                if current_entry:
                    history.append(current_entry)
                current_entry = {
                    "index": len(history),
                    "timestamp": line.replace("## ", "").strip(),
                    "content": [],
                }
            elif line.strip():
                current_entry.setdefault("content", []).append(line)

        if current_entry:
            history.append(current_entry)

        return history

    def search(self, query: str) -> List[dict]:
        """Recherche dans le journal"""
        content = self.read().lower()
        query_lower = query.lower()

        results = []
        lines = (
            self.journal_path.read_text(encoding="utf-8").splitlines()
            if self.journal_path.exists()
            else []
        )

        for i, line in enumerate(lines):
            if query_lower in line.lower():
                results.append({"line": i + 1, "content": line.strip()})

        return results


_evolution_journal = None


def get_evolution_journal():
    global _evolution_journal
    if _evolution_journal is None:
        _evolution_journal = EvolvingJournal()
    return _evolution_journal


if __name__ == "__main__":
    ej = EvolvingJournal()
    print("📖 Journal évolutif initialisé")
    print(f"Longueur: {len(ej.read())} caractères")
