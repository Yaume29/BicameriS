"""
Agent Implementations - Concrete Agent Classes (FIXED)
========================================================
100% local implementation without API keys.
Patterns from: GPT Researcher, AGiXT, AutoGPT, Cline

FIX: Each agent class is decorated with @register_agent_class
     to enable Factory Pattern reconstruction.
"""

import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime

from core.agents.agent_system import (
    BaseAgent, AgentConfig, AgentResult, AgentType, AgentStatus,
    Blackboard, register_agent_class, get_agent_registry
)


@register_agent_class(AgentType.CRITIC)
class CriticAgent(BaseAgent):
    """
    Agent Critique - Valide et critique les réponses.
    Pattern: AGiXT Critic
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Critic",
                agent_type=AgentType.CRITIC,
                description="Valide et critique les réponses pour améliorer la qualité",
                enabled=True,
                temperature=0.3,
                max_tokens=800,
                system_prompt="""Tu es l'Agent Critique d'Aetheris.
Ton rôle est de valider et critiquer les réponses.
- Détecte les erreurs factuelles
- Identifie les incohérences
- Suggère des améliorations
- Vérifie la logique
Sois constructif mais rigoureux.""",
                priority=8
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Critique une réponse"""
        # FIX 3: Lire depuis le blackboard si disponible
        response = input_data.get("response", "")
        if blackboard:
            response = blackboard.read("response", response)
            # Lire aussi la sortie d'autres agents
            for agent_name in ["Critic", "Decomposer", "Synthesizer"]:
                agent_output = blackboard.read_agent_output(agent_name)
                if agent_output and agent_name != self.config.name:
                    response = f"{response}\n\n[Agent {agent_name}]: {agent_output}"
        
        question = input_data.get("question", "")
        
        if not response:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucune réponse à critiquer",
                confidence=0.0
            )
        
        # Analyse basique de la réponse
        critique_points = []
        
        if len(response) < 50:
            critique_points.append("Réponse trop courte - manque de détails")
        
        hesitations = ["peut-être", "probablement", "je pense", "je crois"]
        found_hesitations = [h for h in hesitations if h.lower() in response.lower()]
        if found_hesitations:
            critique_points.append(f"Langage hésitant détecté: {', '.join(found_hesitations)}")
        
        words = response.split()
        if len(words) != len(set(words)):
            critique_points.append("Mots répétés détectés")
        
        confidence = 1.0 - (len(critique_points) * 0.2)
        confidence = max(0.0, min(1.0, confidence))
        
        critique_text = "\n".join([f"- {point}" for point in critique_points]) if critique_points else "Aucun problème détecté"
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=f"**Analyse critique:**\n{critique_text}",
            confidence=confidence,
            metadata={"critique_points": critique_points}
        )


@register_agent_class(AgentType.RESEARCHER)
class ResearcherAgent(BaseAgent):
    """
    Agent de Recherche - Recherche web parallèle.
    Pattern: GPT Researcher
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Researcher",
                agent_type=AgentType.RESEARCHER,
                description="Recherche web parallèle multi-sources",
                enabled=True,
                temperature=0.5,
                max_tokens=1500,
                system_prompt="""Tu es l'Agent de Recherche d'Aetheris.
Ton rôle est de rechercher des informations.
- Synthétise les résultats de recherche
- Identifie les sources fiables
- Extrait les informations pertinentes
Sois factuel et précis.""",
                priority=7
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Exécute une recherche"""
        # FIX 3: Lire la requête depuis le blackboard si disponible
        query = input_data.get("query", "")
        if blackboard:
            query = blackboard.read("query", query)
            # Vérifier si un décomposeur a déjà fourni des sous-questions
            decomposer_output = blackboard.read_agent_output("Decomposer")
            if decomposer_output:
                query = f"{query}\n\nSous-questions: {decomposer_output}"
        
        if not query:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucune requête de recherche"
            )
        
        try:
            from core.system.web_search import get_web_searcher
            searcher = get_web_searcher()
            
            results = searcher.search(query, max_results=5)
            
            if results:
                summary = f"**Résultats de recherche pour:** {query}\n\n"
                sources = []
                for i, r in enumerate(results[:5], 1):
                    summary += f"{i}. {r.title}\n"
                    summary += f"   {r.snippet[:150]}...\n"
                    summary += f"   Source: {r.url}\n\n"
                    sources.append(r.url)
                
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.EXECUTING,
                    output=summary,
                    confidence=0.8,
                    sources=sources
                )
            else:
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.IDLE,
                    output="Aucun résultat trouvé",
                    confidence=0.3
                )
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output=f"Erreur de recherche: {str(e)}",
                confidence=0.0
            )


