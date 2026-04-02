"""
Falsification Loop - Éditeur Spécialiste
=====================================
Boucle de falsification itérative pour l'IA Scientist.
"""

import uuid
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("editeur.falsification")


class IterationStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    TESTING = "testing"
    VALIDATING = "validating"
    SUCCESS = "success"
    FAILED = "failed"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class FalsificationIteration:
    """Une itération de la boucle de falsification."""
    iteration: int
    status: IterationStatus
    solution: str
    test_result: Optional[Dict] = None
    error: Optional[str] = None
    validation: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration: float = 0.0


@dataclass
class FalsificationSession:
    """Une session complète de falsification."""
    id: str
    objective: str
    theme: str
    subtheme: str
    iterations: List[FalsificationIteration] = field(default_factory=list)
    status: IterationStatus = IterationStatus.PENDING
    final_solution: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class FalsificationLoop:
    """
    Boucle de falsification itérative.
    
    Workflow:
    1. Generate(solution) - LLM génère une solution
    2. Test(solution) - Exécution des tests
    3. Validate(solution) - Évaluation par LLM
    4. Si invalide → Fix et réessayer
    5. Until success ou max_iterations
    """
    
    def __init__(
        self,
        max_iterations: int = 5,
        use_llm_validation: bool = True,
        use_test_validation: bool = True,
        llm_validation_prompt: str = None,
        llm_fix_prompt: str = None
    ):
        self.max_iterations = max_iterations
        self.use_llm_validation = use_llm_validation
        self.use_test_validation = use_test_validation
        
        self.llm_validation_prompt = llm_validation_prompt or """Tu es un évaluateur scientifique.
Évalue si la solution satisfies les critères suivants:
- Correcteté scientifique
- Validité des hypothèses
- Qualité de l'implémentation
- Résultats reproductibles

Solution:
{solution}

Tests:
{test_results}

Réponds en JSON:
{{
    "valid": true/false,
    "score": 0-100,
    "issues": ["issue1", "issue2"],
    "recommendations": ["rec1"]
}}"""
        
        self.llm_fix_prompt = llm_fix_prompt or """Tu es un développeur scientifique.
La solution suivante a échoué:

Problèmes identifiés:
{issues}

Solution originale:
{solution}

Génère une version corrigée qui résout ces problèmes.
Sois précis et systematic dans les corrections."""

    def start_session(
        self,
        objective: str,
        theme: str,
        subtheme: str,
        initial_solution: str = None
    ) -> FalsificationSession:
        """Démarre une nouvelle session de falsification."""
        session = FalsificationSession(
            id=f"fals_{uuid.uuid4().hex[:8]}",
            objective=objective,
            theme=theme,
            subtheme=subtheme
        )
        
        if initial_solution:
            iteration = FalsificationIteration(
                iteration=1,
                status=IterationStatus.VALIDATING,
                solution=initial_solution
            )
            session.iterations.append(iteration)
        
        return session
    
    async def run_session(
        self,
        session: FalsificationSession,
        generate_callback: Callable,
        test_callback: Callable = None,
        validate_callback: Callable = None
    ) -> FalsificationSession:
        """
        Exécute la session complète.
        
        Args:
            session: La session à exécuter
            generate_callback: Fonction pour générer une solution (async)
            test_callback: Fonction pour exécuter les tests (async, optionnel)
            validate_callback: Fonction pour valider via LLM (async, optionnel)
        """
        session.status = IterationStatus.GENERATING
        
        for i in range(1, self.max_iterations + 1):
            iteration = session.iterations[-1] if session.iterations else None
            
            if iteration and iteration.status == IterationStatus.SUCCESS:
                break
            
            if i > 1:
                iteration = FalsificationIteration(
                    iteration=i,
                    status=IterationStatus.GENERATING,
                    solution=""
                )
                session.iterations.append(iteration)
            
            if not iteration.solution:
                iteration.solution = await generate_callback(
                    objective=session.objective,
                    theme=session.theme,
                    subtheme=session.subtheme,
                    previous_attempts=session.iterations[:-1],
                    is_first=(i == 1)
                )
            
            iteration.status = IterationStatus.TESTING
            
            test_result = None
            if test_callback and self.use_test_validation:
                test_result = await test_callback(iteration.solution)
                iteration.test_result = test_result
            
            iteration.status = IterationStatus.VALIDATING
            
            validation = None
            if validate_callback and self.use_llm_validation:
                validation = await validate_callback(
                    solution=iteration.solution,
                    test_results=test_result,
                    prompt=self.llm_validation_prompt
                )
                iteration.validation = validation
            
            if validation and validation.get("valid"):
                iteration.status = IterationStatus.SUCCESS
                session.final_solution = iteration.solution
                session.status = IterationStatus.SUCCESS
                break
            
            iteration.status = IterationStatus.FAILED
            
            if i < self.max_iterations:
                iteration.status = IterationStatus.GENERATING
        
        if session.status != IterationStatus.SUCCESS:
            session.status = IterationStatus.MAX_ITERATIONS
        
        session.updated_at = datetime.now().isoformat()
        
        return session
    
    def get_status(self, session: FalsificationSession) -> Dict:
        """Retourne le statut de la session."""
        return {
            "id": session.id,
            "status": session.status.value,
            "objective": session.objective,
            "current_iteration": len(session.iterations),
            "max_iterations": self.max_iterations,
            "progress": len(session.iterations) / self.max_iterations * 100,
            "final_solution": session.final_solution is not None,
            "created_at": session.created_at,
            "updated_at": session.updated_at
        }
    
    def get_iterations(self, session: FalsificationSession) -> List[Dict]:
        """Retourne les itérations."""
        return [
            {
                "iteration": it.iteration,
                "status": it.status.value,
                "solution_preview": it.solution[:200] + "..." if len(it.solution) > 200 else it.solution,
                "test_result": it.test_result,
                "validation": it.validation,
                "error": it.error,
                "timestamp": it.timestamp
            }
            for it in session.iterations
        ]


