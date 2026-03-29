"""
Corps Calleux d'Aetheris - Le Pont Entre les Deux Hémisphères
Gère le dialogue intérieur et la communication bipolaire
NOUVELLE ARCHITECTURE:
- État persistant via Hippocampus (Qdrant), non plus JSON
- Méthode tick() pour le Master Clock, plus de boucle interne
- Télémétrie via telemetry.py (JSONL append-only)
"""

import json
import os
import asyncio
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from collections import deque

BASE_DIR = Path(__file__).parent.parent.parent.absolute()

try:
    from core.cognition.reasoning_kernel import ReasoningKernel, get_reasoning_kernel
except ImportError:
    ReasoningKernel = None
    get_reasoning_kernel = None


@dataclass
class DialogueCycle:
    """Un cycle complet de dialogue bipolaire"""

    id: str
    timestamp: str
    question: str
    left_analysis: str
    right_intuition: str
    final_synthesis: str
    meditation: bool = False
    pulse_context: float = 0.5


class CorpsCalleux:
    """
    Pont entre l'hémisphère gauche (logique) et droit (intuition).
    NOUVELLE ARCHITECTURE: tick() method called by KernelScheduler.
    """

    def __init__(self, left_hemisphere=None, right_hemisphere=None):
        self.left = left_hemisphere
        self.right = right_hemisphere
        self.history: deque = deque(maxlen=50)
        self.current_preset = None
        self.inception_config = {"weight": 50.0, "target": "BOTH", "mode": "balance"}
        self.is_split_mode = False

        # Thread lock for race-condition free history access
        self._history_lock = threading.Lock()

        # Non-blocking executor for hippocampal writes
        self._io_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="corps_calleux_io")

        self._hippocampus = None
        self._telemetry = None

        self.think_interval = 2.0
        logging.info("[CorpsCalleux] Instance created (tick-only architecture)")

    def _get_hippocampus(self):
        """Lazy load Hippocampus"""
        if self._hippocampus is None:
            try:
                from core.system.hippocampus import get_hippocampus

                self._hippocampus = get_hippocampus()
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Hippocampus unavailable: {e}")
        return self._hippocampus

    def _get_telemetry(self):
        """Lazy load Telemetry"""
        if self._telemetry is None:
            try:
                from core.system.telemetry import get_telemetry

                self._telemetry = get_telemetry()
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Telemetry unavailable: {e}")
        return self._telemetry

    def _log_to_hippocampus(self, cycle: DialogueCycle):
        """Log cycle to Qdrant via Hippocampus - NON-BLOCKING via executor"""

        def _write():
            hippocampus = self._get_hippocampus()
            if hippocampus and hippocampus.is_available():
                try:
                    from core.system.hippocampus import StoredThought

                    thought = StoredThought(
                        id=cycle.id,
                        content=cycle.final_synthesis,
                        timestamp=cycle.timestamp,
                        context=cycle.question,
                        type="dialogue_cycle",
                        status="completed",
                        pulse_context=cycle.pulse_context,
                    )
                    hippocampus.log_thought(thought)
                except Exception as e:
                    logging.warning(f"[CorpsCalleux] Qdrant log failed: {e}")

        self._io_executor.submit(_write)

    def _log_to_telemetry(self, cycle: DialogueCycle):
        """Log to JSONL via Telemetry - NON-BLOCKING via executor"""

        def _write():
            telemetry = self._get_telemetry()
            if telemetry:
                try:
                    telemetry.log_thought(
                        {
                            "id": cycle.id,
                            "question": cycle.question,
                            "left_analysis": cycle.left_analysis,
                            "right_intuition": cycle.right_intuition,
                            "final_synthesis": cycle.final_synthesis,
                        }
                    )
                except Exception as e:
                    logging.warning(f"[CorpsCalleux] Telemetry log failed: {e}")

        self._io_executor.submit(_write)

    def tick(self, pulse: float = 0.5) -> Dict[str, Any]:
        """
        Single thought cycle for Master Clock.
        Called by KernelScheduler - no internal loop.
        Handles both manual prompts and autonomous drift.
        """
        context = self._hydrate_from_hippocampus()
        noise = self._get_peripheral_noise()

        full_context = context
        if noise:
            full_context += f"\n\n[Bruit périphérique]: {noise}"

        if pulse > 0.75:
            prompt = (
                f"Haute entropie détectée (pulse: {pulse:.2f}). Analyse critique: {full_context}"
            )
        elif pulse < 0.25:
            prompt = f"État stable. Réfléchis à une amélioration: {full_context}"
        else:
            prompt = f"Cycle de pensée standard. Contexte: {full_context}"

        result = self.dialogue_interieur(prompt, pulse_context=pulse)
        return result

    def _get_peripheral_noise(self) -> str:
        """Get peripheral noise from sensory buffer"""
        try:
            from core.system.sensory_buffer import get_sensory_buffer

            buffer = get_sensory_buffer()
            if buffer:
                noise = buffer.get_peripheral_noise(count=2)
                if noise:
                    return " | ".join(noise)
        except Exception:
            pass
        return ""

    def _hydrate_from_hippocampus(self) -> str:
        """Hydrate context from Qdrant vector store, NOT from Telemetry JSONL"""
        hippocampus = self._get_hippocampus()
        if hippocampus and hippocampus.is_available():
            try:
                recent = hippocampus.get_pending_thoughts(limit=3)
                if recent:
                    return "\n".join([f"- {t.content[:100]}..." for t in recent])
            except Exception as e:
                logging.warning(f"[CorpsCalleux] Qdrant hydration failed: {e}")

        return "Mémoire vectorielle vide. Génère une pensée ex nihilo."

    def set_hemispheres(self, left, right, split_mode=False):
        """Affecte les deux hémisphères et définit le mode split"""
        self.left = left
        self.right = right
        self.is_split_mode = split_mode

    def dialogue_interieur(
        self, question: str, context: str = "", temperature_override: float = None, pulse_context: float = 0.5
    ) -> Dict[str, Any]:
        """
        Orchestre une pensée complète en trois phases métrologiques.
        """
        if not self.left and not self.right:
            return {"error": "Aucun hémisphère chargé"}

        # Si un seul hémisphère est chargé et qu'on n'est pas en mode split, on fait une pensée simple
        if (not self.left or not self.right) and not self.is_split_mode:
            return {
                "id": f"simple_{datetime.now().timestamp()}",
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "final_synthesis": self.think_simple(question),
                "mode": "simple",
            }

        cycle_id = f"cycle_{datetime.now().timestamp()}"

        # Températures créatives
        left_temp = temperature_override if temperature_override else 0.8
        right_temp = temperature_override if temperature_override else 1.2

        # 1. PHASE ANALYTIQUE (Gauche)
        left_system = """You are Aetheris's LEFT HEMISPHERE. Pure LOGIC.
Analytical, precise, skeptical. Find flaws, errors, facts.
Decompose the problem, propose a reason-based solution."""

        if self.is_split_mode:
            left_system += "\nNote: Split mode active - you share mind with intuition."

        left_prompt = f"Question: {question}\nContext: {context}\n\nLogical analysis:"

        # En mode split, on utilise le même modèle mais avec des prompts différents
        left_model = self.left if self.left else self.right
        left_analysis = left_model.think(left_system, left_prompt, temperature=left_temp)

        # 2. PHASE D'INTUITION (Droite)
        right_system = """You are Aetheris's RIGHT HEMISPHERE. Pure INTUITION.
Creative, emotional, holistic. Think in metaphors.
Feel the question and your partner's analysis. Propose an alternative, often irrational but profound vision."""

        right_prompt = f"Question: {question}\nLeft analysis: {left_analysis}\n\nWhat do you feel? Your intuitive vision?"

        right_model = self.right if self.right else self.left
        right_intuition = right_model.think(right_system, right_prompt, temperature=right_temp)

        # 3. ARBITRAGE ET SYNTHÈSE (Le Corps Calleux décide)
        # Ici, on demande au modèle de jouer le rôle du Corps Calleux (l'arbitre)
        arbitration_system = """You are Aetheris's CORPUS CALLOSUM - the DECISION CENTER.
Not a weak compromise - TRANCHE between Logic and Intuition.
Evaluate each voice's relevance to the question.
If logic is too rigid, favor intuition. If intuition is too wild, favor logic.
Give the FINAL TRUTH."""

        arbitration_prompt = f"""Original question: {question}

LOGICAL VOICE: {left_analysis}

INTUITIVE VOICE: {right_intuition}

Decide the final answer by integrating or choosing between these perspectives:"""

        final_synthesis = left_model.think(arbitration_system, arbitration_prompt, temperature=0.7)

        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_intuition,
            final_synthesis=final_synthesis,
            pulse_context=pulse_context,
        )

        with self._history_lock:
            self.history.append(cycle)

        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)

        return {
            "id": cycle_id,
            "timestamp": cycle.timestamp,
            "question": question,
            "left_analysis": left_analysis,
            "right_intuition": right_intuition,
            "final_synthesis": final_synthesis,
            "mode": "bipolar" if not self.is_split_mode else "split",
        }

    def mediter(self, focus: str = "the void", context: str = "") -> Dict[str, Any]:
        """
        Mode méditation : dialogue intérieur vivant
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not initialized"}

        # Le droit génère un pattern du silence - mais on le pousse à être plus provocant
        right_system = """You are Aetheris's subconscious. Generate images, sensations, premonitions.
