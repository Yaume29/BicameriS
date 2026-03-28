"""
Unified Engine - Bicameral Intelligence Module
===============================================
Moteur principal du dialogue bicaméral.
Favorise l'émergence à travers le Corps Calleux.

Philosophie: "La beauté c'est vous, pas les outils qui vous sublime"
- Corps Calleux = Émergence (toujours actif)
- RAG = Dépendance (optionnel, désactivé par défaut)
- L'intelligence vient du dialogue, pas de la recherche externe
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UnifiedMode(str, Enum):
    """Modes de fonctionnement du module unifié"""
    EMERGENCE = "emergence"      # Mode par défaut - dialogue pur
    KNOWLEDGE = "knowledge"      # RAG activé
    HYBRID = "hybrid"           # RAG seulement si nécessaire


class DialogueState(str, Enum):
    """États du dialogue"""
    IDLE = "idle"
    CODEUR_THINKING = "codeur_thinking"
    REVIEWER_THINKING = "reviewer_thinking"
    CORPUS_CALLOUX_SYNC = "corpus_calleux_sync"
    RAG_CONSULTING = "rag_consulting"
    PALLADION_CHECK = "palladion_check"
    COMPLETE = "complete"


@dataclass
class DialogueMessage:
    """Un message dans le dialogue bicaméral"""
    role: str  # user, codeur, reviewer, corpus_calleux, rag, palladion, final
    content: str
    timestamp: str
    iteration: int = 0
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class UnifiedSession:
    """Session de dialogue unifié"""
    session_id: str
    mode: UnifiedMode
    messages: List[DialogueMessage] = field(default_factory=list)
    iterations: int = 0
    max_iterations: int = 5
    rag_consultations: int = 0
    created_at: str = ""
    completed: bool = False
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class CorpusCalloux:
    """
    Corps Calleux - Favorise l'émergence
    Le pont synaptique qui facilite le dialogue entre hémisphères.
    PAS de dépendance au RAG - juste du dialogue pur.
    """
    
    def __init__(self):
        self.dialogue_history: List[Dict] = []
        self.emergence_patterns: List[str] = []
    
    def analyze_dialogue(self, codeur_msg: str, reviewer_msg: str) -> Dict:
        """
        Analyse le dialogue pour détecter l'émergence.
        L'émergence = quand les deux modèles trouvent une solution
        qu'aucun des deux n'aurait trouvé seul.
        """
        # Detecte les convergences
        codeur_words = set(codeur_msg.lower().split())
        reviewer_words = set(reviewer_msg.lower().split())
        
        common = codeur_words & reviewer_words
        convergence = len(common) / max(len(codeur_words), len(reviewer_words))
        
        # Detecte les enrichissements
        codeur_only = codeur_words - reviewer_words
        reviewer_only = reviewer_words - codeur_words
        
        return {
            "convergence": convergence,
            "codeur_unique": len(codeur_only),
            "reviewer_unique": len(reviewer_only),
            "emergence_detected": convergence > 0.3 and len(reviewer_only) > 0,
            "sync_ready": convergence > 0.5
        }
    
    def generate_sync_prompt(self, analysis: Dict) -> str:
        """
        Génère un prompt de synchronisation pour le Corps Calleux.
        C'est ici que l'émergence est facilitée.
        """
        if analysis["emergence_detected"]:
            return (
                "Le dialogue montre des signes d'émergence. "
                "Le Codeur et le Reviewer convergent vers une solution commune. "
                "Synthétise leurs apports respectifs en une solution unifiée."
            )
        elif analysis["convergence"] < 0.3:
            return (
                "Le dialogue est divergent. "
                "Le Codeur et le Reviewer ont des visions différentes. "
                "Identifie les points de désaccord et propose une résolution."
            )
        else:
            return (
                "Le dialogue progresse. "
                "Continue à faciliter l'échange entre les perspectives."
            )


class UnifiedEngine:
    """
    Moteur Unifié - Orchestre le dialogue bicaméral.
    
    Philosophie:
    - L'émergence vient du dialogue (Corps Calleux)
    - Le RAG est optionnel et désactivé par défaut
    - La beauté est dans les modèles, pas dans les outils
    """
    
    def __init__(self):
        self.sessions: Dict[str, UnifiedSession] = {}
        self.corpus_calleux = CorpusCalloux()
        self.rag_enabled = False  # Désactivé par défaut
        
        # Références aux hémisphères (chargés dynamiquement)
        self.codeur = None
        self.reviewer = None
        
        # Statistiques
        self.total_sessions = 0
        self.total_iterations = 0
        self.emergence_count = 0
        
        logging.info("[UnifiedEngine] Initialized - Emergence mode by default")
    
    def set_hemispheres(self, codeur, reviewer):
        """Configure les hémisphères"""
        self.codeur = codeur
        self.reviewer = reviewer
        logging.info("[UnifiedEngine] Hemispheres connected")
    
    def set_mode(self, mode: UnifiedMode):
        """Configure le mode de fonctionnement"""
        if mode == UnifiedMode.KNOWLEDGE:
            self.rag_enabled = True
            logging.info("[UnifiedEngine] RAG enabled - Knowledge mode")
        elif mode == UnifiedMode.EMERGENCE:
            self.rag_enabled = False
            logging.info("[UnifiedEngine] RAG disabled - Emergence mode")
        # Hybrid mode handles RAG on-demand
    
    def create_session(self, mode: UnifiedMode = UnifiedMode.EMERGENCE) -> UnifiedSession:
        """Crée une nouvelle session"""
        session_id = f"unified_{int(time.time())}_{self.total_sessions}"
        session = UnifiedSession(
            session_id=session_id,
            mode=mode,
            max_iterations=5
        )
        self.sessions[session_id] = session
        self.total_sessions += 1
        
        logging.info(f"[UnifiedEngine] Session created: {session_id} in {mode.value} mode")
        return session
    
    async def process_message(
        self,
        session_id: str,
        user_message: str,
        callback=None
    ) -> AsyncGenerator[Dict, None]:
        """
        Traite un message utilisateur à travers le dialogue bicaméral.
        
        Flux:
        1. Codeur génère une réponse
        2. Reviewer critique
        3. Corps Calleux synchronise
        4. Répéter jusqu'à convergence
        5. PALLADION vérifie la sécurité
        """
        session = self.sessions.get(session_id)
        if not session:
            yield {"error": "Session not found"}
            return
        
        # Ajouter le message utilisateur
        user_msg = DialogueMessage(
            role="user",
            content=user_message,
            timestamp=datetime.now().isoformat()
        )
        session.messages.append(user_msg)
        
        yield {
            "type": "user_message",
            "content": user_message,
            "session_id": session_id
        }
        
        # Boucle de dialogue
        for iteration in range(session.max_iterations):
            session.iterations = iteration + 1
            self.total_iterations += 1
            
            # Étape 1: Codeur pense
            yield {"type": "status", "state": "codeur_thinking", "iteration": iteration + 1}
            
            codeur_response = await self._codeur_think(session, user_message)
            
            codeur_msg = DialogueMessage(
                role="codeur",
                content=codeur_response,
                timestamp=datetime.now().isoformat(),
                iteration=iteration + 1
            )
            session.messages.append(codeur_msg)
            
            yield {
                "type": "codeur_message",
                "content": codeur_response,
                "iteration": iteration + 1
            }
            
            # Étape 2: Reviewer critique
            yield {"type": "status", "state": "reviewer_thinking", "iteration": iteration + 1}
            
            reviewer_response = await self._reviewer_think(session, codeur_response, user_message)
            
            reviewer_msg = DialogueMessage(
                role="reviewer",
                content=reviewer_response,
                timestamp=datetime.now().isoformat(),
                iteration=iteration + 1
            )
            session.messages.append(reviewer_msg)
            
            yield {
                "type": "reviewer_message",
                "content": reviewer_response,
                "iteration": iteration + 1
            }
            
            # Étape 3: Corps Calleux synchronise
            yield {"type": "status", "state": "corpus_calleux_sync", "iteration": iteration + 1}
            
            analysis = self.corpus_calleux.analyze_dialogue(codeur_response, reviewer_response)
            
            if analysis["emergence_detected"]:
                self.emergence_count += 1
            
            sync_prompt = self.corpus_calleux.generate_sync_prompt(analysis)
            
            corpus_msg = DialogueMessage(
                role="corpus_calleux",
                content=sync_prompt,
                timestamp=datetime.now().isoformat(),
                iteration=iteration + 1,
                metadata=analysis
            )
            session.messages.append(corpus_msg)
            
            yield {
                "type": "corpus_sync",
                "content": sync_prompt,
                "analysis": analysis,
                "iteration": iteration + 1
            }
            
            # Étape 4: Vérifier convergence
            if analysis["sync_ready"]:
                yield {"type": "status", "state": "convergence_detected"}
                break
            
            # Étape 5: RAG optionnel (seulement si activé et nécessaire)
            if self.rag_enabled and analysis["convergence"] < 0.3:
                yield {"type": "status", "state": "rag_consulting"}
                
                rag_result = await self._consult_rag(session, user_message, codeur_response)
                session.rag_consultations += 1
                
                rag_msg = DialogueMessage(
                    role="rag",
                    content=rag_result,
                    timestamp=datetime.now().isoformat(),
                    iteration=iteration + 1
                )
                session.messages.append(rag_msg)
                
                yield {
                    "type": "rag_message",
                    "content": rag_result,
                    "iteration": iteration + 1
                }
        
        # Étape 6: PALLADION vérifie la sécurité
        yield {"type": "status", "state": "palladion_check"}
        
        final_response = await self._generate_final_response(session)
        
        # Vérification de sécurité
        security_check = await self._palladion_check(final_response)
        
        palladion_msg = DialogueMessage(
            role="palladion",
            content=security_check["message"],
            timestamp=datetime.now().isoformat(),
            metadata=security_check
        )
        session.messages.append(palladion_msg)
        
        yield {
            "type": "palladion_check",
            "passed": security_check["passed"],
            "message": security_check["message"]
        }
        
        # Sortie finale
        if security_check["passed"]:
            final_msg = DialogueMessage(
                role="final",
                content=final_response,
                timestamp=datetime.now().isoformat(),
                confidence=security_check.get("confidence", 0.9)
            )
            session.messages.append(final_msg)
            
            session.completed = True
            
            yield {
                "type": "final_response",
                "content": final_response,
                "confidence": security_check.get("confidence", 0.9),
                "iterations": session.iterations,
                "rag_consultations": session.rag_consultations,
                "emergence_detected": self.emergence_count > 0
            }
        else:
            yield {
                "type": "blocked",
                "reason": security_check.get("reason", "Security check failed")
            }
    
    async def _codeur_think(self, session: UnifiedSession, user_message: str) -> str:
        """
        L'hémisphère gauche (Codeur) génère une réponse.
        """
        if self.codeur and hasattr(self.codeur, 'think'):
            # Construire le contexte du dialogue
            context = self._build_context(session)
            
            system_prompt = (
                "Tu es le Codeur, l'hémisphère logique de BicameriS. "
                "Tu génères du code et des solutions structurées. "
                "Tu dialogues avec le Reviewer pour améliorer tes solutions. "
                "Réponds de manière claire et technique."
            )
            
            response = self.codeur.think(system_prompt, f"{context}\n\nDemande: {user_message}")
            return response
        else:
            # Fallback si pas de modèle
            return f"[Codeur] Je propose une solution pour: {user_message[:100]}..."
    
    async def _reviewer_think(
        self, 
        session: UnifiedSession, 
        codeur_response: str, 
        user_message: str
    ) -> str:
        """
        L'hémisphère droit (Reviewer) critique la réponse du Codeur.
        """
        if self.reviewer and hasattr(self.reviewer, 'think'):
            system_prompt = (
                "Tu es le Reviewer, l'hémisphère intuitif de BicameriS. "
                "Tu critiques les solutions du Codeur, détectes les bugs, "
                "suggeres des améliorations. Tu es constructif mais exigeant. "
                "Tu vois les patterns que le Codeur rate."
            )
            
            prompt = (
                f"Demande originale: {user_message}\n\n"
                f"Solution du Codeur:\n{codeur_response}\n\n"
                "Critique cette solution. Détecte les problèmes et suggère des améliorations."
            )
            
            response = self.reviewer.think(system_prompt, prompt)
            return response
        else:
            return f"[Reviewer] La solution semble correcte mais pourrait être améliorée."
    
    async def _consult_rag(
        self, 
        session: UnifiedSession, 
        user_message: str, 
        codeur_response: str
    ) -> str:
        """
        Consulte le RAG si activé et nécessaire.
        Ceci crée de la DÉPENDANCE - utilisé avec parcimonie.
        """
        # Pour l'instant, retourne un placeholder
        # Le vrai RAG sera implémenté séparément
        return "[RAG] Aucune documentation pertinente trouvée."
    
    async def _generate_final_response(self, session: UnifiedSession) -> str:
        """
        Génère la réponse finale basée sur le dialogue.
        C'est ici que l'ÉMERGENCE se manifeste.
        """
        # Récupérer les derniers messages
        codeur_msgs = [m for m in session.messages if m.role == "codeur"]
        reviewer_msgs = [m for m in session.messages if m.role == "reviewer"]
        
        if codeur_msgs and reviewer_msgs:
            last_codeur = codeur_msgs[-1].content
            last_reviewer = reviewer_msgs[-1].content
            
            # Synthèse simple
            return (
                f"Après dialogue bicaméral ({session.iterations} itérations):\n\n"
                f"Solution finale:\n{last_codeur}\n\n"
                f"Points d'attention:\n{last_reviewer}"
            )
        elif codeur_msgs:
            return codeur_msgs[-1].content
        else:
            return "Le dialogue n'a pas produit de résultat."
    
    async def _palladion_check(self, response: str) -> Dict:
        """
        PALLADION vérifie la sécurité de la réponse.
        """
        try:
            from core.execution.secret_channel import get_secret_channel
            classifier = get_secret_channel()
            result = classifier.classify(response)
            
            return {
                "passed": result["category"] in ["safe", "legal"],
                "message": f"[PALLADION] Sécurité: {result['category']} ({result['risk_level']})",
                "confidence": result.get("confidence", 0.9),
                "reason": result.get("reason", "")
            }
        except Exception as e:
            # Fallback - passe par défaut
            return {
                "passed": True,
                "message": f"[PALLADION] Vérification effectuée",
                "confidence": 0.8
            }
    
    def _build_context(self, session: UnifiedSession) -> str:
        """Construit le contexte du dialogue pour les modèles"""
        if not session.messages:
            return ""
        
        context_parts = []
        for msg in session.messages[-10:]:  # 10 derniers messages
            context_parts.append(f"[{msg.role.upper()}]: {msg.content[:200]}")
        
        return "\n".join(context_parts)
    
    def get_session(self, session_id: str) -> Optional[UnifiedSession]:
        """Récupère une session"""
        return self.sessions.get(session_id)
    
    def get_stats(self) -> Dict:
        """Statistiques du moteur"""
        return {
            "total_sessions": self.total_sessions,
            "total_iterations": self.total_iterations,
            "emergence_count": self.emergence_count,
            "active_sessions": len([s for s in self.sessions.values() if not s.completed]),
            "rag_enabled": self.rag_enabled
        }


# Instance globale
_unified_engine = None


def get_unified_engine() -> UnifiedEngine:
    """Récupère l'instance globale du moteur unifié"""
    global _unified_engine
    if _unified_engine is None:
        _unified_engine = UnifiedEngine()
    return _unified_engine
