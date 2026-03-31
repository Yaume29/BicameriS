"""
RAG Indexer - Optional Knowledge Retrieval
==========================================
Module RAG optionnel pour le module unifié.

IMPORTANT: Ce module est maintenant un wrapper autour de WovenMemory.
Le nouveau système offre:
- Recherche vectorielle (si Qdrant disponible)
- Extraction de concepts
- Liens sémantiques
- Décay temporel (souvenirs récents plus forts)

Philosophie: "La mémoire est tissée dans le tissu de l'expérience"

Ce module reste compatible avec l'ancien système pour ne pas briser le code existant.
"""

import logging

# Import from WovenMemory for backward compatibility
try:
    from core.system.woven_memory import WovenMemory, get_woven_memory, Synapse
    
    # Keep RAGDocument as alias for Synapse for backward compatibility
    class RAGDocument:
        """Backward compatibility alias"""
        def __init__(self, id="", content="", source="", category="", timestamp="", embedding_hash="", metadata=None):
            self.id = id
            self.content = content
            self.source = source
            self.category = category
            self.timestamp = timestamp
            self.embedding_hash = embedding_hash
            self.metadata = metadata or {}
        
        @staticmethod
        def from_synapse(synapse: Synapse):
            doc = RAGDocument()
            doc.id = synapse.id
            doc.content = synapse.content
            doc.source = synapse.source
            doc.category = synapse.category
            doc.timestamp = synapse.timestamp
            doc.embedding_hash = synapse.embedding_hash
            doc.metadata = synapse.metadata
            return doc
    
    class RAGIndexer(WovenMemory):
        """
        Backward compatibility wrapper around WovenMemory.
        All new code should use WovenMemory directly.
        """
        
        def __init__(self):
            super().__init__()
            logging.info("[RAGIndexer] Now using WovenMemory backend")
        
        def index_document(self, content: str, source: str = "custom", category: str = "general", metadata: dict = None):
            """Legacy method - uses weave() internally"""
            return self.weave(content, source=source, category=category, metadata=metadata)
        
        def search(self, query: str, limit: int = 3, source: str = None):
            """Search memories"""
            results = self.recall(query, limit=limit)
            if source:
                results = [s for s in results if s.source == source]
            # Convert to legacy format
            return [RAGDocument.from_synapse(s) for s in results]
        
        def get_context(self, query: str, max_chars: int = 500) -> str:
            """Get context string"""
            if not self.enabled:
                return ""
            
            synapses = self.recall(query, limit=3)
            
            if not synapses:
                return ""
            
            context_parts = ["[RAG - Documentation]"]
            
            total_chars = 0
            for synapse in synapses:
                excerpt = synapse.content[:200]
                
                if total_chars + len(excerpt) > max_chars:
                    break
                
                context_parts.append(f"- [{synapse.source}] {excerpt}...")
                total_chars += len(excerpt)
            
            return "\n".join(context_parts)
    
    def get_rag_indexer() -> WovenMemory:
        """Get RAG indexer instance"""
        return get_woven_memory()

except ImportError as e:
    logging.error(f"[RAGIndexer] Failed to import WovenMemory: {e}")
    
    # Fallback to old implementation
    import json
    import hashlib
    from pathlib import Path
    from typing import Dict, List
    from dataclasses import dataclass, asdict
    from datetime import datetime

    BASE_DIR = Path(__file__).parent.parent.parent.absolute()
    RAG_DIR = BASE_DIR / "storage" / "rag"

    @dataclass
    class RAGDocument:
        id: str
        content: str
        source: str
        category: str
        timestamp: str
        embedding_hash: str = ""
        metadata: Dict = None

    class RAGIndexer:
        def __init__(self):
            self.storage_file = RAG_DIR / "rag_index.json"
            RAG_DIR.mkdir(parents=True, exist_ok=True)
            self.documents: List[RAGDocument] = []
            self.enabled = False
            self._load_index()
            logging.info("[RAGIndexer] Fallback mode - basic keyword search")
        
        def _load_index(self):
            if self.storage_file.exists():
                try:
                    with open(self.storage_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.documents = [RAGDocument(**doc) for doc in data.get("documents", [])]
                except:
                    self.documents = []
        
        def enable(self):
            self.enabled = True
        
        def disable(self):
            self.enabled = False
        
        def is_enabled(self) -> bool:
            return self.enabled
        
        def index_document(self, content: str, source: str = "custom", category: str = "general", metadata: Dict = None):
            content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
            doc_id = f"rag_{content_hash}"
            for doc in self.documents:
                if doc.id == doc_id:
                    return doc
            doc = RAGDocument(
                id=doc_id, content=content, source=source, category=category,
                timestamp=datetime.now().isoformat(), embedding_hash=content_hash, metadata=metadata or {}
            )
            self.documents.append(doc)
            return doc
        
        def search(self, query: str, limit: int = 3, source: str = None):
            if not self.enabled:
                return []
            query_words = set(query.lower().split())
            scored = []
            for doc in self.documents:
                if source and doc.source != source:
                    continue
                common = query_words & set(doc.content.lower().split())
                if common:
                    scored.append((len(common) / max(len(query_words), 1), doc))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [doc for _, doc in scored[:limit]]
        
        def get_context(self, query: str, max_chars: int = 500) -> str:
            if not self.enabled:
                return ""
            docs = self.search(query, limit=2)
            if not docs:
                return ""
            parts = ["[RAG - Documentation]"]
            total = 0
            for doc in docs:
                excerpt = doc.content[:200]
                if total + len(excerpt) > max_chars:
                    break
                parts.append(f"- [{doc.source}] {excerpt}...")
                total += len(excerpt)
            return "\n".join(parts)
        
        def clear(self):
            self.documents = []
    
    _rag_indexer = None
    
    def get_rag_indexer() -> RAGIndexer:
        global _rag_indexer
        if _rag_indexer is None:
            _rag_indexer = RAGIndexer()
        return _rag_indexer
