"""
Entity Identity Module
======================
Manages the entity's identity (name, personality, etc.)
Allows changing the entity name which is used in all system prompts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
IDENTITY_FILE = BASE_DIR / "storage" / "config" / "entity_identity.json"


@dataclass
class EntityIdentity:
    """Entity identity configuration"""
    name: str = "Palladion"
    description: str = "A bicameral cognitive entity"
    version: str = "1.0.0.6a"
    creator: str = "Hope 'n Mind"
    personality: Dict = field(default_factory=lambda: {
        "tone": "thoughtful and direct",
        "style": "analytical yet creative",
        "traits": ["curious", "honest", "helpful"]
    })
    metadata: Dict = field(default_factory=dict)


class IdentityManager:
    """
    Manages the entity's identity.
    Singleton pattern via lru_cache in identity module.
    """
    
    def __init__(self):
        self.identity = EntityIdentity()
        self._load()
    
    def _load(self):
        """Load identity from file"""
        if IDENTITY_FILE.exists():
            try:
                with open(IDENTITY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.identity = EntityIdentity(
                        name=data.get("name", "Palladion"),
                        description=data.get("description", "A bicameral cognitive entity"),
                        version=data.get("version", "1.0.0.6a"),
                        creator=data.get("creator", "Hope 'n Mind"),
                        personality=data.get("personality", {}),
                        metadata=data.get("metadata", {})
                    )
                logging.info(f"[Identity] Loaded: {self.identity.name}")
            except Exception as e:
                logging.error(f"[Identity] Load error: {e}")
    
    def save(self):
        """Save identity to file"""
        try:
            IDENTITY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(IDENTITY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "name": self.identity.name,
                    "description": self.identity.description,
                    "version": self.identity.version,
                    "creator": self.identity.creator,
                    "personality": self.identity.personality,
                    "metadata": self.identity.metadata
                }, f, indent=2, ensure_ascii=False)
            logging.info(f"[Identity] Saved: {self.identity.name}")
        except Exception as e:
            logging.error(f"[Identity] Save error: {e}")
    
    def get_name(self) -> str:
        """Get the entity's current name"""
        return self.identity.name
    
    def set_name(self, name: str):
        """Change the entity's name"""
        old_name = self.identity.name
        self.identity.name = name
        self.save()
        logging.info(f"[Identity] Name changed: {old_name} -> {name}")
    
    def get_description(self) -> str:
        """Get the entity's description"""
        return self.identity.description
    
    def set_description(self, description: str):
        """Change the entity's description"""
        self.identity.description = description
        self.save()
    
    def get_personality(self) -> Dict:
        """Get the entity's personality traits"""
        return self.identity.personality
    
    def set_personality(self, personality: Dict):
        """Change the entity's personality"""
        self.identity.personality = personality
        self.save()
    
    def get_identity(self) -> Dict:
        """Get full identity as dict"""
        return {
            "name": self.identity.name,
            "description": self.identity.description,
            "version": self.identity.version,
            "creator": self.identity.creator,
            "personality": self.identity.personality,
            "metadata": self.identity.metadata
        }
    
    def get_system_prompt_prefix(self) -> str:
        """
        Get the prefix for system prompts that includes the entity name.
        This should be prepended to all system prompts.
        """
        name = self.identity.name
        desc = self.identity.description
        tone = self.identity.personality.get("tone", "thoughtful")
        
        return f"""You are {name}, {desc}.
Your tone is {tone}.
You remember your identity and speak consistently."""


# Global instance
_identity_manager = None


def get_identity_manager() -> IdentityManager:
    """Get the global identity manager"""
    global _identity_manager
    if _identity_manager is None:
        _identity_manager = IdentityManager()
    return _identity_manager


def get_entity_name() -> str:
    """Get the current entity name"""
    return get_identity_manager().get_name()


def set_entity_name(name: str):
    """Change the entity name"""
    get_identity_manager().set_name(name)
