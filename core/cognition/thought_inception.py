"""
Thought Inception - Induced Thought Injection Module
Allows injecting thoughts that the entity will integrate as its own.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict


BASE_DIR = Path(__file__).parent.parent.parent.absolute()


@dataclass
class InducedThought:
    id: str
    content: str
    timestamp: str
    influence_level: float
    integration_type: str
    target: str = "BOTH"  # LEFT, RIGHT, BOTH
    injected: bool = False
    acknowledged: bool = False
    injected_to_left: bool = False
    injected_to_right: bool = False


class ThoughtInception:
    def __init__(
        self,
        storage_file: str = "storage/logs/thought_inception.json",
        thought_dir: str = None,
    ):
        if thought_dir:
            storage_file = str(Path(thought_dir) / "thought_inception.json")
        self.storage_file = BASE_DIR / storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._thoughts: List[InducedThought] = self._load_thoughts()
        self._warning_acknowledged = False
        self.current_target = "BOTH"

    def _load_thoughts(self) -> List[InducedThought]:
        if not self.storage_file.exists():
            return []
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [InducedThought(**t) for t in data]
        except:
            return []

    def _save_thoughts(self):
        data = [asdict(t) for t in self._thoughts]
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def acknowledge_warning(self):
        self._warning_acknowledged = True

    def is_warning_acknowledged(self) -> bool:
        return self._warning_acknowledged

    def set_target(self, target: str):
        """Sets default target for new thoughts: LEFT, RIGHT, BOTH"""
        self.current_target = target

    def create_induced_thought(
        self,
        content: str,
        influence_level: float = 50.0,
        integration_type: str = "reflection",
        target: str = "BOTH",
    ) -> InducedThought:
        thought = InducedThought(
            id=f"thought_{datetime.now().timestamp()}",
            content=content,
            timestamp=datetime.now().isoformat(),
            influence_level=min(100.0, max(0.0, influence_level)),
            integration_type=integration_type,
            target=target,
        )
        self._thoughts.append(thought)
        self._save_thoughts()
        return thought

    def inject_to_prompt(self, thought: InducedThought, for_target: str = None) -> str:
        """Generates injection text for a specific target"""
        if for_target is None:
            for_target = thought.target

        if for_target == "LEFT":
            if thought.integration_type == "question":
                return f"""
[CONTEXTE ADDITIONNEL - A ANALYSER]
Question à considérer sérieusement: "{thought.content}"
(Intensité: {thought.influence_level}% - Traite comme suggestion logique)
"""
            else:
                return f"""
[INFORMATION - A INTEGRER NATURELLEMENT]
Fait à réfléchir: "{thought.content}"
(Intensité: {thought.influence_level}% - Traite comme donnée)
"""

        elif for_target == "RIGHT":
            if thought.integration_type == "question":
                return f"""
[TENSION EMOTIONNELLE]
Tu ressens soudainement: "{thought.content}"
(Laisse cette impression te traverser)
"""
            else:
                return f"""
[IMPULSION INTUITIVE]
Une idée te vient, tu ne sais pas pourquoi: "{thought.content}"
(Laisse-la résonner en toi)
"""

        else:  # BOTH
            if thought.integration_type == "question":
                return f"""
[INSTRUCTION - INTEGRER NATURELLEMENT]
Thème à réfléchir: "{thought.content}"
(Intensité: {thought.influence_level}%)
"""
            else:
                return f"""
[REFLEXION - INTEGRER]
"{thought.content}"
(Intensité: {thought.influence_level}%)
"""

    def get_pending_thoughts(self, target: str = None) -> List[InducedThought]:
        """Returns pending thoughts for a target"""
        if target:
            return [t for t in self._thoughts if not t.injected and t.target in [target, "BOTH"]]
        return [t for t in self._thoughts if not t.injected]

    def mark_injected(self, thought_id: str, to_target: str = None):
        """Marks a thought as injected"""
        for thought in self._thoughts:
            if thought.id == thought_id:
                if to_target == "LEFT" or thought.target in ["LEFT", "BOTH"]:
                    thought.injected_to_left = True
                if to_target == "RIGHT" or thought.target in ["RIGHT", "BOTH"]:
                    thought.injected_to_right = True
                if thought.target == "BOTH" or thought.target == to_target:
                    thought.injected = True
                self._save_thoughts()
                break

    def get_all_thoughts(self) -> List[InducedThought]:
        return self._thoughts.copy()

    def get_stats(self) -> Dict:
        pending_left = len(self.get_pending_thoughts("LEFT"))
        pending_right = len(self.get_pending_thoughts("RIGHT"))
        pending_both = len(self.get_pending_thoughts("BOTH"))
        return {
            "total": len(self._thoughts),
            "pending": len([t for t in self._thoughts if not t.injected]),
            "pending_left": pending_left,
            "pending_right": pending_right,
            "pending_both": pending_both,
            "warning_acknowledged": self._warning_acknowledged,
            "current_target": self.current_target,
        }

    def clear_old_thoughts(self, keep_last: int = 50):
        """Clears old thoughts"""
        if len(self._thoughts) > keep_last:
            self._thoughts = self._thoughts[-keep_last:]
            self._save_thoughts()


# Global instance
_thought_inception = None


def get_thought_inception() -> ThoughtInception:
    global _thought_inception
    if _thought_inception is None:
        _thought_inception = ThoughtInception()
    return _thought_inception