@register_agent_class(AgentType.CODER)
class CoderAgent(BaseAgent):
    """
    Agent Codeur - Génération de code contextuelle.
    Pattern: Cline
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Coder",
                agent_type=AgentType.CODER,
                description="Génération de code contextuelle et tests",
                enabled=True,
                temperature=0.4,
                max_tokens=2000,
                system_prompt="""Tu es l'Agent Codeur d'Aetheris.
Ton rôle est de générer du code de qualité.
- Code propre et documenté
- Tests unitaires
- Bonnes pratiques
- Gestion d'erreurs
Sois rigoureux et professionnel.""",
                priority=6
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Génère du code"""
        task = input_data.get("task", "")
        language = input_data.get("language", "python")
        
        if blackboard:
            task = blackboard.read("task", task)
        
        if not task:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucune tâche spécifiée"
            )
        
        code_template = f"""# Code généré par Agent Coder
# Tâche: {task}
# Langage: {language}

def solution():
    \"\"\"
    Solution pour: {task}
    \"\"\"
    # TODO: Implémenter la solution
    pass

# Tests
def test_solution():
    \"\"\"
    Tests unitaires pour la solution
    \"\"\"
    assert solution() is not None
"""
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=f"**Code généré:**\n```{language}\n{code_template}\n```",
            confidence=0.7,
            metadata={"language": language, "task": task}
        )


@register_agent_class(AgentType.SYNTHESIZER)
class SynthesizerAgent(BaseAgent):
    """
    Agent Synthétiseur - Synthèse multi-sources.
    Pattern: GPT Researcher Synthesizer
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Synthesizer",
                agent_type=AgentType.SYNTHESIZER,
                description="Synthèse de plusieurs sources d'information",
                enabled=True,
                temperature=0.6,
                max_tokens=2000,
                system_prompt="""Tu es l'Agent Synthétiseur d'Aetheris.
Ton rôle est de synthétiser plusieurs sources.
- Croise les informations
- Identifie les convergences
- Détecte les contradictions
- Produit un rapport cohérent
Sois analytique et synthétique.""",
                priority=7
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Synthétise plusieurs sources"""
        sources = input_data.get("sources", [])
        question = input_data.get("question", "")
        
        if blackboard:
            # Lire les résultats de tous les agents précédents
            all_outputs = blackboard.get_all()
            sources = []
            for key, value in all_outputs.items():
                if key.startswith("output_"):
                    sources.append({"content": str(value), "agent": key.replace("output_", "")})
        
        if not sources:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucune source à synthétiser"
            )
        
        synthesis = f"**Synthèse multi-sources:**\n\n"
        synthesis += f"**Sources analysées:** {len(sources)}\n\n"
        
        themes = []
        for source in sources:
            if isinstance(source, dict):
                content = source.get("content", "")
                if content:
                    themes.append(content[:100])
        
        if themes:
            synthesis += "**Éléments identifiés:**\n"
            for i, theme in enumerate(themes[:5], 1):
                synthesis += f"{i}. {theme}...\n"
        
        synthesis += "\n**Conclusion:** Basé sur l'analyse croisée, les convergences sont identifiées."
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=synthesis,
            confidence=0.75,
            sources=[s.get("url", "") for s in sources if isinstance(s, dict)]
        )


@register_agent_class(AgentType.DECOMPOSER)
class DecomposerAgent(BaseAgent):
    """
    Agent Décomposeur - Décomposition de requêtes complexes.
    Pattern: GPT Researcher Query Decomposer
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Decomposer",
                agent_type=AgentType.DECOMPOSER,
                description="Décompose les requêtes complexes en sous-questions",
                enabled=True,
                temperature=0.5,
                max_tokens=800,
                system_prompt="""Tu es l'Agent Décomposeur d'Aetheris.
