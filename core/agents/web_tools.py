"""
Web Tools for Agents
====================
Web search, fetch, and browser automation tools.
Connects agents to the real internet.
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from urllib.parse import quote, urlparse
import logging

logger = logging.getLogger("agents.web_tools")


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str


class WebSearchTool:
    """
    Web search tool using multiple backends.
    Supports: SearX, DuckDuckGo, Bing (optional)
    """
    
    def __init__(self, searx_url: str = None):
        self.searx_url = searx_url or "http://localhost:8080"
        self.session = None
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search(self, query: str, num_results: int = 10) -> List[SearchResult]:
        """
        Search the web using available backends.
        """
        results = []
        
        try:
            results = await self._search_searx(query, num_results)
        except Exception as e:
            logger.warning(f"SearX failed: {e}")
            try:
                results = await self._search_duckduckgo(query, num_results)
            except Exception as e2:
                logger.warning(f"DuckDuckGo failed: {e2}")
        
        return results[:num_results]
    
    async def _search_searx(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using local SearX instance"""
        session = await self._get_session()
        
        params = {
            "q": query,
            "format": "json",
            "engines": "google,duckduckgo,bing",
            "num_results": num_results
        }
        
        try:
            async with session.get(f"{self.searx_url}/search", params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = []
                    
                    for r in data.get("results", []):
                        results.append(SearchResult(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            snippet=r.get("content", ""),
                            source=r.get("engine", "searx")
                        ))
                    return results
        except Exception as e:
            logger.error(f"SearX search error: {e}")
        
        return []
    
    async def _search_duckduckgo(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo HTML"""
        session = await self._get_session()
        
        url = "https://html.duckduckgo.com/html/"
        data = {"q": query, "b": ""}
        
        try:
            async with session.post(url, data=data, timeout=10) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    results = []
                    
                    for match in re.finditer(r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>', html):
                        url, title, snippet = match.groups()
                        results.append(SearchResult(
                            title=title.strip(),
                            url=url,
                            snippet=snippet.strip(),
                            source="duckduckgo"
                        ))
                        if len(results) >= num_results:
                            break
                    
                    return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return []


class WebFetchTool:
    """
    Fetch web page content.
    Supports: plain text, markdown, screenshots (future)
    """
    
    def __init__(self):
        self.session = None
        self.user_agent = "Palladion/1.0 (Research Agent)"
    
    async def _get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent}
            )
        return self.session
    
    async def fetch(self, url: str, mode: str = "text") -> Dict[str, Any]:
        """
        Fetch a web page.
        
        Args:
            url: URL to fetch
            mode: "text", "markdown", "html"
        
        Returns:
            Dict with content, title, status
        """
        session = await self._get_session()
        
        try:
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    return {"status": "error", "message": f"HTTP {resp.status}"}
                
                content = await resp.text()
                
                if mode == "html":
                    return {
                        "status": "ok",
                        "content": content,
                        "url": str(resp.url),
                        "status_code": resp.status
                    }
                
                title = self._extract_title(content)
                text = self._strip_html(content)
                
                if mode == "markdown":
                    text = self._html_to_markdown(text)
                
                return {
                    "status": "ok",
                    "content": text[:50000],
                    "title": title,
                    "url": str(resp.url),
                    "status_code": resp.status
                }
        
        except asyncio.TimeoutError:
            return {"status": "error", "message": "Timeout"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _extract_title(self, html: str) -> str:
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        return match.group(1).strip() if match else ""
    
    def _strip_html(self, html: str) -> str:
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'&#\d+;', '', text)
        return text.strip()
    
    def _html_to_markdown(self, text: str) -> str:
        text = re.sub(r'^### (.+)$', r'### \1', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$', r'## \1', text, flags=re.MULTILINE)
        text = re.sub(r'^# (.+)$', r'# \1', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*(.+?)\*\*', r'**\1**', text)
        text = re.sub(r'\*(.+?)\*', r'*\1*', text)
        return text


class BrowserTool:
    """
    Browser automation for agents.
    Can take screenshots, interact with pages, execute JS.
    Requires: playwright or selenium (optional)
    """
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def init(self, headless: bool = True):
        """Initialize browser"""
        try:
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.page = await self.browser.new_page()
            logger.info("[Browser] Initialized")
            return True
        except ImportError:
            logger.warning("[Browser] Playwright not installed")
            return False
        except Exception as e:
            logger.error(f"[Browser] Init failed: {e}")
            return False
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        if not self.page:
            return {"status": "error", "message": "Browser not initialized"}
        
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            title = await self.page.title()
            return {"status": "ok", "url": url, "title": title}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def screenshot(self, path: str = None) -> Optional[bytes]:
        """Take screenshot"""
        if not self.page:
            return None
        
        try:
            return await self.page.screenshot(path=path, full_page=True)
        except Exception as e:
            logger.error(f"[Browser] Screenshot failed: {e}")
            return None
    
    async def get_html(self) -> str:
        """Get page HTML"""
        if not self.page:
            return ""
        return await self.page.content()
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element"""
        if not self.page:
            return {"status": "error", "message": "Browser not initialized"}
        
        try:
            await self.page.click(selector)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into element"""
        if not self.page:
            return {"status": "error", "message": "Browser not initialized"}
        
        try:
            await self.page.fill(selector, text)
            return {"status": "ok"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def evaluate(self, js: str) -> Any:
        """Execute JavaScript"""
        if not self.page:
            return None
        return await self.page.evaluate(js)
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


class WebTools:
    """
    Unified web tools for agents.
    Combines search, fetch, and browser.
    """
    
    def __init__(self, searx_url: str = None):
        self.search = WebSearchTool(searx_url)
        self.fetch = WebFetchTool()
        self.browser = BrowserTool()
    
    async def research(self, query: str, num_sources: int = 5) -> Dict[str, Any]:
        """
        Complete research: search + fetch top results.
        """
        results = await self.search.search(query, num_results=num_sources)
        
        research = {
            "query": query,
            "sources": [],
            "summary": ""
        }
        
        for r in results:
            fetch_result = await self.fetch.fetch(r.url, mode="text")
            if fetch_result.get("status") == "ok":
                research["sources"].append({
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "content": fetch_result.get("content", "")[:2000]
                })
        
        if research["sources"]:
            research["summary"] = self._generate_summary(research["sources"])
        
        return research
    
    def _generate_summary(self, sources: List[Dict]) -> str:
        """Generate summary from sources"""
        summaries = []
        for s in sources[:3]:
            content = s.get("content", "")[:300]
            if content:
                summaries.append(f"- {s.get('title')}: {content}...")
        return "\n".join(summaries)


_global_web_tools: Optional[WebTools] = None


def get_web_tools(searx_url: str = None) -> WebTools:
    """Get global web tools instance"""
    global _global_web_tools
    if _global_web_tools is None:
        _global_web_tools = WebTools(searx_url)
    return _global_web_tools
