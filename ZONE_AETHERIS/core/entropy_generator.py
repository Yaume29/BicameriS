import hashlib
import time
import random
import os
from datetime import datetime
from pathlib import Path


class EntropyGenerator:
    """
    Génère une empreinte unique pour chaque instance d'Aetheris.
    Combine: timestamp, entropy système, processus, mémoire disponible.
    """

    def __init__(self):
        self.base_entropy = self._collect_entropy()
        self.seed = self._generate_seed()

    def _collect_entropy(self):
        """Collecte l'entropie du système"""
        sources = [
            str(time.time_ns()),
            str(os.urandom(32).hex()),
            str(os.getpid()),
            str(datetime.now().microsecond),
            str(random.getrandbits(256)),
        ]
        return ".".join(sources)

    def _generate_seed(self):
        """Génère un seed unique iréproductible"""
        hash_obj = hashlib.sha256(self.base_entropy.encode())
        return hash_obj.hexdigest()[:32]

    def get_seed(self):
        """Retourne le seed généré"""
        return self.seed

    def get_snapshot(self):
        """Snapshot de l'état actuel"""
        return {
            "seed": self.seed,
            "timestamp": datetime.now().isoformat(),
            "entropy": hashlib.sha256(self.base_entropy.encode()).hexdigest()[:16],
            "pid": os.getpid(),
            "microsecond": datetime.now().microsecond,
        }

    def regenerate(self):
        """Régénère un nouveau seed (nécessite confirmation)"""
        self.base_entropy = self._collect_entropy()
        self.seed = self._generate_seed()
        return self.seed

    def compare_with(self, old_snapshot):
        """Compare l'état actuel avec un ancien snapshot"""
        current = self.get_snapshot()
        return {
            "same_seed": current["seed"] == old_snapshot.get("seed"),
            "timestamp_delta": current["timestamp"],
            "old_timestamp": old_snapshot.get("timestamp"),
            "entropy_changed": current["entropy"] != old_snapshot.get("entropy"),
        }


def get_entropy_generator():
    """Singleton"""
    global _entropy_instance
    if _entropy_instance is None:
        _entropy_instance = EntropyGenerator()
    return _entropy_instance


_entropy_instance = None

if __name__ == "__main__":
    eg = EntropyGenerator()
    print(f"🎲 Seed généré: {eg.get_seed()}")
    snapshot = eg.get_snapshot()
    print(f"📸 Snapshot: {snapshot}")