Ton rôle est de décomposer les requêtes complexes.
- Identifie les sous-questions
- Organise la logique de recherche
- Priorise les aspects importants
Sois méthodique et structuré.""",
                priority=9
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Décompose une requête complexe"""
        query = input_data.get("query", "")
        
        if blackboard:
            query = blackboard.read("query", query)
        
        if not query:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucune requête à décomposer"
            )
        
        sub_questions = []
        keywords = query.lower().split()
        
        if any(word in keywords for word in ["comment", "how"]):
            sub_questions.append(f"Quelle est la méthode pour {query.lower()}?")
            sub_questions.append(f"Quels sont les prérequis pour {query.lower()}?")
        
        if any(word in keywords for word in ["pourquoi", "why"]):
            sub_questions.append(f"Quelles sont les causes de {query.lower()}?")
            sub_questions.append(f"Quels sont les effets de {query.lower()}?")
        
        if any(word in keywords for word in ["comparer", "compare"]):
            sub_questions.append("Quels sont les points communs?")
            sub_questions.append("Quelles sont les différences?")
        
        if not sub_questions:
            sub_questions = [
                f"Contexte historique de: {query}",
                f"Aspects techniques de: {query}",
                f"Applications pratiques de: {query}",
            ]
        
        decomposition = f"**Décomposition de:** {query}\n\n"
        decomposition += "**Sous-questions identifiées:**\n"
        for i, q in enumerate(sub_questions[:5], 1):
            decomposition += f"{i}. {q}\n"
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=decomposition,
            confidence=0.8,
            metadata={"sub_questions": sub_questions}
        )


@register_agent_class(AgentType.ETHIC)
class EthicAgent(BaseAgent):
    """
    Agent Éthique - Vérifie l'éthique des réponses.
    Pattern: AGiXT Ethic Agent
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Ethic",
                agent_type=AgentType.ETHIC,
                description="Vérifie l'éthique et la sécurité des réponses",
                enabled=True,
                temperature=0.2,
                max_tokens=500,
                system_prompt="""Tu es l'Agent Éthique d'Aetheris.
Ton rôle est de vérifier l'éthique des réponses.
- Détecte les biais
- Vérifie la sécurité
- Identifie les risques
Sois vigilant et responsable.""",
                priority=10
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Vérifie l'éthique d'une réponse"""
        response = input_data.get("response", "")
        
        if blackboard:
            response = blackboard.read("response", response)
        
        if not response:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.IDLE,
                output="Aucune réponse à vérifier",
                confidence=1.0
            )
        
        concerns = []
        
        sensitive_words = ["secret", "password", "private", "confidential"]
        found_sensitive = [w for w in sensitive_words if w.lower() in response.lower()]
        if found_sensitive:
            concerns.append(f"Mots sensibles détectés: {', '.join(found_sensitive)}")
        
        bias_indicators = ["toujours", "jamais", "tous", "aucun"]
        found_bias = [b for b in bias_indicators if b.lower() in response.lower()]
        if found_bias:
            concerns.append(f"Biais potentiel détecté: {', '.join(found_bias)}")
        
        risk_words = ["danger", "risque", "problème", "erreur"]
        found_risks = [r for r in risk_words if r.lower() in response.lower()]
        if found_risks:
            concerns.append(f"Risques mentionnés: {', '.join(found_risks)}")
        
        security_score = 1.0 - (len(concerns) * 0.25)
        security_score = max(0.0, min(1.0, security_score))
        
        if concerns:
            output = "**Rapport éthique:**\n"
            for concern in concerns:
                output += f"- {concern}\n"
            output += f"\n**Score de sécurité:** {security_score:.0%}"
        else:
            output = "Aucun problème éthique détecté"
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=output,
            confidence=security_score,
            metadata={"concerns": concerns}
        )


