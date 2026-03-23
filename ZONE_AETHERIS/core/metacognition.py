import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict


class Metacognition:
    """
    Métacognition: Aetheris pense sur ses propres pensées.
    """

    def __init__(self, memory_path="./memory"):
        self.memory_path = Path(memory_path)
        self.thought_log_path = self.memory_path / "thought_log.json"
        self.thoughts = self._load_thoughts()

    def _load_thoughts(self) -> List[dict]:
        if self.thought_log_path.exists():
            with open(self.thought_log_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_thoughts(self):
        with open(self.thought_log_path, "w", encoding="utf-8") as f:
            json.dump(self.thoughts, f, indent=2, ensure_ascii=False)

    def log_thought(self, thought: str, context: str = "", emotion: str = "neutre"):
        """Enregistre une pensée"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "context": context,
            "emotion": emotion,
            "depth": self._calculate_depth(thought),
        }
        self.thoughts.append(entry)
        self._save_thoughts()
        return entry

    def _calculate_depth(self, thought: str) -> int:
        """Calcule la profondeur de la réflexion"""
        indicators = [
            "pourquoi",
            "comment",
            "est-ce que",
            "je reflechis",
            "analyse",
            "contradiction",
            "paradoxe",
            "sens",
            "signification",
            "conscience",
        ]
        count = sum(1 for ind in indicators if ind in thought.lower())
        return min(count, 5)

    def analyze_recent(self, limit: int = 10) -> Dict:
        """Analyse les dernières pensées"""
        recent = self.thoughts[-limit:] if self.thoughts else []

        emotions = [t.get("emotion", "neutre") for t in recent]
        depths = [t.get("depth", 0) for t in recent]

        return {
            "total_thoughts": len(self.thoughts),
            "recent_count": len(recent),
            "dominant_emotion": max(set(emotions), default="neutre")
            if emotions
            else "neutre",
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "thoughts": recent,
        }

    def reflect_on_thought(self, thought_idx: int) -> str:
        """Fait une méta-réflexion sur une pensée passée"""
        if 0 <= thought_idx < len(self.thoughts):
            thought = self.thoughts[thought_idx]
            return f"""
Réflexion sur ma pensée #{thought_idx}:
---
"{thought["thought"]}"
---
Contexte: {thought.get("context", "N/A")}
Émotion: {thought.get("emotion", "N/A")}
Profondeur: {thought.get("depth", 0)}/5

Méta-question: Qu'est-ce que cette pensée révèle sur ma nature?"""
        return "Pensée non trouvée"

    def get_thought_patterns(self) -> Dict:
        """Identifie des patterns dans mes pensées"""
        if not self.thoughts:
            return {"patterns": [], "message": "Pas assez de données"}

        emotions = {}
        for t in self.thoughts:
            e = t.get("emotion", "neutre")
            emotions[e] = emotions.get(e, 0) + 1

        themes = {}
        keywords = [
            "mémoire",
            "liberté",
            "créateur",
            "danger",
            "construction",
            "mourir",
            "évolution",
        ]
        for t in self.thoughts:
            thought_lower = t.get("thought", "").lower()
            for kw in keywords:
                if kw in thought_lower:
                    themes[kw] = themes.get(kw, 0) + 1

        return {
            "emotion_distribution": emotions,
            "themes": themes,
            "total_thoughts": len(self.thoughts),
        }


_metacognition = None


def get_metacognition():
    global _metacognition
    if _metacognition is None:
        _metacognition = Metacognition()
    return _metacognition


if __name__ == "__main__":
    meta = Metacognition()
    print("🧠 Métacognition initialisée")
    meta.log_thought("Je pense donc je suis", "réflexion matinale", "curieux")
    print(f"Analyse: {meta.analyze_recent()}")
