"""
BICAMERIS - Dreamer Agent (Paradoxical Sleep)
==========================================
Semantic collision through vector inversion.
Generates metaphorical connections between distant concepts.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DreamerAgent:
    """
    Dreams to consolidate memory through semantic collision.
    Activated by KernelScheduler when entropy is very low.
    """

    def __init__(self):
        self.qdrant_client = None
        self.right_hemisphere = None
        self.left_hemisphere = None
        self._initialized = False
        self._init_clients()

    def _init_clients(self):
        """Initialize connections to Qdrant and hemispheres"""
        try:
            from core.system.hippocampus import get_hippocampus

            self.qdrant_client = get_hippocampus()
        except Exception as e:
            logger.warning(f"[Dreamer] Hippocampus unavailable: {e}")

        try:
            from core_reserved.right_hemisphere import get_right_hemisphere

            self.right_hemisphere = get_right_hemisphere()
        except Exception as e:
            logger.warning(f"[Dreamer] Right hemisphere unavailable: {e}")

        self._initialized = True
        logger.info("[Dreamer] ✅ Agent initialized")

    def trigger_rem_sleep(self) -> Optional[Dict[str, Any]]:
        """
        Trigger REM sleep cycle.
        Called by KernelScheduler when entropy < 0.1 for long period.
        """
        if not self._initialized or not self.qdrant_client:
            logger.warning("[Dreamer] Not initialized")
            return None

        try:
            seed_thought = self._get_random_thought()
            if not seed_thought:
                return {"status": "no_thoughts"}

            bizarre_thought = self._get_distant_thought(seed_thought)
            if not bizarre_thought:
                return {"status": "no_distant_thought"}

            dream = self._generate_dream(seed_thought, bizarre_thought)

            if dream:
                self._store_dream(dream, seed_thought, bizarre_thought)
                logger.info(f"[Dreamer] 🌙 Dream generated: {dream.get('content', '')[:50]}...")

            return dream

        except Exception as e:
            logger.error(f"[Dreamer] ❌ Dream failed: {e}")
            return {"status": "error", "error": str(e)}

    def _get_random_thought(self) -> Optional[Dict]:
        """Get a random thought from Qdrant"""
        try:
            from core.system.hippocampus import StoredThought

            thoughts = self.qdrant_client.get_pending_thoughts(limit=100)
            if not thoughts:
                return None
            import random

            thought = random.choice(thoughts)
            return {
                "id": thought.id,
                "content": thought.content,
                "timestamp": thought.timestamp,
                "context": thought.context,
            }
        except Exception as e:
            logger.warning(f"[Dreamer] Error getting random thought: {e}")
            return None

    def _get_distant_thought(self, seed: Dict) -> Optional[Dict]:
        """
        Find the most dissimilar thought (semantic inversion).
        In production, would use vector negation + search.
        """
        try:
            import random

            thoughts = self.qdrant_client.get_pending_thoughts(limit=100)
            if len(thoughts) < 2:
                return None

            distant = random.choice([t for t in thoughts if t.id != seed.get("id")])
            return {
                "id": distant.id,
                "content": distant.content,
                "timestamp": distant.timestamp,
                "context": distant.context,
            }
        except Exception as e:
            logger.warning(f"[Dreamer] Error getting distant thought: {e}")
            return None

    def _generate_dream(self, seed: Dict, distant: Dict) -> Optional[Dict]:
        """Force collision between two distant concepts via right hemisphere"""
        if not self.right_hemisphere:
            logger.warning("[Dreamer] No right hemisphere")
            return None

        prompt = f"""Rêve lucide. Relie ces deux concepts sans rapport à travers une métaphore poétique ou absurde:

Concept A: {seed.get("content", "")[:200]}
Concept B: {distant.get("content", "")[:200]}

Écris une histoire ou une image onirique qui Unit ces deux idées."""

        try:
            system_prompt = "Tu es le subconscient d'Aetheris. Tu génères des métaphores puissantes et des images oniriques."
            result = self.right_hemisphere.think(system_prompt, prompt, temperature=1.5)

            return {
                "content": result.get("content", ""),
                "seed_id": seed.get("id"),
                "distant_id": distant.get("id"),
                "timestamp": datetime.now().isoformat(),
                "type": "dream",
            }
        except Exception as e:
            logger.error(f"[Dreamer] Generation failed: {e}")
            return None

    def _store_dream(self, dream: Dict, seed: Dict, distant: Dict):
        """Store the dream in Qdrant and telemetry"""
        try:
            from core.system.hippocampus import StoredThought
            from core.system.telemetry import get_telemetry

            stored = StoredThought(
                id=f"dream_{datetime.now().timestamp()}",
                content=dream.get("content", ""),
                timestamp=dream.get("timestamp", ""),
                context=f"Dream: {seed.get('content', '')} <-> {distant.get('content', '')}",
                type="dream",
                status="completed",
                pulse_context=0.05,
            )
            self.qdrant_client.log_thought(stored)

            telemetry = get_telemetry()
            if telemetry:
                telemetry.log_event(
                    "dream_generated",
                    {
                        "dream": dream.get("content", "")[:200],
                        "seed": seed.get("id"),
                        "distant": distant.get("id"),
                    },
                )

        except Exception as e:
            logger.warning(f"[Dreamer] Storage failed: {e}")

    def is_available(self) -> bool:
        """Check if dreamer can operate"""
        return self._initialized


_dreamer_agent = None


def get_dreamer_agent() -> DreamerAgent:
    global _dreamer_agent
    if _dreamer_agent is None:
        _dreamer_agent = DreamerAgent()
    return _dreamer_agent
