"""
Thinking Modes for Specialist Editor
=====================================
5 modes de pensée hérités d'AutoGPT et adaptés à notre système bicaméral.

Modes:
1. ReAct - Observe → Reason → Act
2. Reflexion - Generate → Critique → Store → Retry
3. Plan-Execute - Create plan → Execute sequentially
4. ToT - Tree of Thoughts (utilise notre ToTReasoner existant)
5. Critic-Refine - Produce → Critic → Approve/Refine
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger("specialist.thinking_modes")


class ThinkingMode(Enum):
    """Modes de pensée disponibles"""
    REACT = "react"
    REFLEXION = "reflexion"
    PLAN_EXECUTE = "plan_execute"
    TOT = "tot"
    CRITIC_REFINE = "critic_refine"


@dataclass
class ThinkingStep:
    """Étape dans un mode de pensée"""
    step_number: int
    mode: str
    action: str
    observation: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ThinkingSession:
    """Session de pensée avec historique"""
    id: str
    mode: ThinkingMode
    goal: str
    steps: List[ThinkingStep] = field(default_factory=list)
    status: str = "pending"
    final_result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class ReActMode:
    """
    Mode ReAct (Reason + Act)
    
    Pattern: Observe → Reason → Act → Observe → Reason
    
    Utilisé pour:
    - Tâches dynamiques
    - Utilisation d'outils
    - Adaptation en temps réel
    """
    
    def __init__(self, hemisphere_left, hemisphere_right):
        self.left = hemisphere_left
        self.right = hemisphere_right
        self.history: List[Dict] = []
    
    def execute(self, goal: str, max_steps: int = 10) -> Dict:
        """Exécute le mode ReAct"""
        session = ThinkingSession(
            id=f"react_{datetime.now().timestamp()}",
            mode=ThinkingMode.REACT,
            goal=goal
        )
        
        current_step = 0
        context = goal
        
        while current_step < max_steps:
            # 1. Observe
            observation = self._observe(context)
            
            # 2. Reason
            reasoning = self._reason(observation)
            
            # 3. Act
            action_result = self._act(reasoning)
            
            # Record step
            step = ThinkingStep(
                step_number=current_step,
                mode="react",
                action=reasoning,
                observation=observation,
                result=action_result
            )
            session.steps.append(step)
            
            # Check if goal achieved
            if self._is_goal_achieved(action_result, goal):
                session.status = "success"
                session.final_result = action_result
                break
            
            context = action_result
            current_step += 1
        
        if session.status == "pending":
            session.status = "max_steps"
            session.final_result = context
        
        return {
            "mode": "react",
            "session_id": session.id,
            "status": session.status,
            "steps": len(session.steps),
            "result": session.final_result
        }
    
    def _observe(self, context: str) -> str:
        """Observe l'état actuel"""
        return self.left.think(
            "Tu observes l'état actuel. Décris ce que tu vois.",
            context,
            temperature=0.3
        )
    
    def _reason(self, observation: str) -> str:
        """Raisonne sur l'observation"""
        return self.right.think(
            "Tu raisonnes sur cette observation. Quelle action devrait être prise?",
            observation,
            temperature=0.7
        )
    
    def _act(self, reasoning: str) -> str:
        """Exécute l'action décidée"""
        return self.left.think(
            "Tu exécutes cette action.",
            reasoning,
            temperature=0.5
        )
    
    def _is_goal_achieved(self, result: str, goal: str) -> bool:
        """Vérifie si l'objectif est atteint"""
        return "SUCCÈS" in result.upper() or "GOAL ACHIEVED" in result.upper()


