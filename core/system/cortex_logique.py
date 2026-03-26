"""
BICAMERIS - Cortex Logique (Graph Database)
=========================================
Epistemological graph using Kùzu for logical reasoning.
Complements Qdrant (intuition) with causal relationships.
"""

import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

try:
    import kuzu

    KUZU_AVAILABLE = True
except ImportError:
    kuzu = None
    KUZU_AVAILABLE = False


class CortexLogique:
    """
    Graph-based logical memory for causal reasoning.
    Extracts triplets (Subject -> Predicate -> Object) from thoughts.
    """

    def __init__(self, db_path: str = None):
        BASE_DIR = Path(__file__).parent.parent.parent.absolute()
        if db_path is None:
            db_path = BASE_DIR / "storage" / "graph" / "kuzu_db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = None
        self.conn = None
        self._initialized = False
        self._db_lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Initialize Kùzu database and schema"""
        if not KUZU_AVAILABLE:
            logger.warning("[CortexLogique] Kùzu non installé - mode dégradé")
            return

        try:
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)
            self._create_schema()
            self._initialized = True
            logger.info(f"[CortexLogique] ✅ Connecté à Kùzu: {self.db_path}")
        except Exception as e:
            logger.error(f"[CortexLogique] ❌ Échec init: {e}")
            self.db = None

    def _create_schema(self):
        """Create the ontological schema"""
        try:
            with self._db_lock:
                self.conn.execute("CREATE NODE TABLE Concept (name STRING, PRIMARY KEY(name))")
                self.conn.execute(
                    "CREATE REL TABLE RelatesTo (FROM Concept TO Concept, relation STRING, confidence DOUBLE)"
                )
                self.conn.execute(
                    "CREATE REL TABLE Contradicts (FROM Concept TO Concept, evidence STRING)"
                )
            logger.info("[CortexLogique] ✅ Schéma créé")
        except Exception as e:
            logger.debug(f"[CortexLogique] Schéma peut-être déjà existant: {e}")

    def injecter_triplet(self, sujet: str, predicat: str, objet: str, confidence: float = 1.0):
        """Inject a knowledge triplet (called by left hemisphere after analysis)"""
        if not self._initialized:
            return

        try:
            query = """
            MERGE (s:Concept {name: $sujet})
            MERGE (o:Concept {name: $objet})
            MERGE (s)-[r:RelatesTo {relation: $predicat}]->(o)
            SET r.confidence = $confidence
            """
            with self._db_lock:
                self.conn.execute(
                    query,
                    parameters={
                        "sujet": sujet,
                        "objet": objet,
                        "predicat": predicat,
                        "confidence": confidence,
                    },
                )
        except Exception as e:
            logger.warning(f"[CortexLogique] Erreur triplet: {e}")

    def auditer_logique(self, concept: str) -> List[Dict]:
        """Query graph to audit logical relationships (left hemisphere)"""
        if not self._initialized:
            return []

        try:
            query = """
            MATCH (c:Concept {name: $concept})-[r:RelatesTo]->(other)
            RETURN r.relation, other.name, r.confidence
            """
            with self._db_lock:
                result = self.conn.execute(query, parameters={"concept": concept})
            return result.get_as_df().to_dict("records")
        except Exception as e:
            logger.warning(f"[CortexLogique] Erreur audit: {e}")
            return []

    def trouver_contradictions(self, concept: str) -> List[Dict]:
        """Find contradictory concepts"""
        if not self._initialized:
            return []

        try:
            query = """
            MATCH (c:Concept {name: $concept})-[r:Contradicts]->(other)
            RETURN other.name, r.evidence
            """
            with self._db_lock:
                result = self.conn.execute(query, parameters={"concept": concept})
            return result.get_as_df().to_dict("records")
        except Exception as e:
            return []

    def ajouter_contradiction(self, concept_a: str, concept_b: str, evidence: str):
        """Add a contradiction between two concepts"""
        if not self._initialized:
            return

        try:
            query = """
            MERGE (a:Concept {name: $concept_a})
            MERGE (b:Concept {name: $concept_b})
            MERGE (a)-[r:Contradicts {evidence: $evidence}]->(b)
            """
            with self._db_lock:
                self.conn.execute(
                    query,
                    parameters={
                        "concept_a": concept_a,
                        "concept_b": concept_b,
                        "evidence": evidence,
                    },
                )
        except Exception as e:
            logger.warning(f"[CortexLogique] Erreur contradiction: {e}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()

    def is_available(self) -> bool:
        """Check if graph DB is connected"""
        return self._initialized and self.conn is not None


_cortex_logique = None


def get_cortex_logique() -> CortexLogique:
    global _cortex_logique
    if _cortex_logique is None:
        _cortex_logique = CortexLogique()
    return _cortex_logique
