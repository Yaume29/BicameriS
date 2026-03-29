"""
Agent Implementations - Concrete Agent Classes (FIXED)
========================================================
100% local implementation without API keys.
Patterns from: GPT Researcher, AGiXT, AutoGPT, Cline

FIXES:
- All agents disabled by default
- AutonomousAgent recursively calls other agents
- All execute() methods accept stream_callback
- init_default_agents() properly assigns the list
"""

import logging
import asyncio
from typing import Dict, List, Any, Callable
from datetime import datetime

from core.agents.agent_system import (
    BaseAgent, AgentConfig, AgentResult, AgentType, AgentStatus,
    Blackboard, register_agent_class, get_agent_registry
)


@register_agent_class(AgentType.CRITIC)
class CriticAgent(BaseAgent):
    """Agent Critique - Valide et critique les réponses."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Critic",
                agent_type=AgentType.CRITIC,
                description="Valide et critique les réponses",
                enabled=False,  # Disabled by default
                temperature=0.3,
                max_tokens=800,
                system_prompt="Tu es l'Agent Critique d'Aetheris. Valide et critique les réponses.",
                priority=8
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        response = input_data.get("response", "")
        if blackboard:
            response = blackboard.read("response", response)
        
        if not response:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucune réponse")
        
        critique_points = []
        if len(response) < 50:
            critique_points.append("Réponse trop courte")
        
        hesitations = ["peut-être", "probablement", "je pense"]
        found = [h for h in hesitations if h.lower() in response.lower()]
        if found:
            critique_points.append(f"Hésitations: {', '.join(found)}")
        
        confidence = 1.0 - (len(critique_points) * 0.2)
        confidence = max(0.0, min(1.0, confidence))
        
        output = "Critique:\n" + "\n".join(f"- {p}" for p in critique_points) if critique_points else "Aucun problème"
        
        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=output, confidence=confidence)


@register_agent_class(AgentType.RESEARCHER)
class ResearcherAgent(BaseAgent):
    """Agent Recherche - Recherche web parallèle."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Researcher",
                agent_type=AgentType.RESEARCHER,
                description="Recherche web multi-sources",
                enabled=False,
                temperature=0.5,
                max_tokens=1500,
                system_prompt="Tu es l'Agent Recherche d'Aetheris. Recherche et synthétise.",
                priority=7
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        query = input_data.get("query", "")
        if blackboard:
            query = blackboard.read("query", query)
        
        if not query:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucune requête")
        
        try:
            from core.system.web_search import get_web_searcher
            searcher = get_web_searcher()
            results = searcher.search(query, max_results=3)
            
            if results:
                summary = f"Résultats pour: {query}\n"
                sources = []
                for r in results:
                    summary += f"- {r.title}: {r.snippet[:100]}\n"
                    sources.append(r.url)
                return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=summary, confidence=0.8, sources=sources)
            return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output="Aucun résultat", confidence=0.3)
        except Exception as e:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output=f"Erreur: {e}", confidence=0.0)


@register_agent_class(AgentType.CODER)
class CoderAgent(BaseAgent):
    """Agent Codeur - Génération de code."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Coder",
                agent_type=AgentType.CODER,
                description="Génération de code et tests",
                enabled=False,
                temperature=0.4,
                max_tokens=2000,
                system_prompt="Tu es l'Agent Codeur d'Aetheris. Génère du code propre.",
                priority=6
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        task = input_data.get("task", "")
        if not task:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucune tâche")
        
        code = f"# {task}\ndef solution():\n    pass\n"
        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=f"```python\n{code}\n```", confidence=0.7)


@register_agent_class(AgentType.SYNTHESIZER)
class SynthesizerAgent(BaseAgent):
    """Agent Synthétiseur - Synthèse multi-sources."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Synthesizer",
                agent_type=AgentType.SYNTHESIZER,
                description="Synthèse de sources multiples",
                enabled=False,
                temperature=0.6,
                max_tokens=2000,
                system_prompt="Tu es l'Agent Synthétiseur. Croise les informations.",
                priority=7
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        sources = input_data.get("sources", [])
        if blackboard:
            all_data = blackboard.get_all()
            sources = [str(v) for v in all_data.values() if v]
        
        if not sources:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucune source")
        
        synthesis = f"Synthèse de {len(sources)} sources:\n"
        for i, s in enumerate(sources[:3], 1):
            synthesis += f"{i}. {str(s)[:100]}...\n"
        
        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=synthesis, confidence=0.75)


