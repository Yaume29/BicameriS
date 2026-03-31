"""
Web Tools Registration
=====================
Register web tools in the Tool Registry.
"""

import logging
from .tool_registry import get_tool_registry, register_tool
from .web_tools import get_web_tools, WebTools

logger = logging.getLogger("agents.web_tools_registration")


def register_web_tools():
    """Register all web tools in the registry"""
    registry = get_tool_registry()
    web_tools = get_web_tools()
    
    registry.register(
        name="web_search",
        description="Search the web for information. Returns list of results with titles, URLs, and snippets.",
        parameters={
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results", "default": 5}
        },
        function=lambda query, num_results=5: _sync_search(web_tools, query, num_results),
        category="research",
        enabled=False,
        examples=["Search for quantum computing recent advances", "Find best Python ML libraries 2024"]
    )
    
    registry.register(
        name="web_fetch",
        description="Fetch content from a URL. Returns page text, title, and metadata.",
        parameters={
            "url": {"type": "string", "description": "URL to fetch"},
            "mode": {"type": "string", "description": "text, markdown, or html", "default": "text"}
        },
        function=lambda url, mode="text": _sync_fetch(web_tools, url, mode),
        category="research",
        enabled=False,
        examples=["Fetch https://arxiv.org/abs/2401.00001", "Get content of Wikipedia page"]
    )
    
    registry.register(
        name="web_research",
        description="Complete research: search + fetch top sources. Best for gathering information on a topic.",
        parameters={
            "query": {"type": "string", "description": "Research question"},
            "num_sources": {"type": "integer", "description": "Number of sources", "default": 3}
        },
        function=lambda query, num_sources=3: _sync_research(web_tools, query, num_sources),
        category="research",
        enabled=False,
        examples=["Research about transformer attention mechanisms", "Find latest advances in nuclear fusion"]
    )
    
    registry.register(
        name="browser_navigate",
        description="Navigate to URL in browser and get page content. Best for interactive web pages.",
        parameters={
            "url": {"type": "string", "description": "URL to navigate to"}
        },
        function=lambda url: _sync_browser_navigate(web_tools, url),
        category="research",
        enabled=False,
        examples=["Navigate to GitHub and get trending repos"]
    )
    
    logger.info("[WebTools] Registered web_search, web_fetch, web_research, browser_navigate")


def _sync_search(web_tools: WebTools, query: str, num_results: int):
    """Sync wrapper for web search"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(web_tools.search(query, num_results), loop)
            return {"status": "ok", "results": [{"title": r.title, "url": r.url, "snippet": r.snippet} for r in future.result()]}
        else:
            return loop.run_until_complete(web_tools.search(query, num_results))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _sync_fetch(web_tools: WebTools, url: str, mode: str):
    """Sync wrapper for web fetch"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(web_tools.fetch.fetch(url, mode), loop)
            return future.result()
        else:
            return loop.run_until_complete(web_tools.fetch.fetch(url, mode))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _sync_research(web_tools: WebTools, query: str, num_sources: int):
    """Sync wrapper for research"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(web_tools.research(query, num_sources), loop)
            return future.result()
        else:
            return loop.run_until_complete(web_tools.research(query, num_sources))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _sync_browser_navigate(web_tools: WebTools, url: str):
    """Sync wrapper for browser navigate"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(web_tools.browser.navigate(url), loop)
            result = future.result()
            if result.get("status") == "ok":
                html = loop.run_until_complete(web_tools.browser.get_html())
                return {"status": "ok", "html": html[:50000], "url": url}
            return result
        else:
            return loop.run_until_complete(_browser_navigate_sync(web_tools, url))
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def _browser_navigate_sync(web_tools: WebTools, url: str):
    result = await web_tools.browser.navigate(url)
    if result.get("status") == "ok":
        html = await web_tools.browser.get_html()
        return {"status": "ok", "html": html[:50000], "url": url}
    return result
