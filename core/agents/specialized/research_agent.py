"""
Research Agent
==============
Agent de recherche avec sources vérifiées.
Pas d'hallucination - utilise des sources réelles.
"""

import uuid
import asyncio
from typing import Dict, List, Optional

from ..base_agent import BaseAgent, AgentConfig, Task, AgentState
from ...system.config_manager import get_config

logger = logging.getLogger("agents.research")


class ResearchAgent(BaseAgent):
    """
    Agent de recherche - Recherche des informations vérifiées.
    
    Avoid hallucinations en utilisant des sources de données réelles.
    """

    def __init__(self, name: str = "Research Agent", description: str = "", **kwargs):
        super().__init__(
            AgentConfig(
                name=name,
                description=description or "Agent de recherche avec sources vérifiées",
                temperature=0.3,
                max_iterations=5,
                **kwargs
            )
        )
        
        self.sources: List[str] = []
        self.confidence_threshold: float = 0.7
        self.max_sources: int = 5

    def configure_sources(self, sources: List[str]):
        """Configure les sources de données"""
        self.sources = sources[:self.max_sources]
        logger.info(f"[ResearchAgent] Configured sources: {self.sources}")

    async def think(self, task: Task) -> str:
        """
        Planifie la recherche.
        
        1. Décomposer la question en sous-questions
        2. Identifier les sources nécessaires
        3. Créer un plan de recherche
        """
        query = task.description
        
        if not self.llm_client:
            return f"Plan: Rechercher '{query}' dans sources disponibles"
        
        prompt = f"""Décompose cette question de recherche en sous-questions et identifie les sources nécessaires.

Question: {query}

Réponds avec:
1. Liste des sous-questions
2. Sources potentielles (web, fichiers locaux, base de connaissances)
3. Ordre de recherche recommandé"""

        try:
            plan = self.llm_client.think(
                self.config.system_prompt or "You are a research planner.",
                prompt,
                temperature=0.3
            )
            task.metadata["research_plan"] = plan
            return plan
        except Exception as e:
            logger.warning(f"[ResearchAgent] Think error: {e}")
            return f"Plan: Rechercher '{query}'"

    async def execute(self, task: Task, plan: str) -> Dict:
        """
        Exécute la recherche.
        
        1. Rechercher dans chaque source configurée
        2. Évaluer la confiance des résultats
        3. Fusionner les résultats
        """
        query = task.description
        results = []
        sources_used = []

        for source in self.sources:
            if task.metadata.get("_stop"):
                break
                
            try:
                source_result = await self._search_source(source, query)
                if source_result:
                    results.append(source_result)
                    sources_used.append(source)
            except Exception as e:
                logger.warning(f"[ResearchAgent] Source {source} error: {e}")

        if not results:
            return {
                "status": "no_results",
                "query": query,
                "message": "Aucune source n'a retourné de résultats",
                "confidence": 0.0,
                "sources_used": []
            }

        merged = self._merge_results(results)
        confidence = self._calculate_confidence(results)
        
        return {
            "status": "ok",
            "query": query,
            "results": merged,
            "confidence": confidence,
            "confidence_level": "high" if confidence >= 0.7 else "medium" if confidence >= 0.4 else "low",
            "sources_used": sources_used,
            "total_results": len(results)
        }

    async def _search_source(self, source: str, query: str) -> Optional[Dict]:
        """
        Recherche dans une source spécifique.
        
        Implémenter selon le type de source:
        - "web": Recherche web
        - "local": Fichiers locaux
        - "knowledge": Base de connaissances
        """
        if not self.llm_client:
            return None

        if source == "web":
            return await self._search_web(query)
        elif source == "local":
            return await self._search_local(query)
        elif source == "knowledge":
            return await self._search_knowledge(query)
        
        return None

    async def _search_web(self, query: str) -> Optional[Dict]:
        """Real web search using web tools"""
        from ..web_tools import get_web_tools
        
        try:
            web_tools = get_web_tools()
            results = await web_tools.search.search(query, num_results=5)
            
            if not results:
                return None
            
            content_parts = [f"Search results for: {query}\n"]
            for i, r in enumerate(results, 1):
                content_parts.append(f"{i}. {r.title}")
                content_parts.append(f"   URL: {r.url}")
                content_parts.append(f"   {r.snippet}\n")
            
            return {
                "source": "web",
                "query": query,
                "content": "\n".join(content_parts),
                "confidence": 0.8,
                "type": "search_results",
                "results": [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in results]
            }
        except Exception as e:
            logger.warning(f"[ResearchAgent] Web search error: {e}")
            return None

    async def _search_local(self, query: str) -> Optional[Dict]:
        """Recherche dans les fichiers locaux"""
        try:
            from pathlib import Path
            base_dir = Path(__file__).parent.parent.parent.parent
            storage_dir = base_dir / "storage"
            
            results = []
            search_term = query.lower()
            
            if storage_dir.exists():
                for file in storage_dir.rglob("*.txt"):
                    try:
                        content = file.read_text(encoding="utf-8", errors="ignore")
                        if search_term in content.lower():
                            results.append({
                                "file": str(file.relative_to(base_dir)),
                                "snippet": content[:200]
                            })
                    except:
                        pass
            
            if results:
                return {
                    "source": "local",
                    "query": query,
                    "content": f"Trouvé {len(results)} fichiers: {results[:3]}",
                    "confidence": 0.8,
                    "type": "files",
                    "files": results[:5]
                }
        except Exception as e:
            logger.warning(f"[ResearchAgent] Local search error: {e}")
        
        return None

    async def _search_knowledge(self, query: str) -> Optional[Dict]:
        """Search in local knowledge base using semantic search"""
        from core.system.woven_memory import get_woven_memory
        
        try:
            wm = get_woven_memory()
            if wm.is_ready():
                results = await wm.search(query, limit=3)
                
                if results:
                    content = f"Knowledge base results for: {query}\n\n"
                    for r in results:
                        content += f"- {r.get('text', '')[:300]}...\n"
                    
                    return {
                        "source": "knowledge",
                        "query": query,
                        "content": content,
                        "confidence": 0.9,
                        "type": "knowledge"
                    }
        except Exception as e:
            logger.warning(f"[ResearchAgent] Knowledge search error: {e}")
        
        return None

    def _merge_results(self, results: List[Dict]) -> Dict:
        """Fusionne les résultats de plusieurs sources"""
        if len(results) == 1:
            return results[0]
        
        combined_content = []
        for r in results:
            content = r.get("content", "")
            if content:
                combined_content.append(f"[{r.get('source', 'unknown')}]: {content[:300]}")
        
        return {
            "merged": True,
            "content": "\n\n".join(combined_content[:3]),
            "sources_count": len(results)
        }

    def _calculate_confidence(self, results: List[Dict]) -> float:
        """Calcule le score de confiance global"""
        if not results:
            return 0.0
        
        confidences = [r.get("confidence", 0.5) for r in results]
        avg_confidence = sum(confidences) / len(confidences)
        
        bonus = min(0.2, len(results) * 0.05)
        
        return min(1.0, avg_confidence + bonus)


class DeepResearchAgent(ResearchAgent):
    """
    Agent de recherche approfondie - Multiples itérations.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.max_iterations = 10
        self.max_sources = 10
