"""
Coder Agent
===========
Agent de génération de code avec exécution et tests.
"""

import uuid
import asyncio
from typing import Dict, Optional, List

from ..base_agent import BaseAgent, AgentConfig, Task
from ...execution.inference_manager import get_inference_manager

logger = logging.getLogger("agents.coder")


class CoderAgent(BaseAgent):
    """
    Agent de codage - Génère du code avec exécution et validation.
    """

    def __init__(self, name: str = "Coder Agent", description: str = "", **kwargs):
        super().__init__(
            AgentConfig(
                name=name,
                description=description or "Agent de génération de code",
                temperature=0.5,
                max_iterations=3,
                **kwargs
            )
        )
        
        self.language: str = "python"
        self.run_tests: bool = True
        self.test_framework: str = "pytest"

    def set_language(self, language: str):
        """Configure le langage cible"""
        self.language = language

    async def think(self, task: Task) -> str:
        """Analyse et planifie la génération de code"""
        prompt = f"""Analyse cette tâche de codage:

Description: {task.description}
Langage: {self.language}

Détermine:
1. Fonctionnalité requise
2. Inputs/outputs attendus
3. Dépendances nécessaires
4. Cas de test à couvrir"""

        if not self.llm_client:
            return f"Plan: Générer du code {self.language} pour '{task.description}'"

        try:
            plan = self.llm_client.think(
                "You are a code planning assistant.",
                prompt,
                temperature=0.3
            )
            task.metadata["code_plan"] = plan
            return plan
        except Exception as e:
            logger.warning(f"[CoderAgent] Think error: {e}")
            return f"Plan: Générer du code {self.language}"

    async def execute(self, task: Task, plan: str) -> Dict:
        """Génère et exécute le code"""
        prompt = f"""Génère du code {self.language} selon ce plan:

Tâche: {task.description}
Plan: {plan}

Requirements:
1. Code propre et documenté
2. Gestion d'erreurs
3. Tests unitaires si pertinent
4. Retourne le code uniquement"""

        try:
            if self.llm_client:
                code = self.llm_client.think(
                    self.config.system_prompt or "You are a code generation assistant.",
                    prompt,
                    temperature=self.config.temperature
                )
            else:
                code = self._fallback_code(task.description)
            
            execution_result = None
            if self.run_tests:
                execution_result = await self._execute_code(code)
            
            return {
                "status": "ok",
                "code": code,
                "language": self.language,
                "execution": execution_result,
                "lines": len(code.split('\n'))
            }
            
        except Exception as e:
            logger.error(f"[CoderAgent] Execute error: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _execute_code(self, code: str) -> Dict:
        """Exécute le code généré"""
        try:
            inference_manager = get_inference_manager()
            
            if not inference_manager:
                return {"status": "skipped", "message": "No inference manager available"}
            
            result = inference_manager.execute_code(code, self.language)
            
            return {
                "status": "success" if result.get("returncode", 1) == 0 else "error",
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "returncode": result.get("returncode")
            }
            
        except Exception as e:
            logger.warning(f"[CoderAgent] Code execution error: {e}")
            return {"status": "error", "message": str(e)}

    def _fallback_code(self, description: str) -> str:
        """Code fallback quand pas de LLM"""
        return f'''# Code pour: {description}
# À implémenter

def main():
    """Point d'entrée"""
    pass

if __name__ == "__main__":
    main()
'''


class CodeReviewAgent(BaseAgent):
    """
    Agent de révision de code - Analyse et suggère des améliorations.
    """

    def __init__(self, **kwargs):
        super().__init__(
            AgentConfig(
                name="Code Review Agent",
                description="Agent de révision de code",
                temperature=0.3,
                max_iterations=1,
                **kwargs
            )
        )
        
        self.check_security: bool = True
        self.check_performance: bool = True

    async def think(self, task: Task) -> str:
        return f"Analyser le code pour: {task.description}"

    async def execute(self, task: Task, plan: str) -> Dict:
        """Analyse le code"""
        code = task.parameters.get("code", "")
        
        if not code:
            return {"status": "error", "message": "No code provided"}
        
        prompt = f"""Fais une revue de code complète:

Code à analyser:
```{code}```

Analyse:
1. Bugs potentiels
2. Problèmes de sécurité
3. Performance
4. Bonnes pratiques
5. Suggestions d'amélioration

Format JSON avec: issues[], suggestions[], score (0-10)"""

        try:
            if self.llm_client:
                review = self.llm_client.think(
                    "You are a code review expert.",
                    prompt,
                    temperature=0.3
                )
            else:
                review = "Analyse non disponible sans LLM"
            
            return {
                "status": "ok",
                "review": review,
                "code_lines": len(code.split('\n')),
                "checks": {
                    "security": self.check_security,
                    "performance": self.check_performance
                }
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}


class DebugAgent(CoderAgent):
    """
    Agent de débogage - Trouve et corrige les erreurs.
    """

    def __init__(self, **kwargs):
        super().__init__(name="Debug Agent", description="Agent de débogage", **kwargs)
        self.max_attempts = 5

    async def think(self, task: Task) -> str:
        return f"Analyser l'erreur: {task.description}"

    async def execute(self, task: Task, plan: str) -> Dict:
        """Corrige les erreurs dans le code"""
        code = task.parameters.get("code", "")
        error = task.parameters.get("error", "")
        
        prompt = f"""Corrige ce code avec l'erreur suivante:

Code:
```{code}```

Erreur:
{error}

Génère le code corrigé avec les explanations."""

        try:
            if self.llm_client:
                fixed_code = self.llm_client.think(
                    "You are a debugging expert. Fix the code and explain the fix.",
                    prompt,
                    temperature=0.3
                )
            else:
                fixed_code = code
            
            return {
                "status": "ok",
                "original_code": code,
                "fixed_code": fixed_code,
                "error": error
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