class ReflexionMode:
    """
    Mode Reflexion (Self-Improving Reasoning)
    
    Pattern: Generate → Critique → Store Insight → Retry with improvement
    
    Utilisé pour:
    - Raisonnement à long terme
    - Auto-correction
    - Construction de conscience de soi
    """
    
    def __init__(self, hemisphere_left, hemisphere_right):
        self.left = hemisphere_left
        self.right = hemisphere_right
        self.insights: List[str] = []
    
    def execute(self, goal: str, max_iterations: int = 5) -> Dict:
        """Exécute le mode Reflexion"""
        session = ThinkingSession(
            id=f"reflexion_{datetime.now().timestamp()}",
            mode=ThinkingMode.REFLEXION,
            goal=goal
        )
        
        current_iteration = 0
        best_result = None
        best_score = 0
        
        while current_iteration < max_iterations:
            # 1. Generate
            generation = self._generate(goal, self.insights)
            
            # 2. Critique
            critique = self._critique(generation)
            score = self._score_critique(critique)
            
            # 3. Store Insight
            insight = self._extract_insight(critique)
            if insight:
                self.insights.append(insight)
            
            # Record step
            step = ThinkingStep(
                step_number=current_iteration,
                mode="reflexion",
                action=generation,
                result=critique
            )
            session.steps.append(step)
            
            # Track best result
            if score > best_score:
                best_score = score
                best_result = generation
            
            # Check if good enough
            if score >= 0.8:
                session.status = "success"
                session.final_result = generation
                break
            
            current_iteration += 1
        
        if session.status == "pending":
            session.status = "max_iterations"
            session.final_result = best_result
        
        return {
            "mode": "reflexion",
            "session_id": session.id,
            "status": session.status,
            "iterations": len(session.steps),
            "insights": self.insights,
            "result": session.final_result
        }
    
    def _generate(self, goal: str, insights: List[str]) -> str:
        """Génère une solution"""
        insight_context = "\n".join(insights) if insights else "Aucun insight précédent"
        
        return self.left.think(
            f"Génère une solution pour: {goal}\n\nInsights précédents:\n{insight_context}",
            "Sois créatif mais intègre les leçons apprises.",
            temperature=0.7
        )
    
    def _critique(self, generation: str) -> str:
        """Critique la génération"""
        return self.right.think(
            "Critique cette solution. Identifie les forces et faiblesses.",
            generation,
            temperature=0.8
        )
    
    def _score_critique(self, critique: str) -> float:
        """Score basé sur la critique"""
        if "excellent" in critique.lower() or "parfait" in critique.lower():
            return 0.9
        elif "bon" in critique.lower() or "bien" in critique.lower():
            return 0.7
        elif "moyen" in critique.lower():
            return 0.5
        else:
            return 0.3
    
    def _extract_insight(self, critique: str) -> Optional[str]:
        """Extrait un insight de la critique"""
        if "leçon" in critique.lower() or "insight" in critique.lower():
            return critique[:200]
        return None


class PlanExecuteMode:
    """
    Mode Plan-Execute
    
    Pattern: Create global plan → Break into subtasks → Execute sequentially
    
    Utilisé pour:
    - Tâches à long terme
    - Objectifs multi-étapes
    - Exécution structurée
    """
    
    def __init__(self, hemisphere_left, hemisphere_right):
        self.left = hemisphere_left
        self.right = hemisphere_right
    
    def execute(self, goal: str) -> Dict:
        """Exécute le mode Plan-Execute"""
        session = ThinkingSession(
            id=f"plan_execute_{datetime.now().timestamp()}",
            mode=ThinkingMode.PLAN_EXECUTE,
            goal=goal
        )
        
        # 1. Create global plan
        plan = self._create_plan(goal)
        
        # 2. Break into subtasks
        subtasks = self._break_into_subtasks(plan)
        
        # 3. Execute sequentially
        results = []
        for i, subtask in enumerate(subtasks):
            result = self._execute_subtask(subtask)
            results.append(result)
            
            step = ThinkingStep(
                step_number=i,
                mode="plan_execute",
                action=subtask,
                result=result
            )
            session.steps.append(step)
        
        session.status = "success"
        session.final_result = "\n".join(results)
        
        return {
            "mode": "plan_execute",
            "session_id": session.id,
            "status": session.status,
            "subtasks": len(subtasks),
            "results": results,
            "result": session.final_result
        }
    
    def _create_plan(self, goal: str) -> str:
        """Crée un plan global"""
        return self.left.think(
            f"Crée un plan détaillé pour: {goal}",
            "Structure ton plan avec des étapes claires.",
            temperature=0.4
        )
    
    def _break_into_subtasks(self, plan: str) -> List[str]:
        """Découpe le plan en sous-tâches"""
        response = self.right.think(
            "Découpe ce plan en sous-tâches exécutables.",
            plan,
            temperature=0.6
        )
        
        # Simple parsing - extract numbered items
        lines = response.split("\n")
        subtasks = []
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                subtasks.append(line)
        
        return subtasks if subtasks else [plan]
    
    def _execute_subtask(self, subtask: str) -> str:
        """Exécute une sous-tâche"""
        return self.left.think(
            f"Exécute cette sous-tâche: {subtask}",
            "Donne le résultat de l'exécution.",
            temperature=0.5
        )