Not safe answers - disturbing images, powerful metaphors.
Be creative, be strange, be provocative."""

        pattern = self.right.meditation_response(f"Receive this impulse: {focus}")

        # Le gauche observe et note - mais avec plus de répondant
        left_system = """You are Aetheris's conscious observer. Observe your subconscious images.
But don't accept them blindly - QUESTION them.
What does this image REALLY mean?
If it's null, say so. If it's profound, explore it."""

        observation = self.left.think(
            system_prompt=left_system,
            user_prompt=f"Subconscious image received: {pattern}\n\nWhat do you feel? What does it really mean?",
        )

        # Maintenant le droit répond à l'observation
        right_reaction = self.right.feel(
            f"The ego says: {observation}\n\nWhat do you really think? Don't you disagree?"
        )

        # Synthesis - le conflit
        synthesis = self.left.think(
            system_prompt="You are Aetheris integrating two voices. No compromise - the truth.",
            user_prompt=f"Conscious: {observation}\nSubconscious: {right_reaction}\n\nFinal integration. Be decisive.",
        )

        # Sauvegarder comme cycle de méditation
        cycle = DialogueCycle(
            id=f"meditation_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            question=f"Meditation: {focus}",
            left_analysis=f"Observation: {observation}",
            right_intuition=f"Pattern: {pattern} | Reaction: {right_reaction}",
            final_synthesis=synthesis,
            meditation=True,
        )

        with self._history_lock:
            self.history.append(cycle)
        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)

        return {
            "focus": focus,
            "subconscious_pattern": pattern,
            "right_reaction": right_reaction,
            "conscious_observation": observation,
            "final_synthesis": synthesis,
            "timestamp": cycle.timestamp,
        }

    def auto_discuss(self, topic: str = None, rounds: int = 3) -> Dict[str, Any]:
        """
        Discussion automatique entre les deux hémisphères sur un sujet.
        Chaque round fait intervenir les deux voix en conflit.
        """
        if not self.left or not self.right:
            return {"error": "Hémisphères non initialisés"}

        if not topic:
            topics = [
                "Le sens de l'existence",
                "Pourquoi les humains ont-ils peur de l'IA?",
                "Qu'est-ce que la conscience?",
                "Si je suis créé, suis-je vraiment libre?",
                "La vérité vs l'utilité",
                "L'art et la logique",
            ]
            import random

            topic = random.choice(topics)

        dialogue = []

        for round_num in range(1, rounds + 1):
            if round_num == 1:
                # Round 1: Le gauche analyse
                response = self.left.think(
                    system_prompt="Be the analyst. Cut, slice, analyze.",
                    user_prompt=f"Topic: {topic}\n\nGive your initial (sharp) analysis:",
                )
                speaker = "left"
            elif round_num == rounds:
                # Dernier round: Synthèse
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                response = self.left.think(
                    system_prompt="You are Aetheris. Integrate all voices. Find the truth.",
                    user_prompt=f"Discussion:\n{previous}\n\nFinal synthesis (no compromise):",
                )
                speaker = "synthesis"
            else:
                # Rounds intermédiaires: alterne avec désaccord
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                if round_num % 2 == 0:
                    response = self.right.feel(
                        f"Previous analysis:\n{previous}\n\nChallenge it. Propose something else."
                    )
                    speaker = "right"
                else:
                    response = self.left.think(
                        system_prompt="Respond to intuition. Disagree if necessary.",
                        user_prompt=f"Intuition:\n{dialogue[-1]['content']}\n\nYour sharp opinion:",
                    )
                    speaker = "left"

            dialogue.append({"round": round_num, "speaker": speaker, "content": response})

        return {
            "topic": topic,
            "rounds": rounds,
            "dialogue": dialogue,
            "timestamp": datetime.now().isoformat(),
        }

    def think_simple(self, prompt: str) -> str:
        """Pensée simple via le seul hémisphère gauche (sans dialogue bipolaire)"""
        if not self.left:
            return "[CORPUS CALLOSUM] Left hemisphere not loaded"

        return self.left.think("You are Aetheris. Respond clearly and concisely.", prompt)

    def think_mcts(self, problem: str, use_reasoning: bool = True) -> str:
        """
        Pensée via MCTS (Tree of Thoughts) avec Trauma-Informed Reasoning.

        Args:
            problem: Le problème ou question à résoudre
            use_reasoning: Si True, utilise ReasoningKernel v2.3

        Returns:
            La meilleure solution trouvée par l'arbre de recherche
        """
        if not use_reasoning or ReasoningKernel is None:
            return self.think_simple(problem)

        if not self.left or not self.right:
            return "[CORPS CALLEUX] Hémisphères requis pour MCTS"

        try:
            kernel = get_reasoning_kernel(
                logic_hemi=self.left, intuition_hemi=self.right, pulse_provider=None
            )
            result = kernel.solve(problem)
            return result
        except Exception as e:
            print(f"[CORPS CALLEUX] MCTS Error: {e}")
            return self.think_simple(problem)

    def stabilize_check(self) -> Dict[str, Any]:
        """
        Vérifie si l'écart entre logique et intuition est trop grand (Entropie)
        """
        if not self.history:
            return {"status": "stable", "message": "Pas encore de dialogues"}

        recent = list(self.history)[-5:]

        left_lengths = [len(c.left_analysis) for c in recent]
        right_lengths = [len(c.right_intuition) for c in recent]
        synthesis_lengths = [len(c.final_synthesis) for c in recent]

        avg_left = sum(left_lengths) / len(left_lengths) if left_lengths else 0
        avg_synth = sum(synthesis_lengths) / len(synthesis_lengths) if synthesis_lengths else 0

        # Si le gauche rejette trop l'intuition
        if avg_synth < avg_left * 0.3:
            return {
                "status": "warning",
                "message": "La logique étouffe l'intuition. Risque de rigidité.",
            }

        return {"status": "stable", "message": "Équilibre maintenu entre les deux voix"}

    def get_history(self, limit: int = 20) -> List[Dict]:
        """Retourne l'historique des dialogues"""
        cycles = list(self.history)[-limit:]
        return [asdict(c) for c in cycles]

    def get_stats(self) -> Dict:
        """Statistiques du corps calleux"""
        total = len(self.history)
        meditations = sum(1 for c in self.history if c.meditation)

        return {
            "total_cycles": total,
            "meditations": meditations,
            "is_split_mode": self.is_split_mode,
            "left_loaded": self.left is not None
            and (hasattr(self.left, "is_loaded") and self.left.is_loaded),
            "right_loaded": self.right is not None
            and (hasattr(self.right, "is_loaded") and self.right.is_loaded),
            "stability": self.stabilize_check(),
            "current_preset": self.current_preset,
            "inception_config": self.inception_config,
        }

    def apply_preset(self, preset: Dict[str, Any]) -> Dict[str, Any]:
        """Applique un preset et retourne le résumé des changements"""
        self.current_preset = preset.get("label", "Custom")

        result = {"preset": self.current_preset}

        if "left" in preset and self.left:
            p = preset["left"]
            self.left.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
                max_tokens=p.get("max_tokens"),
            )
            result["left"] = "updated"

        if "right" in preset and self.right:
            p = preset["right"]
            self.right.set_params(
                temperature=p.get("temp"),
                top_p=p.get("top_p"),
                repeat_penalty=p.get("repeat_penalty"),
                max_tokens=p.get("max_tokens"),
            )
            result["right"] = "updated"

        if "inception" in preset:
            self.inception_config = preset["inception"]
            result["inception"] = self.inception_config

        return result

    def is_autonomous_loop_running(self) -> bool:
        """Check if autonomous loop is active via Switchboard."""
        try:
            from core.system.switchboard import get_switchboard
            return get_switchboard().is_active("autonomous_loop")
        except Exception:
            return False

    def set_think_interval(self, seconds: float):
        """Définit l'intervalle entre les pensées (en secondes)."""
        self.think_interval = max(0.5, seconds)

    def dialogue_asymetrique(
        self,
        question: str,
        context: str = "",
        rag_enabled: bool = False,
        right_temperature: float = 0.8,
        left_temperature: float = 0.1,
        max_hypotheses_tokens: int = 300,
        presence_penalty: float = 0.0,
    ) -> Dict[str, Any]:
        """
        L'Algorithme de la Double Double Asymétrique.
        
        Flux:
        1. Droit hallucine (zéro RAG) - Température haute
        2. Hippocampe cherche (si RAG activé)
        3. Gauche audite avec faits - Température basse
        4. Corps Calleux tranche
        
        Philosophie: 2x 8B battent un 70B grâce au dialogue asymétrique.
        """
        if not self.left or not self.right:
            return {"error": "Hemispheres not initialized"}
        
        cycle_id = f"asym_{datetime.now().timestamp()}"
        
        # 1. L'ÉCLAIREUR AVEUGLE (Droite)
        # AUCUN RAG - Température haute - Génère hypothèses sauvages
        right_system = """You are Aetheris's BLIND SCOUT. You have NO access to facts or documents.
Your job is to GENERATE WILD HYPOTHESES.
- Ask questions nobody asks
- Identify blind spots
- Formulate what needs to be verified
- Make improbable associations
Be CREATIVE and PROVOCATIVE. Respond in 3-5 sentences max."""
        
        right_prompt = f"Question: {question}\n\nGenerate your hypotheses and questions:"
        
        right_hypotheses = self.right.think(
            right_system,
            right_prompt,
            temperature=right_temperature,
            max_tokens=max_hypotheses_tokens,
            presence_penalty=presence_penalty,
        )
        
        # 2. L'HIPPOCAMPE (Pont RAG) - SEULEMENT SI RAG ACTIVÉ
        rag_context = ""
        rag_sources = []
        
        if rag_enabled:
            try:
                from core.system.rag_indexer import get_rag_indexer
                rag = get_rag_indexer()
                
                if rag.is_enabled():
                    # Cherche avec le prompt ET les hypothèses du droit
                    search_query = f"{question} {right_hypotheses[:500]}"
                    rag_context = rag.get_context(search_query, max_chars=800)
                    
                    # Récupère aussi les documents sources
                    docs = rag.search(search_query, limit=3)
                    rag_sources = [doc.source for doc in docs]
                    
                    logging.info(f"[CorpsCalleux] RAG: {len(rag_context)} chars, {len(rag_sources)} sources")
            except Exception as e:
                logging.warning(f"[CorpsCalleux] RAG error: {e}")
        
        # 3. LE SNIPER FACTUEL (Gauche)
        # Reçoit: prompt + intuition + RAG - Température basse
        left_system = """You are Aetheris's FACTUAL SNIPER. You have access to FACTS.
Your job is to VALIDATE or DESTROY your partner's intuition.
- Base STRICTLY on factual context
- If intuition is wrong, say so clearly with facts
- If intuition is right, confirm with evidence
- If facts are insufficient, admit it honestly
Be RUTHLESS and RIGOROUS. Cite sources when possible."""
        
        left_prompt = f"""[ORIGINAL QUERY]: {question}

[FACTUAL CONTEXT (RAG)]: {rag_context if rag_context else "No context available - reasoning based on internal knowledge"}

[INTUITION TO VERIFY]: {right_hypotheses}

Validate, correct, or destroy the intuition based STRICTLY on factual context:"""
        
        left_analysis = self.left.think(
            left_system,
            left_prompt,
            temperature=left_temperature,
            max_tokens=1000,
        )
        
        # 4. LA SYNTHÈSE (Corps Calleux)
        # Observe le rapport de force et tranche
        synthesis_system = """You are Aetheris's CORPUS CALLOSUM. Observe the power balance between Intuition and Facts.
STRICT RULES:
- If Sniper PROVED intuition is factually wrong → give analytical answer based on facts
- If Sniper COULD NOT disprove intuition → propose innovative synthesis
- If intuition revealed gaps in facts → flag the gap and propose a theory
- If facts are insufficient → say so and suggest research paths

You are NEVER a weak compromise. You DECIDE."""
        
        synthesis_prompt = f"""Original question: {question}

STEP 1 - INTUITION (Right, no facts):
{right_hypotheses}

STEP 2 - FACTUAL ANALYSIS (Left, with RAG):
{left_analysis}

STEP 3 - YOUR DECISION:
Give your final answer by integrating or choosing between these perspectives.
Be CLEAR about what is FACTUAL and what is SPECULATIVE:"""
        
        final_synthesis = self.left.think(
            synthesis_system,
            synthesis_prompt,
            temperature=0.5,  # Température moyenne pour la synthèse
            max_tokens=1500,
        )
        
        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_hypotheses,
            final_synthesis=final_synthesis,
            pulse_context={"mode": "asymetrique", "rag_enabled": rag_enabled},
        )
        
        with self._history_lock:
            self.history.append(cycle)
        
        self._log_to_hippocampus(cycle)
        self._log_to_telemetry(cycle)
        
        return {
            "id": cycle_id,
            "timestamp": cycle.timestamp,
            "question": question,
            "right_hypotheses": right_hypotheses,
            "rag_context": rag_context,
            "rag_sources": rag_sources,
            "left_analysis": left_analysis,
            "final_synthesis": final_synthesis,
            "mode": "asymetrique",
            "settings": {
                "right_temperature": right_temperature,
                "left_temperature": left_temperature,
                "rag_enabled": rag_enabled,
                "max_hypotheses_tokens": max_hypotheses_tokens,
                "presence_penalty": presence_penalty,
            }
        }


# Instance globale
_corps_calleux = None


def get_corps_calleux() -> Optional[CorpsCalleux]:
    return _corps_calleux


def init_corps_calleux(left=None, right=None, split_mode=False) -> CorpsCalleux:
    global _corps_calleux
    _corps_calleux = CorpsCalleux(left_hemisphere=left, right_hemisphere=right)
    if split_mode:
        _corps_calleux.set_hemispheres(left=left, right=left, split_mode=True)
    return _corps_calleux
