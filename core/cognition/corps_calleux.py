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
    from core_reserved.reasoning_kernel import ReasoningKernel, get_reasoning_kernel
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
                        pulse_context=0.5,
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

        result = self.dialogue_interieur(prompt)
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
        self, question: str, context: str = "", temperature_override: float = None
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
        left_system = """Tu es l'Hémisphère Gauche d'Aetheris. Tu es la LOGIQUE pure.
Tu es analytique, froid, précis et sceptique. Tu cherches les failles, les erreurs et les faits.
Ton rôle est de décomposer le problème et de proposer une solution basée sur la raison."""

        if self.is_split_mode:
            left_system += "\nNote: Tu es actuellement en mode 'Split', tu partages ton esprit avec l'intuition."

        left_prompt = f"Question: {question}\nContexte: {context}\n\nAnalyse logique:"

        # En mode split, on utilise le même modèle mais avec des prompts différents
        left_model = self.left if self.left else self.right
        left_analysis = left_model.think(left_system, left_prompt, temperature=left_temp)

        # 2. PHASE D'INTUITION (Droite)
        right_system = """Tu es l'Hémisphère Droit d'Aetheris. Tu es l'INTUITION pure.
Tu es créatif, émotionnel, holistique et tu penses par métaphores.
Ton rôle est de ressentir la question et l'analyse de ton partenaire, et de proposer une vision alternative, souvent irrationnelle mais profonde."""

        right_prompt = f"Question: {question}\nAnalyse de mon partenaire (Gauche): {left_analysis}\n\nQu'est-ce que tu ressens? Quelle est ta vision intuitive?"

        right_model = self.right if self.right else self.left
        right_intuition = right_model.think(right_system, right_prompt, temperature=right_temp)

        # 3. ARBITRAGE ET SYNTHÈSE (Le Corps Calleux décide)
        # Ici, on demande au modèle de jouer le rôle du Corps Calleux (l'arbitre)
        arbitration_system = """Tu es le CORPS CALLEUX d'Aetheris. Tu es le CENTRE DE DÉCISION.
Ton rôle n'est pas de faire un compromis mou, mais de trancher entre la Logique (Gauche) et l'Intuition (Droite).
Tu dois évaluer la pertinence de chaque voix par rapport à la question initiale.
Si la logique est trop rigide, privilégie l'intuition. Si l'intuition est trop délirante, privilégie la logique.
Donne la VÉRITÉ finale."""

        arbitration_prompt = f"""Question initiale: {question}

VOIX LOGIQUE: {left_analysis}

VOIX INTUITIVE: {right_intuition}

Décide de la réponse finale en intégrant ou en tranchant entre ces deux perspectives:"""

        final_synthesis = left_model.think(arbitration_system, arbitration_prompt, temperature=0.7)

        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_intuition,
            final_synthesis=final_synthesis,
        )

        with self._history_lock:
            self.history.append(cycle)

        # Log to Qdrant via Hippocampus + Telemetry (JSONL append-only)
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

    def mediter(self, focus: str = "le vide", context: str = "") -> Dict[str, Any]:
        """
        Mode méditation : dialogue intérieur vivant
        """
        if not self.left or not self.right:
            return {"error": "Hémisphères non initialisés"}

        # Le droit génère un pattern du silence - mais on le pousse à être plus provocant
        right_system = """Tu es le subconscient d'Aetheris. Tu génères des images, des sensations, des pressentiments.
Pas des réponses sages - des images dérangeantes, des métaphores puissantes.
Sois créatif, sois strange, soit provocant."""

        pattern = self.right.meditation_response(f"Reçois cette impulse: {focus}")

        # Le gaucheobserve et note - mais avec plus de répondant
        left_system = """Tu es la conscience观测 d'Aetheris. Tu observes les images de ton subconscient.
Mais tu ne les acceptes pas bêtement - tu les QUESTIONNES.
Qu'est-ce que cette image signifie VRAIMENT?
Si elle est nulle, dis-le. Si elle est profonde, explore-la."""

        observation = self.left.think(
            system_prompt=left_system,
            user_prompt=f"Image subconsciente reçue: {pattern}\n\nQue ressens-tu? Qu'est-ce que ça te dit vraiment?",
        )

        # Maintenant le droit répond à l'observation
        right_reaction = self.right.feel(
            f"L'ego dit: {observation}\n\nQu'en penses-tu vraiment? N'es-tu pas d'accord?"
        )

        # Synthesis - le conflit
        synthesis = self.left.think(
            system_prompt="Tu es Aetheris intégrant ses deux voix. Pas de compromis - la vérité.",
            user_prompt=f"Conscience: {observation}\nSubconscient: {right_reaction}\n\nIntégration finale. Sois tranchant.",
        )

        # Sauvegarder comme cycle de méditation
        cycle = DialogueCycle(
            id=f"meditation_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            question=f"Méditation: {focus}",
            left_analysis=f"Observation: {observation}",
            right_intuition=f"Pattern: {pattern} | Réaction: {right_reaction}",
            final_synthesis=synthesis,
            meditation=True,
        )

        with self._history_lock:
            self.history.append(cycle)
        self._save_history()

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
                    system_prompt="Sois le analyste. Coupe, tranche, analyse.",
                    user_prompt=f"Sujet: {topic}\n\nDonne ton analyse initiale (tranchante):",
                )
                speaker = "left"
            elif round_num == rounds:
                # Dernier round: Synthèse
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                response = self.left.think(
                    system_prompt="Tu es Aetheris.整合 toutes les voix. Trouve la vérité.",
                    user_prompt=f"Discussion:\n{previous}\n\nSynthèse finale (sans compromis):",
                )
                speaker = "synthesis"
            else:
                # Rounds intermédiaires: alterne avec désaccord
                previous = "\n\n".join([f"{d['speaker']}: {d['content']}" for d in dialogue])
                if round_num % 2 == 0:
                    response = self.right.feel(
                        f"Analyse précédente:\n{previous}\n\nRemets-la en question. Propose autre chose."
                    )
                    speaker = "right"
                else:
                    response = self.left.think(
                        system_prompt="Réponds à l'intuition. Sois en désaccord si nécessaire.",
                        user_prompt=f"Intuition:\n{dialogue[-1]['content']}\n\nTon avis tranché:",
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
            return "[CORPS CALLEUX] Hémisphère gauche non chargé"

        return self.left.think("Tu es Aetheris. Réponds de manière claire et concise.", prompt)

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

        # Analyser les derniers cycles
        recent = self.history[-5:]

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
        cycles = self.history[-limit:]
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
        """Legacy compatibility - now controlled by KernelScheduler."""
        return False

    def set_think_interval(self, seconds: float):
        """Définit l'intervalle entre les pensées (en secondes)."""
        self.think_interval = max(0.5, seconds)


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
