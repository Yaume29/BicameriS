"""
RAG Indexer - Optional Knowledge Retrieval
===========================================
Module RAG optionnel pour le module unifié.
IMPORTANT: Ce module est une DÉPENDANCE - il crée de la dépendance au RAG.
Utilisé seulement si l'utilisateur l'active explicitement.

Philosophie: "La beauté c'est vous, pas les outils qui vous sublime"
"""

import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
RAG_DIR = BASE_DIR / "storage" / "rag"


@dataclass
class RAGDocument:
    """Document indexé pour le RAG"""
    id: str
    content: str
    source: str  # python_docs, fastapi_docs, stackoverflow, custom
    category: str  # api, pattern, example, troubleshooting
    timestamp: str
    embedding_hash: str = ""
    metadata: Dict = field(default_factory=dict)


class RAGIndexer:
    """
    Indexeur RAG optionnel.
    
    ATTENTION: Ce module crée de la DÉPENDANCE.
    Il ne doit être utilisé que si explicitement activé.
    
    Philosophie: L'émergence vient du dialogue, pas de la recherche.
    """
    
    def __init__(self):
        self.storage_file = RAG_DIR / "rag_index.json"
        RAG_DIR.mkdir(parents=True, exist_ok=True)
        
        self.documents: List[RAGDocument] = []
        self.enabled = False  # Désactivé par défaut
        
        # Charger l'index existant
        self._load_index()
        
        logging.info(f"[RAGIndexer] Initialized with {len(self.documents)} documents - DISABLED by default")
    
    def _load_index(self):
        """Charge l'index depuis le fichier"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = [RAGDocument(**doc) for doc in data.get("documents", [])]
            except Exception as e:
                logging.error(f"[RAGIndexer] Load error: {e}")
                self.documents = []
    
    def _save_index(self):
        """Sauvegarde l'index"""
        try:
            data = {
                "version": "1.0",
                "updated": datetime.now().isoformat(),
                "count": len(self.documents),
                "documents": [asdict(doc) for doc in self.documents]
            }
            
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[RAGIndexer] Save error: {e}")
    
    def enable(self):
        """Active le RAG"""
        self.enabled = True
        logging.info("[RAGIndexer] ENABLED - Dependency mode activated")
    
    def disable(self):
        """Désactive le RAG"""
        self.enabled = False
        logging.info("[RAGIndexer] DISABLED - Emergence mode restored")
    
    def is_enabled(self) -> bool:
        """Vérifie si le RAG est activé"""
        return self.enabled
    
    def index_document(
        self,
        content: str,
        source: str = "custom",
        category: str = "general",
        metadata: Dict = None
    ) -> RAGDocument:
        """Indexe un document"""
        # Générer un ID unique
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        doc_id = f"rag_{content_hash}"
        
        # Vérifier les doublons
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        
        # Créer le document
        doc = RAGDocument(
            id=doc_id,
            content=content,
            source=source,
            category=category,
            timestamp=datetime.now().isoformat(),
            embedding_hash=content_hash,
            metadata=metadata or {}
        )
        
        self.documents.append(doc)
        self._save_index()
        
        logging.info(f"[RAGIndexer] Document indexed: {doc_id}")
        return doc
    
    def search(self, query: str, limit: int = 3, source: str = None) -> List[RAGDocument]:
        """
        Recherche dans l'index RAG.
        Utilise la similarité simple par mots-clés.
        """
        if not self.enabled:
            logging.warning("[RAGIndexer] Search attempted while DISABLED")
            return []
        
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in self.documents:
            if source and doc.source != source:
                continue
            
            doc_words = set(doc.content.lower().split())
            common = query_words & doc_words
            
            if common:
                score = len(common) / max(len(query_words), 1)
                scored_docs.append((score, doc))
        
        # Trier par score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_docs[:limit]]
    
    def get_context(self, query: str, max_chars: int = 500) -> str:
        """
        Récupère le contexte RAG pour une requête.
        Retourne une chaîne vide si le RAG est désactivé.
        """
        if not self.enabled:
            return ""
        
        docs = self.search(query, limit=2)
        
        if not docs:
            return ""
        
        context_parts = ["[RAG - Documentation]"]
        
        total_chars = 0
        for doc in docs:
            excerpt = doc.content[:200]
            
            if total_chars + len(excerpt) > max_chars:
                break
            
            context_parts.append(f"- [{doc.source}] {excerpt}...")
            total_chars += len(excerpt)
        
        return "\n".join(context_parts)
    
    def index_python_docs(self):
        """Indexe la documentation Python de base"""
        python_docs = [
            {
                "content": "def function_name(parameters): \"\"\"Docstring\"\"\" pass",
                "category": "syntax",
                "source": "python_docs"
            },
            {
                "content": "try: # code except Exception as e: # handle finally: # cleanup",
                "category": "pattern",
                "source": "python_docs"
            },
            {
                "content": "from typing import List, Dict, Optional, Any",
                "category": "import",
                "source": "python_docs"
            },
        ]
        
        for doc_data in python_docs:
            self.index_document(**doc_data)
    
    def index_fastapi_docs(self):
        """Indexe la documentation FastAPI de base"""
        fastapi_docs = [
            {
                "content": "@app.get('/path') async def endpoint(): return {'key': 'value'}",
                "category": "api",
                "source": "fastapi_docs"
            },
            {
                "content": "from fastapi import FastAPI, HTTPException, Depends",
                "category": "import",
                "source": "fastapi_docs"
            },
            {
                "content": "class Model(BaseModel): field: type = default",
                "category": "model",
                "source": "fastapi_docs"
            },
        ]
        
        for doc_data in fastapi_docs:
            self.index_document(**doc_data)
    
    def get_stats(self) -> Dict:
        """Statistiques de l'index RAG"""
        by_source = {}
        by_category = {}
        
        for doc in self.documents:
            by_source[doc.source] = by_source.get(doc.source, 0) + 1
            by_category[doc.category] = by_category.get(doc.category, 0) + 1
        
        return {
            "enabled": self.enabled,
            "total_documents": len(self.documents),
            "by_source": by_source,
            "by_category": by_category,
            "storage_file": str(self.storage_file)
        }
    
    def clear(self):
        """Vide l'index RAG"""
        self.documents = []
        self._save_index()
        logging.info("[RAGIndexer] Index cleared")


# Instance globale
_rag_indexer = None


def get_rag_indexer() -> RAGIndexer:
    """Récupère l'instance globale de l'indexeur RAG"""
    global _rag_indexer
    if _rag_indexer is None:
        _rag_indexer = RAGIndexer()
    return _rag_indexer