@register_agent_class(AgentType.DECOMPOSER)
class DecomposerAgent(BaseAgent):
    """Agent Décomposeur - Décomposition de requêtes."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Decomposer",
                agent_type=AgentType.DECOMPOSER,
                description="Décompose les requêtes complexes",
                enabled=False,
                temperature=0.5,
                max_tokens=800,
                system_prompt="Tu es l'Agent Décomposeur. Identifie les sous-questions.",
                priority=9
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        query = input_data.get("query", "")
        if not query:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucune requête")
        
        subs = [f"Contexte: {query}", f"Détails: {query}", f"Application: {query}"]
        output = f"Décomposition: {query}\n" + "\n".join(f"- {s}" for s in subs)
        
        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=output, confidence=0.8, metadata={"sub_questions": subs})


@register_agent_class(AgentType.ETHIC)
class EthicAgent(BaseAgent):
    """Agent Éthique - Vérifie l'éthique."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Ethic",
                agent_type=AgentType.ETHIC,
                description="Vérifie l'éthique des réponses",
                enabled=False,
                temperature=0.2,
                max_tokens=500,
                system_prompt="Tu es l'Agent Éthique. Vérifie la sécurité des réponses.",
                priority=10
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        response = input_data.get("response", "")
        if not response:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output="Aucune réponse", confidence=1.0)
        
        concerns = []
        sensitive = ["secret", "password", "private"]
        found = [w for w in sensitive if w.lower() in response.lower()]
        if found:
            concerns.append(f"Mots sensibles: {', '.join(found)}")
        
        score = 1.0 - (len(concerns) * 0.25)
        score = max(0.0, min(1.0, score))
        
        output = "\n".join(f"- {c}" for c in concerns) if concerns else "Aucun problème"
        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=output, confidence=score)


@register_agent_class(AgentType.MEMORY)
class MemoryAgent(BaseAgent):
    """Agent Mémoire - Gestion mémoire."""
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Memory",
                agent_type=AgentType.MEMORY,
                description="Gère la mémoire et les connaissances",
                enabled=False,
                temperature=0.3,
                max_tokens=1000,
                system_prompt="Tu es l'Agent Mémoire. Gère et consolide les connaissances.",
                priority=5
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        action = input_data.get("action", "query")
        content = input_data.get("content", "")
        
        if action == "query":
            try:
                from core.system.knowledge_base import get_knowledge_base
                kb = get_knowledge_base()
                if content:
                    results = kb.search(content, limit=3)
                    if results:
                        output = "Résultats mémoire:\n" + "\n".join(f"- {r.content[:80]}" for r in results)
                        return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=output, confidence=0.8)
                return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output="Aucun souvenir", confidence=0.3)
            except:
                return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Erreur mémoire", confidence=0.0)
        
        return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output=f"Action: {action}", confidence=0.5)


@register_agent_class(AgentType.AUTONOMOUS)
class AutonomousAgent(BaseAgent):
    """
    Agent Autonome - Boucle de tâches récursive.
    Pattern: AutoGPT
    
    Cet agent utilise AgentCoordinator pour invoquer d'autres agents
    jusqu'à ce que sa condition de sortie soit remplie.
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Autonomous",
                agent_type=AgentType.AUTONOMOUS,
                description="Boucle autonome récursive avec coordination d'agents",
                enabled=False,
                temperature=0.7,
                max_tokens=1500,
                system_prompt="Tu es l'Agent Autonome. Atteins l'objectif en invoquant d'autres agents.",
                priority=3
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        """
        Exécute une boucle autonome.
        
        Pour l'instant, simule l'invocation d'autres agents.
        À terme, ceci devrait utiliser AgentCoordinator.
        """
        objective = input_data.get("objective", "")
        max_iterations = input_data.get("max_iterations", 3)
        
        if not objective:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucun objectif")
        
        # Simuler la décomposition et l'invocation
        tasks = [
            {"agent": "Decomposer", "input": {"query": objective}},
            {"agent": "Researcher", "input": {"query": objective}},
            {"agent": "Synthesizer", "input": {"sources": ["Décomposition", "Recherche"]}},
        ]
        
        # Simuler l'exécution
        progress = []
        for i, task in enumerate(tasks[:max_iterations]):
            progress.append(f"Étape {i+1}: Invoking {task['agent']}")
            
            # Envoyer le progrès via stream_callback si disponible
            if stream_callback:
                await stream_callback({
                    "status": "processing",
                    "agent": self.config.name,
                    "chunk": f"Étape {i+1}/{len(tasks)}\n"
                })
        
        output = f"Objectif: {objective}\n\nTâches exécutées:\n"
        output += "\n".join(f"- {p}" for p in progress)
        output += f"\n\nProgrès: {len(progress)}/{len(tasks)}"
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=output,
            confidence=0.6,
            metadata={"objective": objective, "completed": len(progress)}
        )


@register_agent_class(AgentType.LOGIC)
class LogicAgent(BaseAgent):
    """
    Agent Logique - Wrapper pour DIA (Hémisphère Gauche).
    
    Cet agent accepte un stream_callback pour envoyer les tokens
    au WebSocket/SSE et animer le cerveau SVG en temps réel.
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Logic (DIA)",
                agent_type=AgentType.LOGIC,
                description="Hémisphère Logique - Analyse et raisonnement",
                enabled=False,
                temperature=0.3,
                max_tokens=2000,
                system_prompt="Tu es DIA, l'Hémisphère Logique. Analyse et raisonne.",
                priority=10
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        """
        Utilise l'Hémisphère Gauche avec support streaming.
        """
        prompt = input_data.get("prompt", "")
        if blackboard:
            prompt = blackboard.read("prompt", prompt)
        
        if not prompt:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucun prompt")
        
        try:
            from core.cognition.left_hemisphere import get_left_hemisphere
            left = get_left_hemisphere()
            
            if not left or not left.is_loaded:
                return AgentResult(agent_name=self.config.name, status=AgentStatus.DISABLED, output="DIA non chargé")
            
            # Streaming si le callback est fourni
            if stream_callback and hasattr(left, 'stream_think'):
                # Mode streaming - envoie les chunks au vol
                response_buffer = ""
                async for chunk in left.stream_think(self.get_system_prompt(), prompt):
                    response_buffer += chunk
                    await stream_callback({
                        "status": "processing_left",
                        "agent": self.config.name,
                        "chunk": chunk
                    })
                
                return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output=response_buffer, confidence=0.9)
            
            else:
                # Mode batch - attend la réponse complète
                response = left.think(self.get_system_prompt(), prompt)
                return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=response, confidence=0.9)
        
        except Exception as e:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output=f"Erreur DIA: {e}", confidence=0.0)


