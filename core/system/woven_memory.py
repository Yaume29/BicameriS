"""
Woven Memory - Advanced Memory System
====================================
Advanced memory system with neural mesh, temporal decay, and contextual recall.

This module provides:
- Neural embedding-based search (similarity)
- Concept extraction and linking
- Temporal memory with decay
- Hemisphere-aware context retrieval

Philosophy: "Memory is woven into the fabric of experience"
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("[WovenMemory] numpy not available - using fallback keyword matching")

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    logging.warning("[WovenMemory] Qdrant not available - using local fallback")

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
WOVEN_DIR = BASE_DIR / "storage" / "woven_memory"


@dataclass
class Synapse:
    """A piece of woven memory (like a chunk in RAG systems)"""
    id: str
    content: str
    project_id: str
    source: str
    category: str
    timestamp: str
    embedding_hash: str = ""
    importance: float = 0.5
    access_count: int = 0
    last_accessed: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class Concept:
    """A concept extracted from content (like entities in knowledge graphs)"""
    id: str
    name: str
    aliases: List[str]
    project_id: str
    synapses_count: int = 0
    created_at: str = ""
    last_mentioned: str = ""


@dataclass  
class Link:
    """A link between concepts (like relationships in knowledge graphs)"""
    source_concept: str
    target_concept: str
    relationship: str
    strength: float = 0.5
    project_id: str = ""
    created_at: str = ""


class WovenMemory:
    """
    Advanced memory system with neural mesh architecture.
    
    Features:
    - Synapse-based storage (similar to chunks)
    - Concept extraction (similar to entities)
    - Neural links (similar to knowledge graph)
    - Temporal decay (recent memories are stronger)
    - Hemisphere-aware retrieval
    
    This is a complete rewrite inspired by modern RAG systems
    but with original architecture.
    """
    
    def __init__(
        self,
        qdrant_url: str = "http://localhost:6333",
        collection_name: str = "woven_synapses",
        enable_vector: bool = True,
        enable_concepts: bool = True,
        enable_temporal: bool = True,
        decay_rate: float = 0.95,
        vector_size: int = 384
    ):
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.enable_vector = enable_vector and QDRANT_AVAILABLE
        self.enable_concepts = enable_concepts
        self.enable_temporal = enable_temporal
        self.decay_rate = decay_rate
        self.vector_size = vector_size
        
        WOVEN_DIR.mkdir(parents=True, exist_ok=True)
        
        # Local storage files
        self.synapses_file = WOVEN_DIR / "synapses.json"
        self.concepts_file = WOVEN_DIR / "concepts.json"
        self.links_file = WOVEN_DIR / "links.json"
        self.config_file = WOVEN_DIR / "config.json"
        
        # In-memory caches
        self.synapses: Dict[str, Synapse] = {}
        self.concepts: Dict[str, Concept] = {}
        self.links: List[Link] = []
        
        # State
        self.enabled = False  # Disabled by default like original RAG
        self._qdrant_client = None
        
        # Load existing data
        self._load_data()
        
        # Initialize vector store if enabled
        if self.enable_vector:
            self._init_vector_store()
        
        logging.info(f"[WovenMemory] Initialized - vector:{self.enable_vector}, concepts:{self.enable_concepts}, temporal:{self.enable_temporal}")
    
    def _load_data(self):
        """Load data from disk"""
        # Load synapses
        if self.synapses_file.exists():
            try:
                with open(self.synapses_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.synapses = {k: Synapse(**v) for k, v in data.get("synapses", {}).items()}
            except Exception as e:
                logging.warning(f"[WovenMemory] Load synapses error: {e}")
        
        # Load concepts
        if self.concepts_file.exists():
            try:
                with open(self.concepts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.concepts = {k: Concept(**v) for k, v in data.get("concepts", {}).items()}
            except Exception as e:
                logging.warning(f"[WovenMemory] Load concepts error: {e}")
        
        # Load links
        if self.links_file.exists():
            try:
                with open(self.links_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.links = [Link(**l) for l in data.get("links", [])]
            except Exception as e:
                logging.warning(f"[WovenMemory] Load links error: {e}")
        
        logging.info(f"[WovenMemory] Loaded {len(self.synapses)} synapses, {len(self.concepts)} concepts, {len(self.links)} links")
    
    def _save_data(self):
        """Save data to disk"""
        # Save synapses
        with open(self.synapses_file, "w", encoding="utf-8") as f:
            json.dump({"synapses": {k: asdict(v) for k, v in self.synapses.items()}}, f, indent=2, ensure_ascii=False)
        
        # Save concepts
        with open(self.concepts_file, "w", encoding="utf-8") as f:
            json.dump({"concepts": {k: asdict(v) for k, v in self.concepts.items()}}, f, indent=2, ensure_ascii=False)
        
        # Save links
        with open(self.links_file, "w", encoding="utf-8") as f:
            json.dump({"links": [asdict(l) for l in self.links]}, f, indent=2, ensure_ascii=False)
    
    def _init_vector_store(self):
        """Initialize Qdrant vector store"""
        if not QDRANT_AVAILABLE:
            return
        
        try:
            self._qdrant_client = QdrantClient(url=self.qdrant_url)
            
            # Create collection if not exists
            collections = self._qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.collection_name not in collection_names:
                self._qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logging.info(f"[WovenMemory] Created Qdrant collection: {self.collection_name}")
            else:
                logging.info(f"[WovenMemory] Using existing Qdrant collection: {self.collection_name}")
                
        except Exception as e:
            logging.warning(f"[WovenMemory] Qdrant init error: {e}")
            self.enable_vector = False
            self._qdrant_client = None
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text (stub - requires embedding model)"""
        # This is a stub - in production, use a proper embedding model
        # For now, use a simple hash-based pseudo-embedding
        if not NUMPY_AVAILABLE:
            return None
            
        try:
            # Simple hash-based pseudo-embedding (for fallback)
            hash_val = hashlib.sha256(text.encode()).digest()
            # Convert to float array and normalize
            arr = np.frombuffer(hash_val[:self.vector_size*4], dtype=np.float32)
            if len(arr) < self.vector_size:
                arr = np.pad(arr, (0, self.vector_size - len(arr)))
            # Normalize
            arr = arr / (np.linalg.norm(arr) + 1e-10)
            return arr.tolist()
        except Exception as e:
            logging.warning(f"[WovenMemory] Embedding error: {e}")
            return None
    
    def _extract_concepts(self, content: str) -> Set[str]:
        """Extract concepts from content using simple NLP"""
        # Simple extraction - look for capitalized words and key terms
        words = content.split()
        concepts = set()
        
        # Look for capitalized phrases (potential proper nouns)
        current = ""
        for word in words:
            if word[0].isupper() if word else False:
                current += " " + word
                if len(current) > 3:
                    concepts.add(current.strip())
            else:
                if current:
                    concepts.add(current.strip())
                    current = ""
        
        # Add key programming terms
        key_terms = {"function", "class", "method", "api", "database", "model", "data", "system", "config"}
        for term in key_terms:
            if term.lower() in content.lower():
                concepts.add(term)
        
        return concepts
    
    def _calculate_temporal_weight(self, synapse: Synapse) -> float:
        """Calculate temporal weight with decay"""
        if not self.enable_temporal:
            return synapse.importance
        
        try:
            created = datetime.fromisoformat(synapse.timestamp)
            hours_old = (datetime.now() - created).total_seconds() / 3600
            
            # Exponential decay
            weight = synapse.importance * (self.decay_rate ** (hours_old / 24))
            return max(weight, 0.1)  # Minimum weight
        except:
            return synapse.importance
    
    # ========== PUBLIC API (Backward Compatible with RAGIndexer) ==========
    
    def enable(self):
        """Enable the woven memory system"""
        self.enabled = True
        logging.info("[WovenMemory] ENABLED - Woven Memory mode activated")
    
    def disable(self):
        """Disable the woven memory system"""
        self.enabled = False
        logging.info("[WovenMemory] DISABLED - Emergence mode restored")
    
    def is_enabled(self) -> bool:
        """Check if woven memory is enabled"""
        return self.enabled
    
    def weave(
        self,
        content: str,
        project_id: str = "default",
        source: str = "custom",
        category: str = "general",
        importance: float = 0.5,
        metadata: Dict = None
    ) -> Synapse:
        """
        Weave content into memory (like RAG indexing)
        """
        # Generate ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        synapse_id = f"syn_{content_hash}"
        
        # Check for duplicates
        if synapse_id in self.synapses:
            return self.synapses[synapse_id]
        
        # Create synapse
        synapse = Synapse(
            id=synapse_id,
            content=content,
            project_id=project_id,
            source=source,
            category=category,
            timestamp=datetime.now().isoformat(),
            embedding_hash=content_hash,
            importance=importance,
            metadata=metadata or {}
        )
        
        self.synapses[synapse_id] = synapse
        
        # Extract and store concepts
        if self.enable_concepts:
            concepts = self._extract_concepts(content)
            for concept_name in concepts:
                self._add_concept(concept_name, project_id)
        
        # Store in vector database if enabled
        if self.enable_vector and self._qdrant_client:
            embedding = self._generate_embedding(content)
            if embedding:
                point = PointStruct(
                    id=synapse_id,
                    vector=embedding,
                    payload={
                        "content": content[:1000],  # Truncate for storage
                        "source": source,
                        "category": category,
                        "project_id": project_id
                    }
                )
                try:
                    self._qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=[point]
                    )
                except Exception as e:
                    logging.warning(f"[WovenMemory] Vector upsert error: {e}")
        
        # Save to disk
        self._save_data()
        
        logging.info(f"[WovenMemory] Woven: {synapse_id} ({len(content)} chars)")
        return synapse
    
    def _add_concept(self, name: str, project_id: str):
        """Add or update a concept"""
        concept_id = f"concept_{name.lower().replace(' ', '_')}"
        
        if concept_id in self.concepts:
            self.concepts[concept_id].synapses_count += 1
            self.concepts[concept_id].last_mentioned = datetime.now().isoformat()
        else:
            self.concepts[concept_id] = Concept(
                id=concept_id,
                name=name,
                aliases=[],
                project_id=project_id,
                synapses_count=1,
                created_at=datetime.now().isoformat(),
                last_mentioned=datetime.now().isoformat()
            )
    
    def recall(
        self,
        query: str,
        project_id: str = None,
        hemisphere: str = "both",
        limit: int = 5
    ) -> List[Synapse]:
        """
        Recall memories similar to query (like RAG search)
        
        Args:
            query: Search query
            project_id: Filter by project
            hemisphere: 'left' (factual), 'right' (creative), 'both'
            limit: Max results
        """
        if not self.enabled:
            return []
        
        results = []
        
        # Vector search if available
        if self.enable_vector and self._qdrant_client:
            try:
                embedding = self._generate_embedding(query)
                if embedding:
                    search_results = self._qdrant_client.search(
                        collection_name=self.collection_name,
                        query_vector=embedding,
                        limit=limit * 2
                    )
                    
                    for r in search_results:
                        payload = r.payload
                        synapse_id = r.id
                        
                        if synapse_id in self.synapses:
                            synapse = self.synapses[synapse_id]
                            
                            # Filter by project
                            if project_id and synapse.project_id != project_id:
                                continue
                            
                            # Apply temporal weight
                            weight = self._calculate_temporal_weight(synapse)
                            synapse.access_count += 1
                            synapse.last_accessed = datetime.now().isoformat()
                            
                            results.append((weight * (1 - r.score), synapse))
            except Exception as e:
                logging.warning(f"[WovenMemory] Vector search error: {e}")
        
        # Fallback: keyword matching
        if not results:
            query_words = set(query.lower().split())
            
            for synapse in self.synapses.values():
                # Filter by project
                if project_id and synapse.project_id != project_id:
                    continue
                
                # Keyword matching
                content_words = set(synapse.content.lower().split())
                common = query_words & content_words
                
                if common:
                    weight = len(common) / max(len(query_words), 1)
                    # Apply temporal weight
                    temporal_weight = self._calculate_temporal_weight(synapse)
                    results.append((temporal_weight * weight, synapse))
        
        # Sort by weight and return
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Hemisphere adjustment
        if hemisphere == "left":
            # Prefer factual categories
            results = [(w, s) for w, s in results if s.category in ["api", "syntax", "pattern"]]
        elif hemisphere == "right":
            # Prefer creative categories
            results = [(w, s) for w, s in results if s.category in ["idea", "concept", "example"]]
        
        return [s for _, s in results[:limit]]
    
    def search(self, query: str, limit: int = 3, source: str = None) -> List[Synapse]:
        """Search memories (backward compatible with RAGIndexer)"""
        if not self.enabled:
            return []
        
        results = self.recall(query, limit=limit)
        
        if source:
            results = [s for s in results if s.source == source]
        
        return results
    
    def get_context(self, query: str, max_chars: int = 500) -> str:
        """
        Get context string for query (backward compatible with RAGIndexer)
        """
        if not self.enabled:
            return ""
        
        synapses = self.recall(query, limit=3)
        
        if not synapses:
            return ""
        
        context_parts = ["[WOVEN MEMORY]"]
        
        total_chars = 0
        for synapse in synapses:
            excerpt = synapse.content[:200]
            
            if total_chars + len(excerpt) > max_chars:
                break
            
            context_parts.append(f"- [{synapse.source}] {excerpt}...")
            total_chars += len(excerpt)
        
        return "\n".join(context_parts)
    
    def clear(self):
        """Clear all memory"""
        self.synapses.clear()
        self.concepts.clear()
        self.links.clear()
        
        # Clear vector store
        if self.enable_vector and self._qdrant_client:
            try:
                self._qdrant_client.delete(collection_name=self.collection_name, delete_all=True)
            except:
                pass
        
        self._save_data()
        logging.info("[WovenMemory] All memory cleared")
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "enabled": self.enabled,
            "synapses_count": len(self.synapses),
            "concepts_count": len(self.concepts),
            "links_count": len(self.links),
            "vector_enabled": self.enable_vector,
            "qdrant_connected": self._qdrant_client is not None,
            "temporal_enabled": self.enable_temporal
        }


# Global instance
_woven_memory = None


def get_woven_memory() -> WovenMemory:
    """Get global WovenMemory instance"""
    global _woven_memory
    if _woven_memory is None:
        _woven_memory = WovenMemory()
    return _woven_memory


# Backward compatibility alias
class RAGIndexer(WovenMemory):
    """Backward compatibility wrapper"""
    
    def __init__(self):
        super().__init__()
        logging.info("[RAGIndexer] Wrapping WovenMemory for backward compatibility")
    
    def index_document(self, content: str, source: str = "custom", category: str = "general", metadata: Dict = None) -> Synapse:
        """Legacy method - use weave() instead"""
        return self.weave(content, source=source, category=category, metadata=metadata)


def get_rag_indexer() -> WovenMemory:
    """Get RAG indexer (backward compatible)"""
    return get_woven_memory()