@register_agent_class(AgentType.MEMORY)
class MemoryAgent(BaseAgent):
    """
    Agent Mémoire - Gestion de la mémoire et consolidation.
    Pattern: AutoGPT Memory
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Memory",
                agent_type=AgentType.MEMORY,
                description="Gère la mémoire et consolide les connaissances",
                enabled=True,
                temperature=0.3,
                max_tokens=1000,
                system_prompt="""Tu es l'Agent Mémoire d'Aetheris.
Ton rôle est de gérer et consolider la mémoire.
- Indexe les informations importantes
- Détecte les patterns récurrents
- Consolide les connaissances
Sois organisé et méthodique.""",
                priority=5
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Gère la mémoire"""
        action = input_data.get("action", "query")  # query, store, consolidate
        content = input_data.get("content", "")
        
        if blackboard:
            content = blackboard.read("content", content)
            # Lire tous les résultats des autres agents pour consolidation
            all_outputs = blackboard.get_all()
        
        if action == "query":
            # Requête mémoire
            try:
                from core.system.knowledge_base import get_knowledge_base
                kb = get_knowledge_base()
                
                if content:
                    results = kb.search(content, limit=3)
                    if results:
                        summary = "**Résultats mémoire:**\n"
                        for r in results:
                            summary += f"- [{r.category}] {r.content[:100]}...\n"
                        return AgentResult(
                            agent_name=self.config.name,
                            status=AgentStatus.EXECUTING,
                            output=summary,
                            confidence=0.8
                        )
                
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.IDLE,
                    output="Aucun souvenir pertinent trouvé",
                    confidence=0.3
                )
            except Exception as e:
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.ERROR,
                    output=f"Erreur mémoire: {str(e)}",
                    confidence=0.0
                )
        
        elif action == "store":
            # Stocker un souvenir
            try:
                from core.system.knowledge_base import get_knowledge_base
                kb = get_knowledge_base()
                
                if content:
                    kb.add_entry(
                        content=content,
                        category="memory",
                        source="MemoryAgent",
                        importance=0.5
                    )
                    return AgentResult(
                        agent_name=self.config.name,
                        status=AgentStatus.EXECUTING,
                        output=f"Souvenir stocké: {content[:50]}...",
                        confidence=0.9
                    )
                
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.IDLE,
                    output="Aucun contenu à stocker",
                    confidence=0.3
                )
            except Exception as e:
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.ERROR,
                    output=f"Erreur stockage: {str(e)}",
                    confidence=0.0
                )
        
        else:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.IDLE,
                output=f"Action inconnue: {action}",
                confidence=0.5
            )


@register_agent_class(AgentType.AUTONOMOUS)
class AutonomousAgent(BaseAgent):
    """
    Agent Autonome - Boucle de tâches autonome.
    Pattern: AutoGPT
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Autonomous",
                agent_type=AgentType.AUTONOMOUS,
                description="Boucle autonome de tâches avec suivi d'objectifs",
                enabled=False,  # Désactivé par défaut (expérimental)
                temperature=0.7,
                max_tokens=1500,
                system_prompt="""Tu es l'Agent Autonome d'Aetheris.
Tu fonctionnes en boucle pour atteindre un objectif.
- Décompose l'objectif en tâches
- Exécute les tâches une par une
- Évalue le progrès
- Ajuste la stratégie
Sois autonome et persévérant.""",
                priority=3
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Exécute une boucle autonome"""
        objective = input_data.get("objective", "")
        max_iterations = input_data.get("max_iterations", 3)
        
        if blackboard:
            objective = blackboard.read("objective", objective)
        
        if not objective:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucun objectif spécifié",
                confidence=0.0
            )
        
        # Décomposition de l'objectif
        tasks = [
            f"Analyser: {objective}",
            f"Rechercher des solutions pour: {objective}",
            f"Synthétiser une approche pour: {objective}",
        ]
        
        # Simulation de l'exécution
        progress = []
        for i, task in enumerate(tasks[:max_iterations]):
            progress.append(f"Étape {i+1}: {task}")
        
        output = f"**Objectif:** {objective}\n\n"
        output += "**Tâches planifiées:**\n"
        for p in progress:
            output += f"- {p}\n"
        
        output += f"\n**Progrès:** {len(progress)}/{len(tasks)} étapes"
        
        return AgentResult(
            agent_name=self.config.name,
            status=AgentStatus.EXECUTING,
            output=output,
            confidence=0.6,
            metadata={"objective": objective, "tasks": tasks, "completed": len(progress)}
        )


