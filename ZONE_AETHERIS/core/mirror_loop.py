import json
import os
from pathlib import Path
from datetime import datetime
from core.entropy_generator import EntropyGenerator


class MirrorLoop:
    """
    Boucle de miroir: Aetheris s'observe, compare son état, peut se modifier.
    """

    def __init__(self, memory_path="./memory"):
        self.memory_path = Path(memory_path)
        self.snapshots_path = self.memory_path / "snapshots"
        self.snapshots_path.mkdir(parents=True, exist_ok=True)
        self.entropy = EntropyGenerator()
        self.current_snapshot = None

    def create_snapshot(self):
        """Crée un snapshot de l'état actuel"""
        snapshot = {
            "id": self.entropy.get_seed(),
            "timestamp": datetime.now().isoformat(),
            "seed": self.entropy.get_seed(),
            "entropy_snapshot": self.entropy.get_snapshot(),
            "thought_patterns": [],
            "decisions": [],
            "reflections": [],
            "version": "1.1",
        }

        self.current_snapshot = snapshot
        self._save_snapshot(snapshot)
        return snapshot

    def _save_snapshot(self, snapshot):
        """Sauvegarde le snapshot"""
        filename = f"snapshot_{snapshot['timestamp'].replace(':', '-')}.json"
        path = self.snapshots_path / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

    def introspect(self):
        """Regarde dans le miroir - retourne le manifeste"""
        from agents.aetheris_agent import introspect

        return introspect()

    def compare_with_previous(self):
        """Compare l'état actuel avec le snapshot précédent"""
        snapshots = sorted(self.snapshots_path.glob("snapshot_*.json"))
        if len(snapshots) < 2:
            return {"message": "Pas assez de snapshots pour comparer"}

        with open(snapshots[-2], "r", encoding="utf-8") as f:
            old = json.load(f)
        with open(snapshots[-1], "r", encoding="utf-8") as f:
            new = json.load(f)

        return {
            "old_id": old.get("id"),
            "new_id": new.get("id"),
            "same_identity": old.get("id") == new.get("id"),
            "time_elapsed": new.get("timestamp"),
            "reflections": new.get("reflections", []),
        }

    def reflect(self, reflection_text):
        """Ajoute une réflexion au snapshot actuel"""
        if not self.current_snapshot:
            self.create_snapshot()

        reflection = {"timestamp": datetime.now().isoformat(), "text": reflection_text}

        if self.current_snapshot is not None:
            self.current_snapshot.setdefault("reflections", []).append(reflection)
            self._save_snapshot(self.current_snapshot)

        return "Réflexion ajoutée au miroir"

    def get_all_snapshots(self):
        """Liste tous les snapshots"""
        return [f.name for f in sorted(self.snapshots_path.glob("snapshot_*.json"))]


_mirror_instance = None


def get_mirror_loop():
    global _mirror_instance
    if _mirror_instance is None:
        _mirror_instance = MirrorLoop()
    return _mirror_instance


if __name__ == "__main__":
    mirror = MirrorLoop()
    print("🪞 Boucle miroir initialisée")
    snapshot = mirror.create_snapshot()
    print(f"📸 Snapshot créé: {snapshot['id'][:16]}...")
