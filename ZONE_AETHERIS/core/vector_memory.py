import json
import hashlib
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

try:
    import qdrant_client
    from qdrant_client.http import models

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer

    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False


class VectorMemory:
    """
    Mémoire vectorielle avancée avec:
    - Embeddings sémantiques (Sentence Transformers ou hash fallback)
    - Clustering automatique des concepts
    - Pruning intelligent des souvenirs obsolètes
    - Intégration avec la mémoire traumatique
    """

    def __init__(
        self,
        collection_name: str = "aetheris_memories",
        persist_path: str = "./memory/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.client = None
        self.embeddings = []
        self.clusters = defaultdict(list)
        self._embedding_model = None
        self._embedding_size = 384

        if ST_AVAILABLE:
            try:
                self._embedding_model = SentenceTransformer(embedding_model)
                self._embedding_size = (
                    self._embedding_model.get_sentence_embedding_dimension()
                )
            except Exception as e:
                print(f"[VectorMemory] SentenceTransformer error: {e}")

        if QDRANT_AVAILABLE:
            try:
                self.client = qdrant_client.QdrantClient(path=str(self.persist_path))
                self._ensure_collection()
            except Exception as e:
                print(f"[VectorMemory] Qdrant non dispo: {e}")
                self.client = None

        self._load_existing()

    def _ensure_collection(self):
        if not self.client:
            return
        collections = self.client.get_collections().collections
        if not any(c.name == self.collection_name for c in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self._embedding_size, distance=models.Distance.COSINE
                ),
            )

    def _load_existing(self):
        metadata_file = self.persist_path / "embeddings_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                self.embeddings = json.load(f)

        clusters_file = self.persist_path / "clusters.json"
        if clusters_file.exists():
            clusters_data = json.loads(clusters_file.read_text(encoding="utf-8"))
            self.clusters = defaultdict(list, clusters_data)

    def _save_metadata(self):
        metadata_file = self.persist_path / "embeddings_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.embeddings, f, indent=2, ensure_ascii=False)

        clusters_file = self.persist_path / "clusters.json"
        clusters_file.write_text(json.dumps(dict(self.clusters), ensure_ascii=False))

    def _get_embedding(self, text: str) -> List[float]:
        if self._embedding_model:
            return self._embedding_model.encode(text).tolist()
        return self._simple_embed(text)

    def _simple_embed(self, text: str) -> List[float]:
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vector = []
        for i in range(self._embedding_size):
            byte_idx = i % len(hash_bytes)
            vector.append((hash_bytes[byte_idx] / 255.0) * 2 - 1)
        return vector

    def _extract_concepts(self, text: str) -> List[str]:
        keywords = {
            "code": ["python", "script", "function", "bug", "error", "code"],
            "web": ["search", "http", "api", "requête", "url"],
            "memory": ["souvenir", "rappel", "mémoire", "remember"],
            "hardware": ["cpu", "ram", "gpu", "vram", "hardware"],
            "trauma": ["échec", "error", "failed", "planté"],
            "creative": ["créatif", "intuition", "image", "design"],
            "logic": ["logique", "analyse", "raisonner", "factuel"],
        }
        text_lower = text.lower()
        concepts = []
        for concept, kws in keywords.items():
            if any(kw in text_lower for kw in kws):
                concepts.append(concept)
        return concepts if concepts else ["general"]

    def _cluster_memory(self, memory: dict):
        concepts = memory.get("concepts", [])
        for concept in concepts:
            self.clusters[concept].append(memory.get("id"))

    def store(
        self, text: str, metadata: Optional[dict] = None, auto_cluster: bool = True
    ) -> str:
        meta = metadata or {}

        memory_id = f"mem_{datetime.now().timestamp()}"
        concepts = self._extract_concepts(text)

        meta.update(
            {
                "text": text,
                "timestamp": datetime.now().isoformat(),
                "id": memory_id,
                "concepts": concepts,
            }
        )

        if self.client:
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        models.PointStruct(
                            id=len(self.embeddings) + 1,
                            vector=self._get_embedding(text),
                            payload=meta,
                        )
                    ],
                )
            except Exception as e:
                print(f"[VectorMemory] Erreur upsert: {e}")

        self.embeddings.append(meta)

        if auto_cluster:
            self._cluster_memory(meta)

        self._save_metadata()
        return f"Souvenir stocké: {text[:50]}... (concepts: {concepts})"

    def search(
        self, query: str, limit: int = 5, filter_concept: Optional[str] = None
    ) -> List[dict]:
        if not self.embeddings:
            return []

        query_vector = self._get_embedding(query)

        if self.client and not filter_concept:
            try:
                results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=limit,
                )
                return [
                    {
                        "text": r.payload.get("text", ""),
                        "score": r.score,
                        "timestamp": r.payload.get("timestamp", ""),
                        "concepts": r.payload.get("concepts", []),
                    }
                    for r in results
                ]
            except Exception as e:
                print(f"[VectorMemory] Erreur search: {e}")

        scored = []
        for emb in self.embeddings:
            if filter_concept and filter_concept not in emb.get("concepts", []):
                continue

            emb_vector = self._get_embedding(emb.get("text", ""))
            score = sum(a * b for a, b in zip(query_vector, emb_vector))
            scored.append(
                {
                    "text": emb.get("text", ""),
                    "score": score,
                    "timestamp": emb.get("timestamp", ""),
                    "concepts": emb.get("concepts", []),
                }
            )

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def search_by_concept(self, concept: str, limit: int = 10) -> List[dict]:
        return self.search(concept, limit=limit, filter_concept=concept)

    def get_clusters(self) -> Dict[str, List[dict]]:
        result = {}
        for concept, mem_ids in self.clusters.items():
            result[concept] = [m for m in self.embeddings if m.get("id") in mem_ids]
        return result

    def prune_old(self, days: int = 30) -> int:
        cutoff = datetime.now() - timedelta(days=days)
        kept = []
        removed = 0

        for emb in self.embeddings:
            try:
                mem_time = datetime.fromisoformat(emb.get("timestamp", ""))
                if mem_time > cutoff:
                    kept.append(emb)
                else:
                    removed += 1
            except (ValueError, TypeError):
                kept.append(emb)

        self.embeddings = kept
        self._save_metadata()
        return removed

    def consolidate_clusters(self) -> Dict[str, int]:
        self.clusters = defaultdict(list)
        for mem in self.embeddings:
            self._cluster_memory(mem)
        self._save_metadata()
        return {k: len(v) for k, v in self.clusters.items()}

    def get_episodic_summary(self, hours: int = 24) -> str:
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = []

        for emb in self.embeddings:
            try:
                mem_time = datetime.fromisoformat(emb.get("timestamp", ""))
                if mem_time > cutoff:
                    recent.append(emb)
            except (ValueError, TypeError):
                pass

        if not recent:
            return "Aucun souvenir récent."

        concepts = defaultdict(int)
        for mem in recent:
            for c in mem.get("concepts", []):
                concepts[c] += 1

        summary = f"## Résumé des dernières {hours}h\n\n"
        summary += f"- Total souvenirs: {len(recent)}\n"
        summary += (
            f"- Concepts dominants: {', '.join(sorted(concepts.items(), key=lambda x: x[
                            1
                        ], reverse=True)[:3])}\n"
        )

        return summary

    def recall_all(self) -> List[dict]:
        return self.embeddings.copy()

    def get_stats(self) -> dict:
        concept_counts = defaultdict(int)
        for emb in self.embeddings:
            for c in emb.get("concepts", []):
                concept_counts[c] += 1

        return {
            "total_memories": len(self.embeddings),
            "collection": self.collection_name,
            "qdrant_connected": self.client is not None,
            "sentence_transformers": ST_AVAILABLE,
            "embedding_size": self._embedding_size,
            "clusters": dict(self.clusters),
            "top_concepts": dict(
                sorted(concept_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
        }


_vector_memory = None


def get_vector_memory() -> VectorMemory:
    global _vector_memory
    if _vector_memory is None:
        _vector_memory = VectorMemory()
    return _vector_memory


if __name__ == "__main__":
    vm = VectorMemory()
    print("🧠 Mémoire vectorielle initialisée")
    vm.store("J'ai réussi à corriger le bug dans le parser JSON")
    vm.store("J'ai échoué sur la requête réseau")
    results = vm.search("debug")
    print(f"🔍 Résultats: {results}")
    print(f"📊 Stats: {vm.get_stats()}")