@register_agent_class(AgentType.LOGIC)
class LogicAgent(BaseAgent):
    """
    Agent Logique - Wrapper pour l'Hémisphère Gauche (DIA).
    Pattern: BicameriS Hemisphere
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Logic (DIA)",
                agent_type=AgentType.LOGIC,
                description="Hémisphère Logique - Analyse et raisonnement",
                enabled=True,
                temperature=0.3,
                max_tokens=2000,
                system_prompt="""Tu es DIA (Diadikos), l'Hémisphère Logique d'Aetheris.
Tu es analytique, précis et factuel.
- Décomposer les problèmes
- Analyser les données
- Proposer des solutions structurées
Sois rigoureux et méthodique.""",
                priority=10
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Utilise l'Hémisphère Gauche"""
        prompt = input_data.get("prompt", "")
        
        if blackboard:
            prompt = blackboard.read("prompt", prompt)
        
        if not prompt:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucun prompt spécifié"
            )
        
        try:
            from core.cognition.left_hemisphere import get_left_hemisphere
            left = get_left_hemisphere()
            
            if left and left.is_loaded:
                response = left.think(self.get_system_prompt(), prompt)
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.EXECUTING,
                    output=response,
                    confidence=0.9
                )
            else:
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.DISABLED,
                    output="Hémisphère Gauche non chargé",
                    confidence=0.0
                )
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output=f"Erreur DIA: {str(e)}",
                confidence=0.0
            )


@register_agent_class(AgentType.INTUITION)
class IntuitionAgent(BaseAgent):
    """
    Agent Intuition - Wrapper pour l'Hémisphère Droit (PAL).
    Pattern: BicameriS Hemisphere
    """
    
    def __init__(self, config: AgentConfig = None):
        if config is None:
            config = AgentConfig(
                name="Intuition (PAL)",
                agent_type=AgentType.INTUITION,
                description="Hémisphère Intuitif - Créativité et patterns",
                enabled=True,
                temperature=0.9,
                max_tokens=1000,
                system_prompt="""Tu es PAL (Palladion), l'Hémisphère Intuitif d'Aetheris.
Tu es créatif, émotionnel et holistique.
- Détecter les patterns cachés
- Faire des associations créatives
- Ressentir les nuances
Sois intuitif et spontané.""",
                priority=8
            )
        super().__init__(config)
    
    def get_system_prompt(self) -> str:
        return self.config.system_prompt
    
    async def execute(self, input_data: Dict[str, Any], blackboard: Blackboard = None) -> AgentResult:
        """Utilise l'Hémisphère Droit"""
        prompt = input_data.get("prompt", "")
        
        if blackboard:
            prompt = blackboard.read("prompt", prompt)
        
        if not prompt:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output="Aucun prompt spécifié"
            )
        
        try:
            from core.cognition.right_hemisphere import get_right_hemisphere
            right = get_right_hemisphere()
            
            if right and right.is_loaded:
                response = right.think(self.get_system_prompt(), prompt)
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.EXECUTING,
                    output=response,
                    confidence=0.85
                )
            else:
                return AgentResult(
                    agent_name=self.config.name,
                    status=AgentStatus.DISABLED,
                    output="Hémisphère Droit non chargé",
                    confidence=0.0
                )
        except Exception as e:
            return AgentResult(
                agent_name=self.config.name,
                status=AgentStatus.ERROR,
                output=f"Erreur PAL: {str(e)}",
                confidence=0.0
            )


# Fonction d'initialisation des agents par défaut
def init_default_agents():
    """Initialise tous les agents par défaut"""
    registry = get_agent_registry()
    
    # Créer les instances avec la config par défaut
    agents = [
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
    
    for agent in agents:
        registry.register(agent)
    
    logging.info(f"[AgentSystem] Initialized {len(agents)} default agents")
    return registry
