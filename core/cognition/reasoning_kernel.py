"""
Reasoning Kernel - MCTS (Monte Carlo Tree Search)
Monte Carlo Tree Search pour le raisonnement complexe.
Permet une recherche arborescente pour résoudre des problèmes.
"""

import math
import random
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MCTSNode:
    """Noeud dans l'arbre MCTS"""
    state: str
    parent: Optional['MCTSNode'] = None
    children: List['MCTSNode'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    action: str = ""
    is_terminal: bool = False
    
    def ucb1(self, exploration: float = 1.41) -> float:
        """Calculate UCB1 score for node selection"""
        if self.visits == 0:
            return float('inf')
        exploitation = self.value / self.visits
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration_term
    
    def best_child(self, exploration: float = 1.41) -> 'MCTSNode':
        """Select best child using UCB1"""
        return max(self.children, key=lambda c: c.ucb1(exploration))
    
    def expand(self, actions: List[str]) -> 'MCTSNode':
        """Expand node with new child"""
        action = random.choice(actions)
        child = MCTSNode(
            state=f"{self.state} -> {action}",
            parent=self,
            action=action
        )
        self.children.append(child)
        return child


class ReasoningKernel:
    """
    Noyau de raisonnement basé sur MCTS (Monte Carlo Tree Search).
    Utilise les hémisphères gauche et droit pour simuler et évaluer des branches.
    """

    def __init__(self, logic_hemi=None, intuition_hemi=None, pulse_provider=None):
        self.logic_hemi = logic_hemi
        self.intuition_hemi = intuition_hemi
        self.pulse_provider = pulse_provider
        self.is_initialized = False
        self.iterations = 1000  # Default MCTS iterations
        self.exploration = 1.41  # UCB1 exploration constant
        
        # Statistics
        self.total_solves = 0
        self.total_nodes_explored = 0
        self.history: List[Dict] = []

    def initialize(self, logic_hemi=None, intuition_hemi=None):
        """Initialize with hemisphere references"""
        if logic_hemi:
            self.logic_hemi = logic_hemi
        if intuition_hemi:
            self.intuition_hemi = intuition_hemi
        
        self.is_initialized = True
        logging.info("[ReasoningKernel] Initialized with MCTS")

    def solve(self, problem: str, max_depth: int = 5, iterations: int = None) -> Dict[str, Any]:
        """
        Résout un problème via MCTS.
        
        Args:
            problem: Le problème à résoudre
            max_depth: Profondeur maximale de l'arbre
            iterations: Nombre d'itérations MCTS
            
        Returns:
            Dict avec la solution et les statistiques
        """
        if iterations is None:
            iterations = self.iterations
        
        start_time = datetime.now()
        
        # Create root node
        root = MCTSNode(state=problem)
        
        # Generate possible actions using hemispheres
        actions = self._generate_actions(problem)
        
        if not actions:
            return {
                "solution": "Aucune action possible générée",
                "confidence": 0.0,
                "nodes_explored": 0,
                "time_ms": 0
            }
        
        nodes_explored = 0
        
        # MCTS iterations
        for i in range(iterations):
            node = root
            
            # Selection
            while node.children and not node.is_terminal:
                node = node.best_child(self.exploration)
            
            # Expansion
            if not node.is_terminal and node.visits > 0:
                node = node.expand(actions)
            
            # Simulation
            value = self._simulate(node.state, actions, max_depth)
            
            # Backpropagation
            while node:
                node.visits += 1
                node.value += value
                node = node.parent
                nodes_explored += 1
        
        # Select best action
        best_child = root.best_child(exploration=0)  # Pure exploitation
        
        # Calculate confidence
        confidence = best_child.value / best_child.visits if best_child.visits > 0 else 0
        
        elapsed = (datetime.now() - start_time).total_seconds() * 1000
        
        result = {
            "solution": best_child.action,
            "confidence": confidence,
            "nodes_explored": nodes_explored,
            "time_ms": elapsed,
            "tree_depth": len(root.children),
            "best_path": self._get_best_path(root)
        }
        
        # Update statistics
        self.total_solves += 1
        self.total_nodes_explored += nodes_explored
        self.history.append(result)
        
        return result

    def _generate_actions(self, problem: str) -> List[str]:
        """Generate possible actions using hemispheres"""
        actions = []
        
        # Use logic hemisphere for structured analysis
        if self.logic_hemi and self.logic_hemi.is_loaded:
            try:
                prompt = f"Analyze this problem and propose 3 possible actions (one per line):\n{problem[:500]}"
                response = self.logic_hemi.think(
                    "You are a logical analyst. Propose concrete actions.",
                    prompt
                )
                # Parse actions from response
                for line in response.split('\n'):
                    line = line.strip()
                    if line and len(line) > 5:
                        actions.append(line)
            except Exception as e:
                logging.warning(f"[ReasoningKernel] Logic hemisphere error: {e}")
        
        # Use intuition hemisphere for creative alternatives
        if self.intuition_hemi and self.intuition_hemi.is_loaded:
            try:
                prompt = f"Intuition on the problem: {problem[:500]}. Propose 2 creative alternatives (one per line)."
                response = self.intuition_hemi.think(
                    "You are intuitive and creative. Propose unexpected alternatives.",
                    prompt
                )
                for line in response.split('\n'):
                    line = line.strip()
                    if line and len(line) > 5:
                        actions.append(line)
            except Exception as e:
                logging.warning(f"[ReasoningKernel] Intuition hemisphere error: {e}")
        
        # Fallback: generate generic actions
        if not actions:
            actions = [
                "Analyser le problème en détail",
                "Chercher des solutions existantes",
                "Diviser le problème en sous-problèmes",
                "Consulter la documentation",
                "Expérimenter avec différentes approches"
            ]
        
        return actions[:10]  # Limit to 10 actions

    def _simulate(self, state: str, actions: List[str], max_depth: int) -> float:
        """Simulate a random playout from the given state"""
        value = 0.0
        depth = 0
        
        while depth < max_depth:
            # Random action selection
            if not actions:
                break
            
            action = random.choice(actions)
            
            # Evaluate action using intuition
            if self.intuition_hemi and self.intuition_hemi.is_loaded:
                try:
                    prompt = f"Évalue cette action pour '{state}': {action}\nRéponds avec un score de 0 à 100."
                    response = self.intuition_hemi.think(
                        "Évalue brièvement cette action (juste un score).",
                        prompt
                    )
                    # Extract score from response
                    import re
                    score_match = re.search(r'(\d+)', response)
                    if score_match:
                        value += int(score_match.group(1)) / 100
                except:
                    value += random.random() * 0.5
            else:
                value += random.random() * 0.5
            
            depth += 1
        
        return value / max_depth if max_depth > 0 else 0

    def _get_best_path(self, root: MCTSNode) -> List[str]:
        """Get the best path through the tree"""
        path = []
        node = root
        
        while node.children:
            node = node.best_child(exploration=0)
            if node.action:
                path.append(node.action)
        
        return path

    def get_stats(self) -> Dict:
        """Retourne les statistiques du kernel"""
        return {
            "initialized": self.is_initialized,
            "logic_hemi_available": self.logic_hemi is not None,
            "logic_hemi_loaded": self.logic_hemi.is_loaded if self.logic_hemi else False,
            "intuition_hemi_available": self.intuition_hemi is not None,
            "intuition_hemi_loaded": self.intuition_hemi.is_loaded if self.intuition_hemi else False,
            "total_solves": self.total_solves,
            "total_nodes_explored": self.total_nodes_explored,
            "iterations": self.iterations,
            "exploration": self.exploration
        }

    def configure(self, iterations: int = None, exploration: float = None):
        """Configure MCTS parameters"""
        if iterations is not None:
            self.iterations = iterations
        if exploration is not None:
            self.exploration = exploration


# Global instance
_reasoning_kernel = None


def get_reasoning_kernel(
    logic_hemi=None, intuition_hemi=None, pulse_provider=None
) -> Optional[ReasoningKernel]:
    """Retourne l'instance globale du ReasoningKernel"""
    global _reasoning_kernel
    if _reasoning_kernel is None:
        _reasoning_kernel = ReasoningKernel(
            logic_hemi=logic_hemi,
            intuition_hemi=intuition_hemi,
            pulse_provider=pulse_provider
        )
    return _reasoning_kernel