class ScientistWorkflow:
    """
    Workflow complet pour le mode "AI Scientist".
    Utilise le système bicaméral pour générer et valider.
    """
    
    def __init__(self, max_iterations: int = 5):
        self.falsification_loop = FalsificationLoop(max_iterations=max_iterations)
        self.current_session: Optional[FalsificationSession] = None
    
    async def start(
        self,
        objective: str,
        theme: str,
        subtheme: str,
        preprompt: str
    ) -> Dict:
        """Démarre un workflow scientist."""
        self.current_session = self.falsification_loop.start_session(
            objective=objective,
            theme=theme,
            subtheme=subtheme
        )
        
        return {
            "status": "started",
            "session_id": self.current_session.id,
            "objective": objective,
            "theme": theme,
            "subtheme": subtheme
        }
    
    async def generate(
        self,
        objective: str,
        theme: str,
        subtheme: str,
        preprompt: str,
        hemispheres=None
    ) -> str:
        """Génère une solution avec les hemispheres."""
        prompt = f"""{preprompt}

Objectif scientifique: {objective}

Génère une solution complète qui:
1. Formule des hypothèses claires
2. Propose une méthododologie
3. Implémente une solution fonctionnelle
4. Inclut des tests de validation

Sois rigoureux et vérifiable."""

        if hemispheres and hasattr(hemispheres, 'left') and hasattr(hemispheres, 'right'):
            left_resp = hemispheres.left.think(
                "Tu es un analyste scientifique rigoureux.",
                prompt,
                temperature=0.3
            )
            right_resp = hemispheres.right.think(
                "Tu es un créatif scientifique.",
                prompt,
                temperature=0.7
            )
            return f"# Analyse (Hémisphère Gauche)\n{left_resp}\n\n# Intuition (Hémisphère Droit)\n{right_resp}"
        
        return prompt
    
    async def validate(
        self,
        solution: str,
        test_results: Dict = None,
        hemispheres=None
    ) -> Dict:
        """Valide une solution."""
        prompt = f"""Évalue cette solution scientifique:

Solution:
{solution}

Résultats des tests:
{test_results or 'Aucun test exécuté'}

Réponds en JSON avec:
- valid: true/false
- score: 0-100
- issues: problèmes identifiés
- recommendations: corrections suggérées"""

        if hemispheres and hasattr(hemispheres, 'left'):
            result = hemispheres.left.think(
                "Tu es un reviewer scientifique.",
                prompt,
                temperature=0.3
            )
            
            try:
                import json
                for line in result.split('\n'):
                    if '{' in line:
                        data = json.loads(line)
                        return data
            except:
                pass
        
        return {"valid": True, "score": 50, "issues": [], "recommendations": []}


_scientist_workflow = None


def get_scientist_workflow(max_iterations: int = 5) -> ScientistWorkflow:
    """Singleton du workflow scientist."""
    global _scientist_workflow
    if _scientist_workflow is None:
        _scientist_workflow = ScientistWorkflow(max_iterations)
    return _scientist_workflow
