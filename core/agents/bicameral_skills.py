"""
Bicameral Skills & Agents Integration
=====================================
Intégration des patterns skills/agents/hooks dans BicameriS.
Adaptation pour notre système bicaméral.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml

logger = logging.getLogger("bicameral_skills")

BASE_DIR = Path(__file__).parent.parent.parent.absolute()
SKILLS_DIR = BASE_DIR / "storage" / "skills-reference" / "skills"
AGENTS_DIR = BASE_DIR / "storage" / "skills-reference" / "agents"


@dataclass
class BicameralSkill:
    """Skill adapté pour BicameriS"""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    content: str = ""
    hooks: List[str] = field(default_factory=list)
    config: Dict = field(default_factory=dict)


@dataclass
class BicameralAgent:
    """Agent adapté pour BicameriS"""
    name: str
    description: str
    tools: List[str] = field(default_factory=list)
    model: str = "sonnet"
    color: str = "purple"
    content: str = ""
    bicameral: bool = True  # Utilise les deux hémisphères


@dataclass
class BicameralHook:
    """Hook adapté pour BicameriS"""
    id: str
    event: str  # pre_tick, post_tick, pre_dialogue, post_dialogue, mode_change
    matcher: str  # Pattern to match
    action: str  # Shell command or Python function
    priority: str = "standard"  # minimal, standard, strict
    enabled: bool = True


class BicameralSkillsManager:
    """
    Gestionnaire de skills et agents pour BicameriS.
    Permet d'utiliser les skills, agents et hooks avec notre système bicaméral.
    """
    
    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.agents_dir = AGENTS_DIR
        
        self._skills: Dict[str, BicameralSkill] = {}
        self._agents: Dict[str, BicameralAgent] = {}
        self._hooks: Dict[str, BicameralHook] = {}
        
        self._loaded = False
    
    def load_all(self):
        """Charge tous les skills, agents et hooks"""
        if self._loaded:
            return
        
        self._load_skills()
        self._load_agents()
        self._loaded = True
        
        logger.info(f"[BicameralSkills] Loaded {len(self._skills)} skills, {len(self._agents)} agents")
    
    def _load_skills(self):
        """Charge les skills"""
        if not self.skills_dir.exists():
            logger.warning("[BicameralSkills] Skills directory not found")
            return
        
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            
            try:
                content = skill_md.read_text(encoding="utf-8")
                
                # Parse frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        body = parts[2].strip()
                    else:
                        frontmatter = {}
                        body = content
                else:
                    frontmatter = {}
                    body = content
                
                skill = BicameralSkill(
                    name=frontmatter.get("name", skill_dir.name),
                    description=frontmatter.get("description", ""),
                    tools=frontmatter.get("tools", []),
                    content=body
                )
                
                self._skills[skill.name] = skill
                
            except Exception as e:
                logger.warning(f"[BicameralSkills] Failed to load skill {skill_dir.name}: {e}")
    
    def _load_agents(self):
        """Charge les agents"""
        if not self.agents_dir.exists():
            logger.warning("[BicameralSkills] Agents directory not found")
            return
        
        for agent_md in self.agents_dir.glob("*.md"):
            try:
                content = agent_md.read_text(encoding="utf-8")
                
                # Parse frontmatter
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        body = parts[2].strip()
                    else:
                        frontmatter = {}
                        body = content
                else:
                    frontmatter = {}
                    body = content
                
                agent = BicameralAgent(
                    name=frontmatter.get("name", agent_md.stem),
                    description=frontmatter.get("description", ""),
                    tools=frontmatter.get("tools", []),
                    model=frontmatter.get("model", "sonnet"),
                    color=frontmatter.get("color", "purple"),
                    content=body,
                    bicameral=True
                )
                
                self._agents[agent.name] = agent
                
            except Exception as e:
                logger.warning(f"[BicameralSkills] Failed to load agent {agent_md.stem}: {e}")
    
    def get_skill(self, name: str) -> Optional[BicameralSkill]:
        """Récupère un skill par nom"""
        if not self._loaded:
            self.load_all()
        return self._skills.get(name)
    
    def get_agent(self, name: str) -> Optional[BicameralAgent]:
        """Récupère un agent par nom"""
        if not self._loaded:
            self.load_all()
        return self._agents.get(name)
    
    def list_skills(self) -> List[Dict]:
        """Liste tous les skills disponibles"""
        if not self._loaded:
            self.load_all()
        
        return [
            {
                "name": skill.name,
                "description": skill.description,
                "tools": skill.tools
            }
            for skill in self._skills.values()
        ]
    
    def list_agents(self) -> List[Dict]:
        """Liste tous les agents disponibles"""
        if not self._loaded:
            self.load_all()
        
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "model": agent.model,
                "tools": agent.tools,
                "bicameral": agent.bicameral
            }
            for agent in self._agents.values()
        ]
    
    def get_relevant_skills(self, task_type: str) -> List[BicameralSkill]:
        """
        Récupère les skills pertinents pour un type de tâche.
        Utilisé par l'Éditeur Spécialiste pour déléguer.
        """
        if not self._loaded:
            self.load_all()
        
        relevant = []
        
        # Mapping des types de tâches vers les skills
        task_mapping = {
            "code_review": ["security-review", "coding-standards", "tdd-workflow"],
            "planning": ["planner", "architect", "blueprint"],
            "testing": ["tdd-workflow", "verification-loop", "e2e-testing"],
            "security": ["security-review", "security-scan", "safety-guard"],
            "documentation": ["doc-updater", "docs-lookup"],
            "refactoring": ["refactor-cleaner", "hexagonal-architecture"],
            "learning": ["continuous-learning-v2", "iterative-retrieval"],
        }
        
        skill_names = task_mapping.get(task_type, [])
        
        for name in skill_names:
            if name in self._skills:
                relevant.append(self._skills[name])
        
        return relevant
    
    def create_bicameral_agent(self, agent: BicameralAgent) -> Dict:
        """
        Crée un agent bicaméral à partir d'un agent.
        Combine l'agent avec notre système de deux hémisphères.
        """
        return {
            "name": f"bicameral-{agent.name}",
            "description": agent.description,
            "agent": agent.name,
            "left_hemisphere": {
                "role": "analytical",
                "system_prompt": f"You are the analytical part of {agent.name}.\n{agent.content[:500]}",
                "temperature": 0.3
            },
            "right_hemisphere": {
                "role": "intuitive",
                "system_prompt": f"You are the intuitive part of {agent.name}.\n{agent.content[:500]}",
                "temperature": 0.8
            },
            "synthesis_prompt": f"Combine analytical and intuitive perspectives for {agent.name}",
            "tools": agent.tools,
            "bicameral": True
        }


# Instance globale
_skills_manager: Optional[BicameralSkillsManager] = None


def get_skills_manager() -> BicameralSkillsManager:
    """Récupère l'instance globale du gestionnaire de skills"""
    global _skills_manager
    if _skills_manager is None:
        _skills_manager = BicameralSkillsManager()
    return _skills_manager
