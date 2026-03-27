"""
BICAMERIS - Sensory Buffer (Data Hose)
====================================
Passive semantic noise injection to prevent cognitive collapse.
Provides peripheral concepts from external data streams.
"""

import asyncio
import logging
import random
from collections import deque
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logging.warning("[SensoryBuffer] httpx not installed - external feeds disabled")

logger = logging.getLogger(__name__)


class SensoryBuffer:
    """
    Circular buffer that stores external semantic noise.
    Prevents "Semantic Collapse" by injecting random concepts.
    """

    def __init__(self, max_size: int = 50, fetch_interval: int = 60):
        self.stream: deque = deque(maxlen=max_size)
        self.fetch_interval = fetch_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._sources = [
            self._fetch_hackernews,
            self._fetch_crypto,
        ]

    async def start(self):
        """Start the sensory daemon"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info("[SensoryBuffer] ✅ Daemon started")

    async def stop(self):
        """Stop the sensory daemon"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[SensoryBuffer] ⏹️ Daemon stopped")

    async def _listen_loop(self):
        """Background loop that fetches external data"""
        while self._running:
            try:
                source = random.choice(self._sources)
                data = await source()
                if data:
                    self.stream.append(data)
                    logger.debug(f"[SensoryBuffer] Added: {data.get('title', '')[:50]}")
            except Exception as e:
                logger.warning(f"[SensoryBuffer] Fetch error: {e}")

            await asyncio.sleep(self.fetch_interval)

    async def _fetch_hackernews(self) -> Optional[Dict[str, Any]]:
        """Fetch top story from HackerNews (mock for now)"""
        if not HTTPX_AVAILABLE:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10.0
                )
                if response.status_code == 200:
                    story_ids = response.json()[:5]
                    story_id = random.choice(story_ids)
                    story_response = await client.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    )
                    story = story_response.json()
                    return {
                        "source": "hackernews",
                        "title": story.get("title", ""),
                        "keywords": self._extract_keywords(story.get("title", "")),
                        "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            logger.debug(f"[SensoryBuffer] HN fetch failed: {e}")
        return None

    async def _fetch_crypto(self) -> Optional[Dict[str, Any]]:
        """Fetch crypto ticker (mock for now)"""
        if not HTTPX_AVAILABLE:
            return None
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd",
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "source": "crypto",
                        "title": f"BTC: ${data.get('bitcoin', {}).get('usd', 0)}",
                        "keywords": ["bitcoin", "crypto", "finance"],
                        "timestamp": datetime.now().isoformat(),
                    }
        except Exception as e:
            logger.debug(f"[SensoryBuffer] Crypto fetch failed: {e}")
        return None

    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        words = text.lower().split()
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        return [w for w in words if w not in stopwords and len(w) > 3][:5]

    def get_peripheral_noise(self, count: int = 2) -> List[str]:
        """
        Get random concepts from the buffer.
        AutonomousThinker calls this during tick().
        """
        if len(self.stream) < count:
            return [item.get("title", "") for item in self.stream]

        samples = random.sample(list(self.stream), min(count, len(self.stream)))
        return [item.get("title", "") for item in samples]

    def get_latest_keywords(self, count: int = 5) -> List[str]:
        """Get recent keywords for context injection"""
        keywords = []
        for item in list(self.stream)[-10:]:
            keywords.extend(item.get("keywords", []))
        return list(set(keywords))[:count]


_sensory_buffer = None


def get_sensory_buffer() -> SensoryBuffer:
    global _sensory_buffer
    if _sensory_buffer is None:
        _sensory_buffer = SensoryBuffer()
    return _sensory_buffer