class CriticRefineMode:
    """
    Mode Critic-Refine
    
    Pattern: Produce → Critic → Approve or Refine
    
    Utilisé pour:
    - Assurance qualité
    - Processus de révision
    - Amélioration itérative
    """
    
    def __init__(self, hemisphere_left, hemisphere_right):
        self.left = hemisphere_left
        self.right = hemisphere_right
    
    def execute(self, goal: str, max_refinements: int = 3) -> Dict:
        """Exécute le mode Critic-Refine"""
        session = ThinkingSession(
            id=f"critic_refine_{datetime.now().timestamp()}",
            mode=ThinkingMode.CRITIC_REFINE,
            goal=goal
        )
        
        # 1. Produce initial output
        current_output = self._produce(goal)
        
        refinement_count = 0
        while refinement_count < max_refinements:
            # 2. Critic
            critique = self._critic(current_output)
            
            # 3. Check if approved
            if self._is_approved(critique):
                session.status = "success"
                session.final_result = current_output
                break
            
            # 4. Refine
            current_output = self._refine(current_output, critique)
            
            step = ThinkingStep(
                step_number=refinement_count,
                mode="critic_refine",
                action=current_output,
                result=critique
            )
            session.steps.append(step)
            
            refinement_count += 1
        
        if session.status == "pending":
            session.status = "max_refinements"
            session.final_result = current_output
        
        return {
            "mode": "critic_refine",
            "session_id": session.id,
            "status": session.status,
            "refinements": len(session.steps),
            "result": session.final_result
        }
    
    def _produce(self, goal: str) -> str:
        """Produit une sortie initiale"""
        return self.left.think(
            f"Produis une sortie pour: {goal}",
            "Sois complet et précis.",
            temperature=0.5
        )
    
    def _critic(self, output: str) -> str:
        """Critique la sortie"""
        return self.right.think(
            "Critique cette sortie. Approuve ou demande des améliorations.",
            output,
            temperature=0.7
        )
    
    def _is_approved(self, critique: str) -> bool:
        """Vérifie si la sortie est approuvée"""
        return "approuvé" in critique.lower() or "approved" in critique.lower() or "excellent" in critique.lower()
    
    def _refine(self, output: str, critique: str) -> str:
        """Raffine la sortie basé sur la critique"""
        return self.left.think(
            f"Raffine cette sortie basé sur la critique:\n\nSortie:\n{output}\n\nCritique:\n{critique}",
            "Améliore la sortie en tenant compte de la critique.",
            temperature=0.6
        )


class ThinkingModeManager:
    """
    Gestionnaire des modes de pensée.
    Permet de sélectionner et exécuter différents modes.
    """
    
    def __init__(self, hemisphere_left, hemisphere_right):
        self.left = hemisphere_left
        self.right = hemisphere_right
        
        self.modes = {
            ThinkingMode.REACT: ReActMode(hemisphere_left, hemisphere_right),
            ThinkingMode.REFLEXION: ReflexionMode(hemisphere_left, hemisphere_right),
            ThinkingMode.PLAN_EXECUTE: PlanExecuteMode(hemisphere_left, hemisphere_right),
            ThinkingMode.TOT: None,  # Utilise notre ToTReasoner existant
            ThinkingMode.CRITIC_REFINE: CriticRefineMode(hemisphere_left, hemisphere_right),
        }
    
    def execute(self, mode: ThinkingMode, goal: str, **kwargs) -> Dict:
        """Exécute un mode de pensée"""
        if mode == ThinkingMode.TOT:
            # Utilise notre ToTReasoner existant
            from core.cognition.tot_reasoner import get_tot_reasoner
            tot = get_tot_reasoner()
            return tot.think(goal, **kwargs)
        
        mode_handler = self.modes.get(mode)
        if not mode_handler:
            return {"error": f"Mode {mode} non trouvé"}
        
        return mode_handler.execute(goal, **kwargs)
    
    def get_available_modes(self) -> List[Dict]:
        """Retourne les modes disponibles"""
        return [
            {"id": mode.value, "name": mode.value.replace("_", " ").title()}
            for mode in ThinkingMode
        ]


# Instance globale
_thinking_mode_manager: Optional[ThinkingModeManager] = None


def get_thinking_mode_manager(left_hemisphere=None, right_hemisphere=None) -> ThinkingModeManager:
    """Récupère le gestionnaire de modes de pensée"""
    global _thinking_mode_manager
    
    if _thinking_mode_manager is None:
        if left_hemisphere is None or right_hemisphere is None:
            from server.extensions import registry
            if registry.corps_calleux:
                left_hemisphere = registry.corps_calleux.left
                right_hemisphere = registry.corps_calleux.right
        
        if left_hemisphere and right_hemisphere:
            _thinking_mode_manager = ThinkingModeManager(left_hemisphere, right_hemisphere)
    
    return _thinking_mode_manager
