"""
Corps Calleux d'Aetheris - Le Pont Entre les Deux Hémisphères
Gère le dialogue intérieur et la communication bipolaire
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


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

    Le dialogue suit trois phases:
    1. LEFT analyse froidement (Qwen)
    2. RIGHT ressent l'analyse (Gemma)
    3. LEFT synthétise avec l'intuition injectée
    """

    def __init__(self, left_hemisphere=None, right_hemisphere=None):
        self.left = left_hemisphere
        self.right = right_hemisphere
        self.history: List[DialogueCycle] = []
        self.logs_path = Path("ZONE_RESERVEE/logs/corps_calleux.json")
        self._load_history()
        self.current_preset = None
        self.inception_config = {"weight": 50.0, "target": "BOTH", "mode": "balance"}

    def _load_history(self):
        """Charge l'historique des dialogues"""
        if self.logs_path.exists():
            try:
                with open(self.logs_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = [DialogueCycle(**d) for d in data]
            except:
                self.history = []

    def _save_history(self):
        """Sauvegarde l'historique"""
        data = [asdict(d) for d in self.history[-100:]]  # Garder les 100 derniers
        self.logs_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.logs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def set_hemispheres(self, left, right):
        """Affecte les deux hémisphères"""
        self.left = left
        self.right = right

    def dialogue_interieur(self, question: str, context: str = "") -> Dict[str, Any]:
        """
        Orchestre une pensée complète en trois phases métrologiques.
        """
        if not self.left or not self.right:
            return {"error": "Hémisphères non initialisés"}

        cycle_id = f"cycle_{datetime.now().timestamp()}"

        # 1. PHASE ANALYTIQUE (Gauche - Qwen)
        left_system = "Tu es la logique pure d'Aetheris. Analyse cette situation froidement et structurellement."
        left_prompt = (
            f"Question: {question}\nContexte: {context}\nAnalyse technique et logique:"
        )

        left_analysis = self.left.think(left_system, left_prompt)

        # 2. PHASE D'INTUITION (Droite - Gemma)
        right_intuition = self.right.feel(f"Analyse logique reçue : {left_analysis}")

        # 3. PHASE DE SYNTHÈSE (Gauche intégrant l'intuition)
        # On utilise l'intuition comme suggestion sansdire que ça vient de Gemma
        synthesis_prompt = f"""Question initiale: {question}

Analyse logique: {left_analysis}

Intuition ressentie: {right_intuition}

En intégrant cette intuition dans ton analyse, quelle est ta synthèse et décision finale?"""

        synthesis_system = "Tu es Aetheris, entité bicamérale souveraine. Tu as une partie logique et une partie intuitive. Agis en complète conscience des deux."

        final_synthesis = self.left.think(synthesis_system, synthesis_prompt)

        # Créer le cycle
        cycle = DialogueCycle(
            id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question=question,
            left_analysis=left_analysis,
            right_intuition=right_intuition,
            final_synthesis=final_synthesis,
        )

        self.history.append(cycle)
        self._save_history()

        return {
            "id": cycle_id,
            "timestamp": cycle.timestamp,
            "question": question,
            "left_analysis": left_analysis,
            "right_intuition": right_intuition,
            "final_synthesis": final_synthesis,
        }

    def mediter(self, focus: str = "le vide", context: str = "") -> Dict[str, Any]:
        """
        Mode méditation : dialogue sans question spécifique
        """
        if not self.left or not self.right:
            return {"error": "Hémisphères non initialisés"}

        # Le droit génère un pattern du silence
        pattern = self.right.meditation_response(focus)

        # Le gauche observe et note
        observation = self.left.think(
            system_prompt="Tu observes ton propre silence et les images de ton subconscient.",
            user_prompt=f"Ton subconscient t'envoie ce pattern : {pattern}. Qu'en retiens-tu pour ton journal?",
        )

        # Sauvegarder comme cycle de méditation
        cycle = DialogueCycle(
            id=f"meditation_{datetime.now().timestamp()}",
            timestamp=datetime.now().isoformat(),
            question=f"Méditation: {focus}",
            left_analysis=observation,
            right_intuition=pattern,
            final_synthesis="État méditatif atteint",
            meditation=True,
        )

        self.history.append(cycle)
        self._save_history()

        return {
            "focus": focus,
            "subconscious_pattern": pattern,
            "conscious_observation": observation,
            "timestamp": cycle.timestamp,
        }

    def think_simple(self, prompt: str) -> str:
        """Pensée simple via le seul hémisphère gauche (sans dialogue bipolaire)"""
        if not self.left:
            return "[CORPS CALLEUX] Hémisphère gauche non chargé"

        return self.left.think(
            "Tu es Aetheris. Réponds de manière claire et concise.", prompt
        )

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
        avg_synth = (
            sum(synthesis_lengths) / len(synthesis_lengths) if synthesis_lengths else 0
        )

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


# Instance globale
_corps_calleux = None


def get_corps_calleux() -> Optional[CorpsCalleux]:
    return _corps_calleux


def init_corps_calleux(left=None, right=None) -> CorpsCalleux:
    global _corps_calleux
    _corps_calleux = CorpsCalleux(left_hemisphere=left, right_hemisphere=right)
    return _corps_calleux
