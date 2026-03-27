"""
BICAMERIS - Hippocampus
======================
Vector memory wrapper using Qdrant.
Provides semantic search and payload filtering for thoughts, tasks, and trauma.
"""

import logging
import uuid
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from core.system.retry import retry

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    models = None


@dataclass
class StoredThought:
    """Thought stored in Qdrant with payload"""

    id: str
    content: str
    timestamp: str
    context: str
    type: str
    status: str
    pulse_context: float


@dataclass
class StoredTask:
    """Task stored in Qdrant with payload"""

    id: str
    description: str
    timestamp: str
    priority: str
    status: str
    assigned_to: Optional[str]


class Hippocampus:
    """
    Vector memory manager using Qdrant.
    Handles semantic search and payload filtering for cognition.
    """

    def __init__(self, host: str = "localhost", port: int = 6333):
        self.host = host
        self.port = port
        self.client = None
        self._initialized = False
        self._embedding_model = None
        self._init_client()

        import threading
        threading.Thread(target=self._get_embedding_model, daemon=True, name="NLP_Prewarm").start()

    def _get_embedding_model(self):
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logging.info("[Hippocampus] Chargement du modèle d'embedding (MiniLM)...")
                self._embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logging.error(f"[Hippocampus] Erreur modèle NLP: {e}")
        return self._embedding_model

    def _init_client(self):
        """Initialize Qdrant client"""
        if not QDRANT_AVAILABLE:
            logging.warning("[Hippocampus] Qdrant non installé - mode dégradé")
            return

        try:
            self.client = QdrantClient(host=self.host, port=self.port)
            self._ensure_collections()
            self._initialized = True
            logging.info(f"[Hippocampus] ✅ Connecté à Qdrant ({self.host}:{self.port})")
        except Exception as e:
            logging.warning(f"[Hippocampus] ⚠️ Connexion échouée: {e}")
            self.client = None

    def _ensure_collections(self):
        """Create collections if they don't exist"""
        collections = ["aetheris_thoughts", "aetheris_tasks", "aetheris_trauma", "synaptic_tools"]

        for coll in collections:
            try:
                collections_info = self.client.get_collections().collections
                collection_names = [c.name for c in collections_info]

                if coll not in collection_names:
                    self.client.create_collection(
                        collection_name=coll,
                        vectors_config=models.VectorParams(
                            size=384,  # Default for sentence-transformers
                            distance=models.Distance.COSINE,
                        ),
                    )
                    logging.info(f"[Hippocampus] ✅ Collection créée: {coll}")
            except Exception as e:
                logging.warning(f"[Hippocampus] Erreur création {coll}: {e}")

    @retry(exceptions=(Exception,), max_attempts=4, base_delay=2, backoff="exponential")
    def log_thought(self, thought: StoredThought, vector: List[float] = None):
        """Store a thought in vector memory"""
        if not self.client or not self._initialized:
            return False

        self.client.upsert(
            collection_name="aetheris_thoughts",
            points=[
                models.PointStruct(
                    id=thought.id, vector=vector or [0.0] * 384, payload=asdict(thought)
                )
            ],
        )
        return True

    @retry(exceptions=(Exception,), max_attempts=4, base_delay=2, backoff="exponential")
    def log_task(self, task: StoredTask, vector: List[float] = None):
        """Store a task in vector memory"""
        if not self.client or not self._initialized:
            return False

        self.client.upsert(
            collection_name="aetheris_tasks",
            points=[
                models.PointStruct(
                    id=task.id, vector=vector or [0.0] * 384, payload=asdict(task)
                )
            ],
        )
        return True

    def search_thoughts(
        self, query_vector: List[float], limit: int = 5, status: str = None, min_pulse: float = None
    ) -> List[StoredThought]:
        """Search thoughts by semantic similarity with payload filtering"""
        if not self.client or not self._initialized:
            return []

        filters = []
        if status:
            filters.append(
                models.FieldCondition(key="status", match=models.MatchValue(value=status))
            )
        if min_pulse is not None:
            filters.append(
                models.FieldCondition(key="pulse_context", range=models.Range(gte=min_pulse))
            )

        results = self.client.search(
            collection_name="aetheris_thoughts",
            query_vector=query_vector,
            limit=limit,
            query_filter=models.Filter(must=filters) if filters else None,
            with_payload=True,
        )
        return [StoredThought(**hit.payload) for hit in results]

    @retry(exceptions=(Exception,), max_attempts=3, base_delay=1, backoff="linear")
    def get_pending_thoughts(self, limit: int = 10) -> List[StoredThought]:
        """Get thoughts with status 'pending'"""
        if not self.client or not self._initialized:
            return []

        results, _ = self.client.scroll(
            collection_name="aetheris_thoughts",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="status", match=models.MatchValue(value="pending")
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
        )
        return [StoredThought(**r.payload) for r in results]

    @retry(exceptions=(Exception,), max_attempts=3, base_delay=1, backoff="linear")
    def get_pending_tasks(self, limit: int = 10) -> List[StoredTask]:
        """Get tasks with status 'pending'"""
        if not self.client or not self._initialized:
            return []

        try:
            results, _ = self.client.scroll(
                collection_name="aetheris_tasks",
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="status", match=models.MatchValue(value="pending")
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
            )
            return [StoredTask(**r.payload) for r in results]
        except Exception as e:
            logging.error(f"[Hippocampus] Erreur get_pending_tasks: {e}")
            return []

    def is_available(self) -> bool:
        """Check if Qdrant is connected"""
        return self._initialized and self.client is not None

    def index_tool(self, tool_data: Dict):
        """Indexe un outil MCP ou natif dans la collection 'synaptic_tools'."""
        if not self.client or not self._initialized:
            return False

        try:
            text = f"{tool_data.get('name', '')}: {tool_data.get('description', '')}"
            vector = self._get_embedding(text)

            self.client.upsert(
                collection_name="synaptic_tools",
                points=[models.PointStruct(id=str(uuid.uuid4()), vector=vector, payload=tool_data)],
            )
            logging.debug(f"[Hippocampus] Outil indexé: {tool_data.get('name')}")
            return True
        except Exception as e:
            logging.error(f"[Hippocampus] Erreur index_tool: {e}")
            return False

    def search_tools(self, query: str, limit: int = 5) -> List[Dict]:
        """Recherche les outils les plus pertinents pour une tâche donnée."""
        if not self.client or not self._initialized:
            return []

        try:
            query_vector = self._get_embedding(query)
            results = self.client.search(
                collection_name="synaptic_tools",
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
            return [hit.payload for hit in results]
        except Exception as e:
            logging.error(f"[Hippocampus] Erreur search_tools: {e}")
            return []

    def _get_embedding(self, text: str) -> List[float]:
        """Génère un embedding pour le texte (384 dimensions)"""
        try:
            model = self._get_embedding_model()
            if model:
                return model.encode(text).tolist()
        except Exception:
            pass
        return [0.0] * 384


_hippocampus = None


def get_hippocampus() -> Hippocampus:
    global _hippocampus
    if _hippocampus is None:
        _hippocampus = Hippocampus()
    return _hippocampus
