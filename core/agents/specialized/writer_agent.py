"""
Writer Agent
============
Agent de rédaction et révision de contenu.
"""

import uuid
from typing import Dict, Optional

from ..base_agent import BaseAgent, AgentConfig, Task

logger = logging.getLogger("agents.writer")


class WriterAgent(BaseAgent):
    """
    Agent de rédaction - Génère et revise du contenu écrit.
    """

    def __init__(self, name: str = "Writer Agent", description: str = "", **kwargs):
        super().__init__(
            AgentConfig(
                name=name,
                description=description or "Agent de rédaction et révision",
                temperature=0.7,
                max_iterations=3,
                **kwargs
            )
        )
        
        self.style: str = "formal"
        self.target_length: str = "medium"
        self.include_examples: bool = True

    def set_style(self, style: str):
        """Configure le style d'écriture"""
        self.style = style

    async def think(self, task: Task) -> str:
        """Planifie la rédaction"""
        prompt = f"""Analyse cette tâche d'écriture et crée un plan:

Tâche: {task.description}

Détermine:
1. Type de contenu (article, résumé, document technique, etc.)
2. Structure recommandée
3. Points clés à couvrir
4. Style (formel, décontracté, technique)"""

        if not self.llm_client:
            return f"Plan: Écrire sur '{task.description}'"

        try:
            plan = self.llm_client.think(
                "You are a writing planner.",
                prompt,
                temperature=0.5
            )
            task.metadata["writing_plan"] = plan
            return plan
        except Exception as e:
            logger.warning(f"[WriterAgent] Think error: {e}")
            return f"Plan: Écrire sur '{task.description}'"

    async def execute(self, task: Task, plan: str) -> Dict:
        """Génère le contenu"""
        style_guide = self._get_style_guide()
        
        prompt = f"""Rédige du contenu selon ce plan:

Tâche: {task.description}

Plan: {plan}

Style: {self.style}
Longueur: {self.target_length}

{style_guide}

Génère le contenu complet."""

        try:
            if self.llm_client:
                content = self.llm_client.think(
                    self.config.system_prompt or "You are a professional writer.",
                    prompt,
                    temperature=self.config.temperature
                )
            else:
                content = f"Contenu pour: {task.description}"
            
            evaluation = await self.evaluate(content)
            
            return {
                "status": "ok",
                "content": content,
                "style": self.style,
                "length": len(content),
                "evaluation": {
                    "score": evaluation,
                    "quality": "good" if evaluation >= 0.7 else "needs_review"
                }
            }
            
        except Exception as e:
            logger.error(f"[WriterAgent] Execute error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_style_guide(self) -> str:
        """Retourne le guide de style selon la configuración"""
        guides = {
            "formal": "Utilisez un français soutenu, évite les contractions, Soins particulière à la grammaire.",
            "casual": "Utilisez un français décontracté, tons conversationnel, phrases courtes autorisées.",
            "technical": "Précision technique, définitions, exemples de code si pertinent, structure logique.",
            "creative": "Métaphores, imagery, engagement du lecteur, variation stylististique."
        }
        return guides.get(self.style, guides["formal"])


class EditorAgent(WriterAgent):
    """
    Agent de révision - Corrige et améliore le contenu existant.
    """

    def __init__(self, **kwargs):
        super().__init__(name="Editor Agent", description="Agent de révision", **kwargs)
        self.focus: str = "grammar"

    def set_focus(self, focus: str):
        """Configure le focus de révision"""
        self.focus = focus

    async def think(self, task: Task) -> str:
        """Analyse le contenu à réviser"""
        return f"Analyser le contenu pour: {self.focus}"

    async def execute(self, task: Task, plan: str) -> Dict:
        """Réviser le contenu"""
        content = task.parameters.get("content", "")
        
        if not content:
            return {"status": "error", "message": "No content to edit"}
        
        focus_instructions = {
            "grammar": "Corrige les fautes de grammaire, orthographe, conjugaison.",
            "style": "Améliore le style, clarté, fluidité.",
            "structure": "Améliore l'organisation, transitions, structure.",
            "all": "Revision complète: grammaire, style, structure."
        }
        
        prompt = f"""Révision de texte:

Contenu original:
{content}

Focus: {self.focus}

{focus_instructions.get(self.focus, focus_instructions['all'])}

Retourne le contenu révisé."""

        if self.llm_client:
            revised = self.llm_client.think(
                "You are a professional editor.",
                prompt,
                temperature=0.3
            )
        else:
            revised = content
        
        return {
            "status": "ok",
            "original": content,
            "revised": revised,
            "focus": self.focus,
            "changes_count": self._count_changes(content, revised)
        }

    def _count_changes(self, original: str, revised: str) -> int:
        """Compte les changements"""
        if original == revised:
            return 0
        
        orig_words = set(original.lower().split())
        rev_words = set(revised.lower().split())
        
        return len(rev_words - orig_words) + len(orig_words - rev_words)
