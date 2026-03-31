"""
Tree of Thoughts Reasoner
=========================
Implementation du raisonnement par arbres de pensées (ToT).
Inspiré de Yao et al., NeurIPS 2023.

Désactivé par défaut - activable via toggle.
"""

import uuid
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger("cognition.tot")


class ToTStrategy(Enum):
    BFS = "breadth_first"
    DFS = "depth_first"
    BEST_FIRST = "best_first"
    MONTE_CARLO = "monte_carlo"


class NodeStatus(Enum):
    PENDING = "pending"
    GENERATING = "generating"
    EVALUATED = "evaluated"
    EXPANDED = "expanded"
    PRUNED = "pruned"
    COMPLETE = "complete"


@dataclass
class ThoughtNode:
    id: str
    content: str
    parent: Optional['ThoughtNode'] = None
    children: List['ThoughtNode'] = field(default_factory=list)
    score: float = 0.0
    depth: int = 0
    status: NodeStatus = NodeStatus.PENDING
    evaluation: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


class ToTReasoner:
    """
    Tree of Thoughts - Structured reasoning with tree exploration.
    
    Disabled by default (enabled=False).
    Enable via enable() before use.
    
    Uses Corps Calleux (left/right hemispheres) for:
    - Generation: Both hemispheres (synthesis)
    - Evaluation: Both hemispheres (average score)
    """

    def __init__(
        self,
        strategy: ToTStrategy = ToTStrategy.BFS,
        max_depth: int = 5,
        max_branches: int = 5,
        evaluation_threshold: float = 0.5,
        max_iterations: int = 10
    ):
        self.strategy = strategy
        self.max_depth = max_depth
        self.max_branches = max_branches
        self.evaluation_threshold = evaluation_threshold
        self.max_iterations = max_iterations
        
        self.enabled = False
        self.root: Optional[ThoughtNode] = None
        self.best_node: Optional[ThoughtNode] = None
        self.all_nodes: List[ThoughtNode] = []
        
        self._llm_generate: Optional[Callable] = None
        self._llm_evaluate: Optional[Callable] = None
        
        self._corps_calleux = None
        self._left = None
        self._right = None

    def connect_corps_calleux(self, corps_calleux):
        """
        Connecte le ToT au Corps Calleux.
        
        Utilise TOUJOURS les deux hemisphères:
        - Pour générer: Les deux en parallèle, puis synthèse
        - Pour évaluer: Les deux, puis moyenne des scores
        - Résultat final: Synthèse bicamérale
        """
        self._corps_calleux = corps_calleux
        
        if corps_calleux:
            self._left = corps_calleux.left
            self._right = corps_calleux.right
            
            def generate_fn(prompt):
                if not self._left and not self._right:
                    return prompt
                
                results = {}
                
                if self._left:
                    results['left'] = self._left.think(
                        "You are the analytical (left) hemisphere. Generate logical and structured approaches.",
                        prompt,
                        temperature=0.5
                    )
                
                if self._right:
                    results['right'] = self._right.think(
                        "You are the intuitive (right) hemisphere. Generate creative and original approaches.",
                        prompt,
                        temperature=0.9
                    )
                
                if 'left' in results and 'right' in results:
                    return f"**Analysis (DIA):**\n{results['left']}\n\n---\n\n**Intuition (PAL):**\n{results['right']}"
                elif 'left' in results:
                    return results['left']
                elif 'right' in results:
                    return results['right']
                
                return prompt
            
            def evaluate_fn(prompt):
                if not self._left and not self._right:
                    return "0.5"
                
                scores = {}
                
                if self._left:
                    scores['left'] = self._left.think(
                        "Evaluate this approach critically. Give a score from 0 to 1 (decimal only).",
                        prompt,
                        temperature=0.2
                    )
                
                if self._right:
                    scores['right'] = self._right.think(
                        "Evaluate this approach intuitively. Give a score from 0 to 1 (decimal only).",
                        prompt,
                        temperature=0.4
                    )
                
                if scores:
                    try:
                        parsed = []
                        for s in scores.values():
                            import re
                            nums = re.findall(r'[0-9.]+', s)
                            if nums:
                                parsed.append(float(nums[0]))
                        if parsed:
                            avg = sum(parsed) / len(parsed)
                            return str(min(1.0, max(0.0, avg)))
                    except:
                        pass
                
                return "0.5"
            
            self.set_llm_generate(generate_fn)
            self.set_llm_evaluate(evaluate_fn)
            
            logger.info("[ToT] Connecté au Corps Calleux - TOUJOURS bipolaire")

    def set_llm_generate(self, fn: Callable):
        """Configure la fonction LLM pour génération"""
        self._llm_generate = fn

    def set_llm_evaluate(self, fn: Callable):
        """Configure la fonction LLM pour évaluation"""
        self._llm_evaluate = fn

    def enable(self):
        """Active le mode ToT"""
        self.enabled = True
        logger.info("[ToT] Enabled")

    def disable(self):
        """Désactive le mode ToT"""
        self.enabled = False
        logger.info("[ToT] Disabled")

    def is_enabled(self) -> bool:
        return self.enabled

    def is_connected(self) -> bool:
        """Vérifie si connecté au Corps Calleux"""
        return self._corps_calleux is not None

    def get_status(self) -> Dict:
        """Retourne le statut complet du ToT"""
        return {
            "enabled": self.enabled,
            "connected": self.is_connected(),
            "has_generator": self._llm_generate is not None,
            "has_evaluator": self._llm_evaluate is not None,
            "strategy": self.strategy.value,
            "max_depth": self.max_depth,
            "max_branches": self.max_branches,
            "hemispheres": {
                "left": self._left is not None,
                "right": self._right is not None
            }
        }

    async def think(
        self,
        prompt: str,
        context: Dict = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Raisonnement ToT principal.
        
        Returns:
            Dict avec:
            - solution: str
            - tree: List[Dict] - l'arbre de pensées
            - best_score: float
            - iterations: int
            - used_tot: bool
        """
        if not self.enabled or not self._llm_generate:
            return await self._direct_think(prompt, context, system_prompt)

        self._reset()
        iteration = 0

        try:
            self.root = ThoughtNode(
                id="root",
                content=prompt,
                depth=0,
                status=NodeStatus.PENDING
            )
            self.all_nodes.append(self.root)

            while iteration < self.max_iterations and not self._is_complete():
                logger.debug(f"[ToT] Iteration {iteration + 1}")

                pending = [n for n in self.all_nodes 
                          if n.status in (NodeStatus.PENDING, NodeStatus.EVALUATED)
                          and n.depth < self.max_depth]

                if not pending:
                    break

                await self._expand_nodes(pending)
                await self._evaluate_nodes()
                self._select_and_prune()

                iteration += 1

            return self._extract_result(iteration + 1)

        except Exception as e:
            logger.error(f"[ToT] Error: {e}")
            return await self._direct_think(prompt, context, system_prompt)

    async def _direct_think(
        self,
        prompt: str,
        context: Dict = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """Fallback: raisonnement direct sans ToT"""
        if not self._llm_generate:
            return {
                "solution": prompt,
                "tree": [],
                "best_score": 0.0,
                "iterations": 0,
                "used_tot": False,
                "error": "No LLM generator configured"
            }

        try:
            full_prompt = f"{system_prompt or ''}\n\n{prompt}".strip()
            result = await self._llm_generate(full_prompt)
            
            return {
                "solution": result,
                "tree": [],
                "best_score": 0.0,
                "iterations": 0,
                "used_tot": False
            }
        except Exception as e:
            return {
                "solution": prompt,
                "tree": [],
                "best_score": 0.0,
                "iterations": 0,
                "used_tot": False,
                "error": str(e)
            }

    async def _expand_nodes(self, nodes: List[ThoughtNode]):
        """Développe les noeuds sélectionnés"""
        for node in nodes[:self.max_branches]:
            if node.status == NodeStatus.EVALUATED:
                node.status = NodeStatus.EXPANDED

            if node.depth >= self.max_depth:
                node.status = NodeStatus.COMPLETE
                continue

            try:
                children_contents = await self._llm_generate(
                    f"Propose des continuations pour: {node.content}\n"
                    f"Profondeur: {node.depth + 1}/{self.max_depth}\n"
                    f"Nombre de propositions: {self.max_branches}"
                )

                children = self._parse_children(children_contents, node)
                
                for child in children:
                    node.children.append(child)
                    self.all_nodes.append(child)
                    child.status = NodeStatus.EVALUATED

                node.status = NodeStatus.EXPANDED

            except Exception as e:
                logger.warning(f"[ToT] Expand error: {e}")
                node.status = NodeStatus.PRUNED

    def _parse_children(self, content: str, parent: ThoughtNode) -> List[ThoughtNode]:
        """Parse le contenu généré en enfants"""
        lines = content.split('\n')
        children = []
        
        for line in lines[:self.max_branches]:
            line = line.strip()
            if not line:
                continue
            
            if line[0].isdigit() and ('.' in line or ')' in line):
                content = line.split('.', 1)[-1].split(')', 1)[-1].strip()
            elif line.startswith('-') or line.startswith('*'):
                content = line[1:].strip()
            else:
                content = line
            
            if len(content) > 10:
                children.append(ThoughtNode(
                    content=content,
                    parent=parent,
                    depth=parent.depth + 1
                ))
        
        return children[:self.max_branches]

    async def _evaluate_nodes(self):
        """Évalue chaque noeud avec le LLM"""
        if not self._llm_evaluate:
            for node in self.all_nodes:
                if node.status == NodeStatus.EXPANDED:
                    node.score = 0.5
            return

        evaluable = [n for n in self.all_nodes 
                     if n.status == NodeStatus.EXPANDED]

        for node in evaluable:
            try:
                eval_prompt = (
                    f"Évalue cette approche de 0 à 1:\n"
                    f"{node.content}\n"
                    f"Donne uniquement un nombre décimal."
                )
                
                result = await self._llm_evaluate(eval_prompt)
                
                try:
                    score = float(result.strip().split()[-1].replace(',', '.'))
                    node.score = max(0.0, min(1.0, score))
                except:
                    node.score = 0.5
                
                node.status = NodeStatus.EVALUATED

            except Exception as e:
                logger.warning(f"[ToT] Evaluate error: {e}")
                node.score = 0.5

    def _select_and_prune(self):
        """Sélectionne les meilleurs noeuds et élague les autres"""
        if self.strategy == ToTStrategy.BFS:
            self._select_bfs()
        elif self.strategy == ToTStrategy.DFS:
            self._select_dfs()
        elif self.strategy == ToTStrategy.BEST_FIRST:
            self._select_best_first()
        else:
            self._select_bfs()

    def _select_bfs(self):
        """Breadth-First: garde les meilleurs par niveau"""
        for depth in range(self.max_depth + 1):
            level_nodes = [n for n in self.all_nodes if n.depth == depth 
                          and n.status == NodeStatus.EVALUATED]
            
            if not level_nodes:
                continue
            
            level_nodes.sort(key=lambda x: x.score, reverse=True)
            
            for node in level_nodes[self.max_branches:]:
                node.status = NodeStatus.PRUNED

    def _select_dfs(self):
        """Depth-First: suit le meilleur chemin"""
        if not self.root:
            return
        
        current = self.root
        while current.children and current.depth < self.max_depth:
            if not current.children:
                break
            
            best = max(current.children, key=lambda x: x.score)
            
            for child in current.children:
                if child != best and child.status != NodeStatus.COMPLETE:
                    child.status = NodeStatus.PRUNED
            
            current = best
        
        current.status = NodeStatus.COMPLETE

    def _select_best_first(self):
        """Best-First: всегда выбирает лучший узел"""
        all_evaluated = [n for n in self.all_nodes 
                        if n.status == NodeStatus.EVALUATED]
        
        if not all_evaluated:
            return
        
        all_evaluated.sort(key=lambda x: x.score, reverse=True)
        
        best = all_evaluated[0]
        
        for node in all_evaluated[self.max_branches:]:
            node.status = NodeStatus.PRUNED
        
        best.status = NodeStatus.COMPLETE

    def _is_complete(self) -> bool:
        """Vérifie si solution trouvée"""
        complete = [n for n in self.all_nodes 
                   if n.status == NodeStatus.COMPLETE]
        
        if complete and any(n.score >= 0.9 for n in complete):
            return True
        
        if all(n.status == NodeStatus.PRUNED or n.depth >= self.max_depth 
               for n in self.all_nodes):
            return True
        
        return False

    def _extract_result(self, iterations: int) -> Dict[str, Any]:
        """Extrait la meilleure solution et produit une SYNTHÈSE BICAMÉRALE"""
        evaluated = [n for n in self.all_nodes 
                    if n.status in (NodeStatus.EVALUATED, NodeStatus.COMPLETE)]
        
        if not evaluated:
            return {
                "solution": self.root.content if self.root else "",
                "synthesis": self.root.content if self.root else "",
                "tree": [],
                "best_score": 0.0,
                "iterations": iterations,
                "used_tot": True
            }
        
        best = max(evaluated, key=lambda x: x.score)
        self.best_node = best
        
        best_thought = best.content
        alternative_thoughts = [n.content for n in evaluated[:3] if n != best]
        
        final_synthesis = best_thought
        
        if self._left and self._right:
            synthesis_prompt = f"""BICAMERAL SYNTHESIS - Combine both perspectives:

Best approach found:
{best_thought}

Other approaches explored:
{chr(10).join('- ' + t for t in alternative_thoughts)}

Produce a final synthesis that:
1. Uses logical analysis (left hemisphere)
2. Integrates creative intuition (right hemisphere)
3. Gives a unified and complete conclusion

Reply with the final synthesis only."""
            
            left_result = self._left.think(
                "You are the analytical hemisphere. Synthesize approaches logically.",
                synthesis_prompt,
                temperature=0.5
            )
            
            right_result = self._right.think(
                "You are the intuitive hemisphere. Synthesize approaches creatively.",
                synthesis_prompt,
                temperature=0.8
            )
            
            final_synthesis = f"**Analysis (DIA):**\n{left_result}\n\n**Intuition (PAL):**\n{right_result}\n\n---\n\n**FINAL SYNTHESIS:**\n{left_result[:200]}... and {right_result[:200]}..."
        
        elif self._left:
            final_synthesis = self._left.think(
                "Synthesize this approach analytically.",
                best_thought,
                temperature=0.5
            )
        elif self._right:
            final_synthesis = self._right.think(
                "Synthesize this approach intuitively.",
                best_thought,
                temperature=0.7
            )
        
        return {
            "solution": best.content,
            "synthesis": final_synthesis,
            "best_score": best.score,
            "iterations": iterations,
            "used_tot": True,
            "tree": self._serialize_tree(),
            "path": self._get_path(best),
            "bicameral": True
        }

    def _serialize_tree(self) -> List[Dict]:
        """Sérialise l'arbre pour affichage"""
        result = []
        
        for node in self.all_nodes:
            if node.parent is None:
                parent_id = None
            else:
                parent_id = node.parent.id
            
            result.append({
                "id": node.id,
                "content": node.content[:100] + "..." if len(node.content) > 100 else node.content,
                "score": node.score,
                "depth": node.depth,
                "status": node.status.value,
                "parent_id": parent_id
            })
        
        return result

    def _get_path(self, node: ThoughtNode) -> List[str]:
        """Retourne le chemin depuis la racine"""
        path = []
        current = node
        
        while current:
            path.insert(0, current.content[:50])
            current = current.parent
        
        return path

    def _reset(self):
        """Reset l'état du reasoner"""
        self.root = None
        self.best_node = None
        self.all_nodes = []

    def get_tree_visualization(self) -> str:
        """Génère une représentation textuelle de l'arbre"""
        if not self.root:
            return "(empty)"
        
        lines = []
        
        def render(node: ThoughtNode, prefix: str = "", is_last: bool = True):
            score_str = f"[{node.score:.2f}]" if node.score else "[--]"
            status_icon = {
                NodeStatus.PENDING: "○",
                NodeStatus.EVALUATED: "◐",
                NodeStatus.EXPANDED: "◉",
                NodeStatus.PRUNED: "✗",
                NodeStatus.COMPLETE: "✓"
            }.get(node.status, "•")
            
            content = node.content[:60] + "..." if len(node.content) > 60 else node.content
            lines.append(f"{prefix}{status_icon} {score_str} {content}")
            
            children = node.children
            for i, child in enumerate(children):
                ext = "└── " if i == len(children) - 1 else "├── "
                render(child, prefix + ext, i == len(children) - 1)
        
        render(self.root)
        return "\n".join(lines)


_global_tot_reasoner: Optional[ToTReasoner] = None


def get_tot_reasoner() -> ToTReasoner:
    """Retourne l'instance globale du ToT reasoner"""
    global _global_tot_reasoner
    if _global_tot_reasoner is None:
        _global_tot_reasoner = ToTReasoner()
    return _global_tot_reasoner


def create_tot_reasoner(
    strategy: ToTStrategy = ToTStrategy.BFS,
    max_depth: int = 5,
    max_branches: int = 5
) -> ToTReasoner:
    """Crée une nouvelle instance de ToT reasoner"""
    return ToTReasoner(
        strategy=strategy,
        max_depth=max_depth,
        max_branches=max_branches
    )