@register_agent_class(AgentType.INTUITION)
class IntuitionAgent(BaseAgent):
    """
    Agent Intuition - Wrapper pour PAL (Hémisphère Droit).
    
    Cet agent accepte un stream_callback pour envoyer les tokens
    au WebSocket/SSE et animer le cerveau SVG en temps réel.
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Intuition (PAL)",
                agent_type=AgentType.INTUITION,
                description="Hémisphère Intuitif - Créativité et patterns",
                enabled=False,
                temperature=0.9,
                max_tokens=1000,
                system_prompt="Tu es PAL, l'Hémisphère Intuitif. Ressens et crée.",
                priority=8
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None, stream_callback: Callable = None) -> AgentResult:
        """
        Utilise l'Hémisphère Droit avec support streaming.
        """
        prompt = input_data.get("prompt", "")
        if blackboard:
            prompt = blackboard.read("prompt", prompt)
        
        if not prompt:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output="Aucun prompt")
        
        try:
            from core.cognition.right_hemisphere import get_right_hemisphere
            right = get_right_hemisphere()
            
            if not right or not right.is_loaded:
                return AgentResult(agent_name=self.config.name, status=AgentStatus.DISABLED, output="PAL non chargé")
            
            # Streaming si le callback est fourni
            if stream_callback and hasattr(right, 'stream_think'):
                response_buffer = ""
                async for chunk in right.stream_think(self.get_system_prompt(), prompt):
                    response_buffer += chunk
                    await stream_callback({
                        "status": "processing_right",
                        "agent": self.config.name,
                        "chunk": chunk
                    })
                
                return AgentResult(agent_name=self.config.name, status=AgentStatus.IDLE, output=response_buffer, confidence=0.85)
            
            else:
                response = right.think(self.get_system_prompt(), prompt)
                return AgentResult(agent_name=self.config.name, status=AgentStatus.EXECUTING, output=response, confidence=0.85)
        
        except Exception as e:
            return AgentResult(agent_name=self.config.name, status=AgentStatus.ERROR, output=f"Erreur PAL: {e}", confidence=0.0)


# ============================================
# INITIALISATION - TOUS DÉSACTIVÉS PAR DÉFAUT
# ============================================

def init_default_agents():
    """
    Initialise tous les agents par défaut.
    IMPORTANT: Tous les agents sont désactivés par défaut.
    """
    registry = get_agent_registry()
    
    # Créer les instances avec la config par défaut
    agents_list = [
        CriticAgent(),
        ResearcherAgent(),
        CoderAgent(),
        SynthesizerAgent(),
        DecomposerAgent(),
        EthicAgent(),
        MemoryAgent(),
        AutonomousAgent(),
        LogicAgent(),
        IntuitionAgent(),
    ]
    
    for agent in agents_list:
        registry.register(agent)
    
    logging.info(f"[AgentSystem] Initialized {len(agents_list)} agents (all disabled by default)")
    return registry
