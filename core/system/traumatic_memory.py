"""
Traumatic Memory RAG - Mémoire des Échecs
Interroge les souvenirs d'échecs passés pour éviter les mêmes erreurs.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class TraumaticMemory:
    """
    Mémoire traumatique qui stocke les échecs passés.

    Quand l'utilisateur fait une requête, le système:
    1. Cherche des similarités avec d'anciens échecs
    2. Injecte ces "traumas" dans le contexte du Coder
    3. Force une approche différente
    """

    def __init__(
        self,
        storage_path: Optional[str] = "ZONE_RESERVEE/logs/traumatic_memory.json",
        storage_dir: Optional[str] = None,
    ):
        if storage_dir:
            storage_path = str(Path(storage_dir) / "traumatic_memory.json")
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._memories = self._load()

    def _load(self) -> List[Dict]:
        if self.storage_path.exists():
            try:
                return json.loads(self.storage_path.read_text(encoding="utf-8"))
            except:
                return []
        return []

    def _save(self):
        self.storage_path.write_text(
            json.dumps(self._memories, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def add_failure(self, query: str, error: str, context: str = "", severity: str = "medium"):
        """Enregistre un échec"""
        memory = {
            "id": f"trauma_{datetime.now().timestamp()}",
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "error": error,
            "context": context,
            "severity": severity,
            "retry_count": 0,
        }

        self._memories.append(memory)

        if len(self._memories) > 200:
            self._memories = self._memories[-100:]

        self._save()

    def increment_retry(self, trauma_id: str):
        """Incrément le compteur de tentatives"""
        for m in self._memories:
            if m.get("id") == trauma_id:
                m["retry_count"] = m.get("retry_count", 0) + 1
                self._save()
                break

    def resolve_failure(self, query: str) -> bool:
        """
        Guérit un trauma après un succès.
        Marque le trauma comme 'guéri' et incrémente le compteur de réussites.
        """
        query_words = set(query.lower().split())

        for m in self._memories:
            if m.get("error"):
                mem_words = set(m.get("query", "").lower().split())
                if query_words & mem_words:
                    m["healed"] = True
                    m["healed_at"] = datetime.now().isoformat()
                    m["healed_count"] = m.get("healed_count", 0) + 1

        self._save()
        return True

    def query_similar(self, user_query: str, limit: int = 3) -> List[Dict]:
        """
        Cherche des souvenirs similaires à la requête.
        Utilise un matching simple sur les mots-clés.
        """
        query_words = set(user_query.lower().split())

        scored_memories = []

        for memory in self._memories:
            if memory.get("error"):
                memory_words = set(memory.get("query", "").lower().split())
                common = query_words & memory_words
                score = len(common)

                if score > 0:
                    scored_memories.append({"score": score, "memory": memory})

        scored_memories.sort(key=lambda x: x["score"], reverse=True)

        return [item["memory"] for item in scored_memories[:limit]]

    def get_context_injection(self, similar_memories: List[Dict]) -> str:
        """
        Génère l'injection de contexte pour le Coder.
        """
        if not similar_memories:
            return ""

        injection = "\n[TRAUMATIC MEMORY - Souvenirs d'échecs similaires]\n"

        for mem in similar_memories:
            injection += f"""
❌ ÉCHEC PASSÉ #{mem.get("id", "unknown")}
   Requête: {mem.get("query", "")[:100]}
   Erreur: {mem.get("error", "")[:150]}
   Tentatives: {mem.get("retry_count", 0)}
   ---
"""

        injection += "\n⚠️ ATTENTION: Ces requêtes ont déjà échoué. Approche différente requise.\n"

        return injection

    def get_recent_failures(self, hours: int = 24, limit: int = 10) -> List[Dict]:
        """Retourne les échecs récents"""
        cutoff = datetime.now() - timedelta(hours=hours)

        recent = []
        for m in self._memories:
            try:
                mem_time = datetime.fromisoformat(m.get("timestamp", ""))
                if mem_time > cutoff:
                    recent.append(m)
            except:
                pass

        return recent[-limit:]

    def get_stats(self) -> Dict:
        """Statistiques des traumas"""
        return {
            "total_memories": len(self._memories),
            "total_failures": len(self._memories),
            "recent_24h": len(self.get_recent_failures(24)),
            "retry_counts": {
                "0": len([m for m in self._memories if m.get("retry_count", 0) == 0]),
                "1-3": len([m for m in self._memories if 1 <= m.get("retry_count", 0) <= 3]),
                "3+": len([m for m in self._memories if m.get("retry_count", 0) > 3]),
            },
        }


_traumatic_memory = None


def get_traumatic_memory() -> TraumaticMemory:
    global _traumatic_memory
    if _traumatic_memory is None:
        _traumatic_memory = TraumaticMemory()
    return _traumatic_memory
