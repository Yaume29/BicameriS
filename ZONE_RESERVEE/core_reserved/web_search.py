"""
Web Search Module - SearXNG + DuckDuckGo
Permet à Aetheris de rechercher et vérifier ses intuitions
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import quote


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    timestamp: str


class WebSearcher:
    """
    Moteur de recherche hybride:
    - SearXNG: Recherche locale/profonde (Docker)
    - DuckDuckGo: Recherche rapide mondiale
    """

    def __init__(
        self,
        searxng_url: str = "http://localhost:8080",
        use_duckduckgo: bool = True,
    ):
        self.searxng_url = searxng_url.rstrip("/")
        self.use_duckduckgo = use_duckduckgo
        self._results_history: List[SearchResult] = []

    def search(
        self, query: str, sources: Optional[List[str]] = None, max_results: int = 5
    ) -> List[SearchResult]:
        """
        Recherche multi-sources

        Args:
            query: Requête de recherche
            sources: ['searxng', 'duckduckgo'] ou None pour tous
            max_results: Nombre de résultats par source

        Returns:
            Liste de SearchResult
        """
        results = []

        if sources is None:
            sources = ["searxng"]
            if self.use_duckduckgo:
                sources.append("duckduckgo")

        if "searxng" in sources:
            results.extend(self._search_searxng(query, max_results))

        if "duckduckgo" in sources:
            results.extend(self._search_duckduckgo(query, max_results))

        self._results_history.extend(results)
        return results

    def _search_searxng(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Recherche via SearXNG (local/Docker)"""
        try:
            import requests

            url = f"{self.searxng_url}/search"
            params = {
                "q": query,
                "format": "json",
                "engines": "google,bing,duckduckgo",
                "num_results": max_results,
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                results = []

                for r in data.get("results", [])[:max_results]:
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            snippet=r.get("content", r.get("snippet", "")),
                            source="searxng",
                            timestamp=datetime.now().isoformat(),
                        )
                    )
                return results

        except ImportError:
            print("[WEB_SEARCH] Requests non installé")
        except Exception as e:
            print(f"[WEB_SEARCH] Erreur SearXNG: {e}")

        return []

    def _search_duckduckgo(
        self, query: str, max_results: int = 5
    ) -> List[SearchResult]:
        """Recherche via DuckDuckGo (HTML scraping)"""
        try:
            from bs4 import BeautifulSoup
            import requests

            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                results = []

                for result in soup.select(".result")[:max_results]:
                    title_elem = result.select_one(".result__title")
                    url_elem = result.select_one(".result__url")
                    snippet_elem = result.select_one(".result__snippet")

                    if title_elem:
                        results.append(
                            SearchResult(
                                title=title_elem.get_text(strip=True),
                                url=url_elem.get_text(strip=True) if url_elem else "",
                                snippet=(
                                    snippet_elem.get_text(strip=True)
                                    if snippet_elem
                                    else ""
                                ),
                                source="duckduckgo",
                                timestamp=datetime.now().isoformat(),
                            )
                        )
                return results

        except ImportError:
            print("[WEB_SEARCH] BeautifulSoup4 non installé")
        except Exception as e:
            print(f"[WEB_SEARCH] Erreur DuckDuckGo: {e}")

        return []

    def search_and_summarize(self, query: str, max_results: int = 3) -> str:
        """
        Recherche et retourne un résumé textuel
        """
        results = self.search(query, max_results=max_results)

        if not results:
            return f"Aucun résultat pour: {query}"

        summary = f"🔍 Résultats pour '{query}':\n\n"

        for i, r in enumerate(results, 1):
            summary += f"{i}. {r.title}\n"
            summary += f"   📎 {r.url}\n"
            summary += f"   💬 {r.snippet[:200]}...\n"
            summary += f"   Source: {r.source}\n\n"

        return summary

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Retourne l'historique des recherches"""
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source,
                "timestamp": r.timestamp,
            }
            for r in self._results_history[-limit:]
        ]

    def clear_history(self):
        """Efface l'historique"""
        self._results_history.clear()

    def get_stats(self) -> Dict:
        """Statistiques du module"""
        searx_count = sum(1 for r in self._results_history if r.source == "searxng")
        ddg_count = sum(1 for r in self._results_history if r.source == "duckduckgo")

        return {
            "total_searches": len(self._results_history),
            "searxng_queries": searx_count,
            "duckduckgo_queries": ddg_count,
            "searxng_url": self.searxng_url,
            "duckduckgo_enabled": self.use_duckduckgo,
        }


# Instance globale
_web_searcher = None


def get_web_searcher() -> Optional[WebSearcher]:
    return _web_searcher


def init_web_searcher(
    searxng_url: str = "http://localhost:8080", use_duckduckgo: bool = True
) -> WebSearcher:
    global _web_searcher
    _web_searcher = WebSearcher(searxng_url=searxng_url, use_duckduckgo=use_duckduckgo)
    return _web_searcher
