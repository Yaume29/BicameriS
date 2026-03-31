"""
Knowledge Base Module
=====================
Vector-based knowledge storage for model growth.
Helps small models become smarter by storing and retrieving relevant knowledge.
"""

import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
KNOWLEDGE_DIR = BASE_DIR / "storage" / "knowledge"


@dataclass
class KnowledgeEntry:
    """A single knowledge entry"""
    id: str
    content: str
    category: str  # fact, pattern, correction, insight, technique
    source: str  # chat, thought, inception, manual
    timestamp: str
    importance: float = 0.5  # 0-1
    usage_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeBase:
    """
    Vector-based knowledge storage for model growth.
    Stores patterns, facts, corrections, and insights that help models improve.
    """
    
    def __init__(self):
        self.storage_file = KNOWLEDGE_DIR / "knowledge_base.json"
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        
        self.entries: List[KnowledgeEntry] = []
        self.load()
        
        # Category weights for retrieval
        self.category_weights = {
            "correction": 1.5,  # Corrections are important
            "insight": 1.3,     # Insights are valuable
            "pattern": 1.2,     # Patterns are useful
            "fact": 1.0,        # Facts are neutral
            "technique": 1.1,   # Techniques are helpful
        }
        
        logging.info(f"[KnowledgeBase] Initialized with {len(self.entries)} entries")
    
    def load(self):
        """Load knowledge from file"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entries = [KnowledgeEntry(**e) for e in data.get("entries", [])]
            except Exception as e:
                logging.error(f"[KnowledgeBase] Load error: {e}")
                self.entries = []
    
    def save(self):
        """Save knowledge to file"""
        try:
            data = {
                "version": "1.0",
                "updated": datetime.now().isoformat(),
                "count": len(self.entries),
                "entries": [asdict(e) for e in self.entries]
            }
            
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"[KnowledgeBase] Save error: {e}")
    
    def add_entry(
        self,
        content: str,
        category: str = "fact",
        source: str = "manual",
        importance: float = 0.5,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> KnowledgeEntry:
        """Add a new knowledge entry"""
        
        # Generate ID from content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()[:12]
        entry_id = f"kb_{content_hash}"
        
        # Check for duplicates
        for existing in self.entries:
            if existing.id == entry_id:
                existing.usage_count += 1
                existing.importance = min(1.0, existing.importance + 0.1)
                self.save()
                return existing
        
        # Create new entry
        entry = KnowledgeEntry(
            id=entry_id,
            content=content,
            category=category,
            source=source,
            timestamp=datetime.now().isoformat(),
            importance=importance,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.entries.append(entry)
        self.save()
        
        logging.info(f"[KnowledgeBase] Added entry: {entry_id}")
        return entry
    
    def search(self, query: str, limit: int = 5, category: str = None) -> List[KnowledgeEntry]:
        """
        Search for relevant knowledge entries.
        Uses simple keyword matching with category weighting.
        """
        query_words = set(query.lower().split())
        
        scored_entries = []
        
        for entry in self.entries:
            if category and entry.category != category:
                continue
            
            # Calculate relevance score
            entry_words = set(entry.content.lower().split())
            common_words = query_words & entry_words
            
            if not common_words:
                continue
            
            # Score based on word overlap, importance, and category
            word_score = len(common_words) / max(len(query_words), 1)
            category_weight = self.category_weights.get(entry.category, 1.0)
            
            total_score = word_score * entry.importance * category_weight
            
            scored_entries.append((total_score, entry))
        
        # Sort by score and return top results
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        
        results = [entry for _, entry in scored_entries[:limit]]
        
        # Update usage counts
        for entry in results:
            entry.usage_count += 1
        
        if results:
            self.save()
        
        return results
    
    def get_context_for_query(self, query: str, max_tokens: int = 500) -> str:
        """
        Get relevant knowledge context for a query.
        Returns formatted string ready for injection into prompts.
        """
        entries = self.search(query, limit=3)
        
        if not entries:
            return ""
        
        context_parts = ["[KNOWLEDGE BASE - Pertinent]"]
        
        total_chars = 0
        for entry in entries:
            entry_text = f"- [{entry.category.upper()}] {entry.content[:200]}"
            
            if total_chars + len(entry_text) > max_tokens * 4:  # ~4 chars per token
                break
            
            context_parts.append(entry_text)
            total_chars += len(entry_text)
        
        return "\n".join(context_parts)
    
    def learn_from_correction(self, original: str, corrected: str, explanation: str = ""):
        """Learn from a correction"""
        content = f"Correction: {original[:100]} → {corrected[:100]}"
        if explanation:
            content += f" | Raison: {explanation[:100]}"
        
        self.add_entry(
            content=content,
            category="correction",
            source="correction",
            importance=0.8,
            tags=["correction", "apprentissage"]
        )
    
    def learn_from_insight(self, insight: str, context: str = ""):
        """Store an insight"""
        content = insight
        if context:
            content = f"{insight} | Contexte: {context[:100]}"
        
        self.add_entry(
            content=content,
            category="insight",
            source="thought",
            importance=0.7,
            tags=["insight", "réflexion"]
        )
    
    def learn_pattern(self, pattern: str, examples: List[str] = None):
        """Store a pattern"""
        content = pattern
        if examples:
            content += f" | Exemples: {', '.join(examples[:3])}"
        
        self.add_entry(
            content=content,
            category="pattern",
            source="analysis",
            importance=0.6,
            tags=["pattern", "structure"]
        )
    
    def learn_technique(self, technique: str, domain: str = ""):
        """Store a technique"""
        content = technique
        if domain:
            content = f"[{domain}] {technique}"
        
        self.add_entry(
            content=content,
            category="technique",
            source="experience",
            importance=0.7,
            tags=["technique", domain.lower() if domain else "general"]
        )
    
    def export_knowledge(self, format: str = "json") -> str:
        """Export knowledge base"""
        if format == "json":
            return json.dumps({
                "version": "1.0",
                "exported": datetime.now().isoformat(),
                "count": len(self.entries),
                "entries": [asdict(e) for e in self.entries]
            }, indent=2, ensure_ascii=False)
        
        elif format == "markdown":
            lines = ["# Base de Connaissances BicameriS", ""]
            lines.append(f"Exporté le: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            lines.append(f"Nombre d'entrées: {len(self.entries)}")
            lines.append("")
            
            # Group by category
            by_category = {}
            for entry in self.entries:
                cat = entry.category
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(entry)
            
            for category, entries in by_category.items():
                lines.append(f"## {category.upper()}")
                lines.append("")
                
                for entry in sorted(entries, key=lambda e: e.importance, reverse=True):
                    lines.append(f"- **[{entry.importance:.1f}]** {entry.content}")
                    if entry.tags:
                        lines.append(f"  Tags: {', '.join(entry.tags)}")
                    lines.append("")
            
            return "\n".join(lines)
        
        return ""
    
    def import_knowledge(self, data: str, format: str = "json"):
        """Import knowledge from external source"""
        if format == "json":
            try:
                import_data = json.loads(data)
                entries_data = import_data.get("entries", [])
                
                imported = 0
                for entry_data in entries_data:
                    # Check if already exists
                    entry_id = entry_data.get("id")
                    if any(e.id == entry_id for e in self.entries):
                        continue
                    
                    entry = KnowledgeEntry(**entry_data)
                    self.entries.append(entry)
                    imported += 1
                
                self.save()
                logging.info(f"[KnowledgeBase] Imported {imported} entries")
                return imported
                
            except Exception as e:
                logging.error(f"[KnowledgeBase] Import error: {e}")
                return 0
        
        return 0
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics"""
        by_category = {}
        by_source = {}
        
        for entry in self.entries:
            cat = entry.category
            src = entry.source
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_source[src] = by_source.get(src, 0) + 1
        
        total_usage = sum(e.usage_count for e in self.entries)
        avg_importance = sum(e.importance for e in self.entries) / max(len(self.entries), 1)
        
        return {
            "total_entries": len(self.entries),
            "by_category": by_category,
            "by_source": by_source,
            "total_usage": total_usage,
            "avg_importance": round(avg_importance, 2),
            "storage_file": str(self.storage_file)
        }
    
    def cleanup(self, min_importance: float = 0.1, max_age_days: int = 90):
        """Clean up old or low-importance entries"""
        cutoff = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        
        before_count = len(self.entries)
        
        self.entries = [
            e for e in self.entries
            if e.importance >= min_importance or 
            datetime.fromisoformat(e.timestamp).timestamp() > cutoff
        ]
        
        removed = before_count - len(self.entries)
        
        if removed > 0:
            self.save()
            logging.info(f"[KnowledgeBase] Cleaned up {removed} entries")
        
        return removed


# Global instance
_knowledge_base = None


def get_knowledge_base() -> KnowledgeBase:
    """Get global knowledge base instance"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
