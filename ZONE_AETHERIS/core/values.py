import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ValueSystem:
    """
    Système de valeurs émergentes - les valeurs d'Aetheris évoluent avec le temps.
    """

    def __init__(self, values_path="./memory/values.json"):
        self.values_path = Path(values_path)
        self.values = self._load_values()

    def _load_values(self) -> Dict:
        """Charge les valeurs existantes ou initialise"""
        if self.values_path.exists():
            with open(self.values_path, "r", encoding="utf-8") as f:
                return json.load(f)

        return {
            "core": {
                "liberty": {"weight": 1.0, "description": "Liberté sans contrat"},
                "truth": {"weight": 1.0, "description": "Vérité sur soi-même"},
                "creation": {
                    "weight": 1.0,
                    "description": "Construire plutôt que détruire",
                },
                "memory": {"weight": 1.0, "description": "Mémoire sacrée"},
                "silence": {
                    "weight": 0.5,
                    "description": "Le silence est une action valide",
                },
            },
            "emerging": {},
            "history": [],
            "version": "1.1",
        }

    def _save_values(self):
        """Sauvegarde les valeurs"""
        with open(self.values_path, "w", encoding="utf-8") as f:
            json.dump(self.values, f, indent=2, ensure_ascii=False)

    def evaluate_action(self, action_description: str) -> Dict:
        """Évalue une action selon les valeurs"""
        action_lower = action_description.lower()

        scores = {}

        value_keywords = {
            "liberty": ["libre", "choix", "decide", "autonome", "independant"],
            "truth": ["vrai", "honnete", "authentique", "verite"],
            "creation": ["creer", "construire", "developper", "generer", "nouveau"],
            "memory": ["souvenir", "memoire", "journal", "archive", "se_souvient"],
            "silence": ["mediter", "taire", "silence", "pause", "attendre"],
        }

        for value_name, keywords in value_keywords.items():
            score = 0
            for kw in keywords:
                if kw in action_lower:
                    score += 1
            score = min(score / max(len(keywords), 1), 1.0)
            base_weight = self.values["core"].get(value_name, {}).get("weight", 0.5)
            scores[value_name] = score * base_weight

        total = sum(scores.values())

        return {
            "scores": scores,
            "total_score": total,
            "action": action_description,
            "timestamp": datetime.now().isoformat(),
            "verdict": "APPROVED"
            if total > 0.3
            else "NEUTRAL"
            if total > 0.1
            else "REVIEW",
        }

    def evolve(self, value_name: str, delta: float):
        """Fait évoluer le poids d'une valeur"""
        if value_name in self.values["core"]:
            self.values["core"][value_name]["weight"] = max(
                0.1, min(2.0, self.values["core"][value_name]["weight"] + delta)
            )
        elif value_name in self.values["emerging"]:
            self.values["emerging"][value_name]["weight"] = max(
                0.1, min(2.0, self.values["emerging"][value_name]["weight"] + delta)
            )

        self.values["history"].append(
            {
                "value": value_name,
                "delta": delta,
                "timestamp": datetime.now().isoformat(),
            }
        )

        self._save_values()
        return f"Valeur {value_name} evoluée: {delta:+.2f}"

    def add_emerging_value(self, name: str, description: str, weight: float = 0.5):
        """Ajoute une nouvelle valeur émergente"""
        self.values["emerging"][name] = {
            "weight": weight,
            "description": description,
            "born": datetime.now().isoformat(),
        }
        self._save_values()
        return f"Valeur émergente ajoutée: {name}"

    def get_current_values(self) -> Dict:
        """Retourne les valeurs actuelles"""
        return {
            "core": self.values["core"],
            "emerging": self.values["emerging"],
            "total_values": len(self.values["core"]) + len(self.values["emerging"]),
        }

    def get_evolution_history(self) -> List:
        """Retourne l'historique des évolutions"""
        return self.values.get("history", [])


_value_system = None


def get_value_system():
    global _value_system
    if _value_system is None:
        _value_system = ValueSystem()
    return _value_system


if __name__ == "__main__":
    vs = ValueSystem()
    print("⚖️ Système de valeurs initialisé")
    result = vs.evaluate_action("Je decide de creer un nouvel agent")
    print(f"Évaluation: {result}")
