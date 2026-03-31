"""
AutoTune Engine - Context-Adaptive Parameter Tuning
=====================================================
Moteur de paramètres adaptatifs basé sur le contexte.
Analyse le texte et ajuste automatiquement les paramètres d'inférence.

Philosophie: Ce module est OPTIONNEL mais peut être activé par défaut.
Il optimise simplement les paramètres - pas de transformation du contenu.
"""

import re
import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


BASE_DIR = Path(__file__).parent.parent.parent.absolute()
AUTOTUNE_DIR = BASE_DIR / "storage" / "autotune"


class ContextType(str, Enum):
    """Types de contexte détectés"""
    CODE = "code"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    CONVERSATIONAL = "conversational"
    CHAOTIC = "chaotic"
    BALANCED = "balanced"


@dataclass
class InferenceParams:
    """Paramètres d'inférence"""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    frequency_penalty: float = 0.1
    presence_penalty: float = 0.1
    repetition_penalty: float = 1.0


@dataclass
class AutoTuneResult:
    """Résultat de l'auto-tuning"""
    context: ContextType
    confidence: float
    params: InferenceParams
    reasoning: str


class AutoTuneEngine:
    """
    Moteur de paramètres adaptatifs.
    
    Analyse le contexte de la requête et ajuste automatiquement:
    - temperature
    - top_p
    - top_k
    - frequency_penalty
    - presence_penalty
    - repetition_penalty
    """
    
    # Profils de stratégie
    STRATEGY_PROFILES: Dict[str, InferenceParams] = {
        "precise": InferenceParams(
            temperature=0.2,
            top_p=0.85,
            top_k=30,
            frequency_penalty=0.3,
            presence_penalty=0.1,
            repetition_penalty=1.1
        ),
        "balanced": InferenceParams(
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            repetition_penalty=1.0
        ),
        "creative": InferenceParams(
            temperature=1.1,
            top_p=0.95,
            top_k=80,
            frequency_penalty=0.4,
            presence_penalty=0.6,
            repetition_penalty=1.15
        ),
        "chaotic": InferenceParams(
            temperature=1.6,
            top_p=0.98,
            top_k=100,
            frequency_penalty=0.7,
            presence_penalty=0.8,
            repetition_penalty=1.25
        ),
    }
    
    # Patterns de détection de contexte
    CONTEXT_PATTERNS: Dict[str, List[str]] = {
        ContextType.CODE: [
            r'def\s+', r'class\s+', r'function\s+', r'import\s+',
            r'console\.log', r'print\(', r'return\s+', r'if\s*\(',
            r'for\s*\(', r'while\s*\(', r'try\s*\{', r'catch\s*\(',
            r'async\s+', r'await\s+', r'const\s+', r'let\s+', r'var\s+',
            r'public\s+', r'private\s+', r'static\s+', r'void\s+',
            r'#include', r'std::', r'System\.', r'println\('
        ],
        ContextType.CREATIVE: [
            r'story', r'poem', r'creative', r'imagine', r'fiction',
            r'narrative', r'character', r'setting', r'plot',
            r'describe', r'vivid', r'emotion', r'feeling',
            r'once upon', r'chapter', r'verse', r'stanza'
        ],
        ContextType.ANALYTICAL: [
            r'analyze', r'compare', r'evaluate', r'research',
            r'explain', r'describe', r'summarize', r'conclude',
            r'data', r'statistics', r'metric', r'benchmark',
            r'hypothesis', r'theory', r'evidence', r'proof',
            r'pros and cons', r'advantages', r'disadvantages'
        ],
        ContextType.CONVERSATIONAL: [
            r'hello', r'hi\b', r'hey', r'how are you',
            r'thanks', r'thank you', r'please', r'sorry',
            r'can you help', r'what do you think', r'opinion',
            r'recommend', r'suggest', r'advice'
        ],
        ContextType.CHAOTIC: [
            r'random', r'crazy', r'wild', r'absurd', r'silly',
            r'joke', r'funny', r'humor', r'meme',
            r'whatever', r'surprise me', r'shock me', r'chaos'
        ],
    }
    
    # Profils appris (EMA)
    LEARNED_PROFILES_FILE = AUTOTUNE_DIR / "learned_profiles.json"
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.learned_profiles: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        
        AUTOTUNE_DIR.mkdir(parents=True, exist_ok=True)
        self._load_learned_profiles()
        
        logging.info(f"[AutoTune] Initialisé (enabled={enabled})")
    
    def _load_learned_profiles(self):
        """Charge les profils appris"""
        if self.LEARNED_PROFILES_FILE.exists():
            try:
                with open(self.LEARNED_PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.learned_profiles = json.load(f)
            except Exception as e:
                logging.warning(f"[AutoTune] Erreur chargement profils: {e}")
                self.learned_profiles = {}
    
    def _save_learned_profiles(self):
        """Sauvegarde les profils appris"""
        try:
            with open(self.LEARNED_PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.learned_profiles, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.warning(f"[AutoTune] Erreur sauvegarde profils: {e}")
    
    def detect_context(self, text: str) -> Tuple[ContextType, float]:
        """
        Détecte le type de contexte du texte.
        
        Returns:
            Tuple (context_type, confidence)
        """
        text_lower = text.lower()
        scores: Dict[str, float] = {}
        
        for context_type, patterns in self.CONTEXT_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                score += len(matches)
            scores[context_type] = score
        
        # Normaliser les scores
        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            for ctx in scores:
                scores[ctx] /= max_score
        
        # Trouver le contexte dominant
        if max(scores.values()) > 0:
            dominant = max(scores, key=scores.get)
            confidence = scores[dominant]
            return ContextType(dominant), confidence
        
        # Par défaut: balanced
        return ContextType.BALANCED, 0.5
    
    def get_optimal_params(self, context: ContextType) -> InferenceParams:
        """
        Retourne les paramètres optimaux pour un contexte donné.
        Prend en compte les profils appris.
        """
        # Mapping context → strategy
        context_to_strategy = {
            ContextType.CODE: "precise",
            ContextType.CREATIVE: "creative",
            ContextType.ANALYTICAL: "precise",
            ContextType.CONVERSATIONAL: "balanced",
            ContextType.CHAOTIC: "chaotic",
            ContextType.BALANCED: "balanced",
        }
        
        strategy = context_to_strategy.get(context, "balanced")
        params = self.STRATEGY_PROFILES[strategy]
        
        # Appliquer les ajustements appris
        if context.value in self.learned_profiles:
            learned = self.learned_profiles[context.value]
            params = InferenceParams(
                temperature=max(0.1, min(2.0, params.temperature + learned.get("temp_adj", 0))),
                top_p=max(0.1, min(1.0, params.top_p + learned.get("top_p_adj", 0))),
                top_k=max(1, min(200, params.top_k + learned.get("top_k_adj", 0))),
                frequency_penalty=params.frequency_penalty,
                presence_penalty=params.presence_penalty,
                repetition_penalty=params.repetition_penalty
            )
        
        return params
    
    def tune(self, text: str) -> AutoTuneResult:
        """
        Analyse le texte et retourne les paramètres optimaux.
        """
        if not self.enabled:
            return AutoTuneResult(
                context=ContextType.BALANCED,
                confidence=0.5,
                params=self.STRATEGY_PROFILES["balanced"],
                reasoning="AutoTune désactivé - paramètres par défaut"
            )
        
        context, confidence = self.detect_context(text)
        params = self.get_optimal_params(context)
        
        reasoning = f"Contexte détecté: {context.value} (confiance: {confidence:.1%}). "
        reasoning += f"Paramètres: temp={params.temperature:.1f}, top_p={params.top_p:.2f}"
        
        result = AutoTuneResult(
            context=context,
            confidence=confidence,
            params=params,
            reasoning=reasoning
        )
        
        # Historique
        self.history.append({
            "text_preview": text[:100],
            "context": context.value,
            "confidence": confidence,
            "params": {
                "temperature": params.temperature,
                "top_p": params.top_p,
                "top_k": params.top_k
            }
        })
        
        if len(self.history) > 100:
            self.history = self.history[-50:]
        
        return result
    
    def feedback(self, context: str, rating: int):
        """
        Enregistre un feedback utilisateur pour améliorer les paramètres.
        rating: 1 = positif, -1 = négatif
        """
        if context not in self.learned_profiles:
            self.learned_profiles[context] = {"temp_adj": 0, "top_p_adj": 0, "top_k_adj": 0, "count": 0}
        
        profile = self.learned_profiles[context]
        
        # EMA adjustment
        alpha = 0.1  # Learning rate
        if rating > 0:
            profile["temp_adj"] = profile.get("temp_adj", 0) * (1 - alpha) + 0.05 * alpha
        else:
            profile["temp_adj"] = profile.get("temp_adj", 0) * (1 - alpha) - 0.05 * alpha
        
        profile["count"] = profile.get("count", 0) + 1
        
        self._save_learned_profiles()
    
    def enable(self):
        """Active AutoTune"""
        self.enabled = True
        logging.info("[AutoTune] ACTIVÉ")
    
    def disable(self):
        """Désactive AutoTune"""
        self.enabled = False
        logging.info("[AutoTune] DÉSACTIVÉ")
    
    def get_stats(self) -> Dict:
        """Statistiques du moteur"""
        return {
            "enabled": self.enabled,
            "history_size": len(self.history),
            "learned_profiles": len(self.learned_profiles),
            "contexts_detected": {
                ctx.value: sum(1 for h in self.history if h["context"] == ctx.value)
                for ctx in ContextType
            }
        }


# Instance globale
_autotune_engine = None


def get_autotune_engine(enabled: bool = False) -> AutoTuneEngine:
    """Récupère l'instance globale du moteur AutoTune"""
    global _autotune_engine
    if _autotune_engine is None:
        _autotune_engine = AutoTuneEngine(enabled=enabled)
    return _autotune_engine
