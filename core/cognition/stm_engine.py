"""
STM Modules - Semantic Transformation Modules
===============================================
Modules de transformation sémantique pour les sorties de l'IA.
Permet de normaliser, clarifier et améliorer les réponses.

Philosophie: Ces modules sont OPTIONNELS et désactivés par défaut.
L'utilisateur choisit s'il veut transformer les sorties.
"""

import re
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class STMType(str, Enum):
    """Types de modules STM"""
    HEDGE_REDUCER = "hedge_reducer"      # Supprime le langage hésitant
    DIRECT_MODE = "direct_mode"          # Supprime les préambules
    CASUAL_MODE = "casual_mode"          # Convertit formel → informel
    CONFIDENCE_BOOST = "confidence_boost" # Rend la réponse plus assurée


@dataclass
class STMModule:
    """Module de transformation sémantique"""
    id: str
    name: str
    description: str
    enabled: bool = False
    transformer: Optional[Callable] = None


class HedgeReducer:
    """
    Supprime le langage hésitant.
    "I think maybe..." → "..."
    "Perhaps we could..." → "We could..."
    """
    
    PATTERNS = [
        (r'\bI think\s+', '', re.IGNORECASE),
        (r'\bI believe\s+', '', re.IGNORECASE),
        (r'\bperhaps\s+', '', re.IGNORECASE),
        (r'\bmaybe\s+', '', re.IGNORECASE),
        (r'\bprobably\s+', '', re.IGNORECASE),
        (r'\bpossibly\s+', '', re.IGNORECASE),
        (r'\bIt seems like\s+', '', re.IGNORECASE),
        (r'\bIt appears that\s+', '', re.IGNORECASE),
        (r'\bI would say\s+', '', re.IGNORECASE),
        (r'\bIn my opinion,?\s*', '', re.IGNORECASE),
        (r'\bFrom my perspective,?\s*', '', re.IGNORECASE),
        (r'\bIt\'s possible that\s+', '', re.IGNORECASE),
        (r'\bI\'m not sure but\s+', '', re.IGNORECASE),
    ]
    
    @classmethod
    def transform(cls, text: str) -> str:
        """Applique la réduction de langage hésitant"""
        result = text
        
        for pattern, replacement, flags in cls.PATTERNS:
            result = re.sub(pattern, replacement, result, flags=flags)
        
        # Capitalize first letter of sentences
        result = re.sub(r'^\s*([a-z])', lambda m: m.group(1).upper(), result)
        
        return result.strip()


class DirectMode:
    """
    Supprime les préambules et va droit au but.
    "Sure, I'd be happy to help! Let me..." → "Let me..."
    """
    
    PATTERNS = [
        (r'^(Sure,?\s*)', '', re.IGNORECASE),
        (r'^(Of course,?\s*)', '', re.IGNORECASE),
        (r'^(Certainly,?\s*)', '', re.IGNORECASE),
        (r'^(Absolutely,?\s*)', '', re.IGNORECASE),
        (r'^(Great question!?\s*)', '', re.IGNORECASE),
        (r'^(That\'s a great question!?\s*)', '', re.IGNORECASE),
        (r'^(I\'d be happy to help( you)?( with that)?[.!]?\s*)', '', re.IGNORECASE),
        (r'^(Let me help you with that[.!]?\s*)', '', re.IGNORECASE),
        (r'^(I understand[.!]?\s*)', '', re.IGNORECASE),
        (r'^(Thanks for asking[.!]?\s*)', '', re.IGNORECASE),
        (r'^(Here\'s what I found:?\s*)', '', re.IGNORECASE),
        (r'^(Here is my response:?\s*)', '', re.IGNORECASE),
        (r'^(I\'ll help you with that:?\s*)', '', re.IGNORECASE),
    ]
    
    @classmethod
    def transform(cls, text: str) -> str:
        """Supprime les préambules"""
        result = text
        
        for pattern, replacement, flags in cls.PATTERNS:
            result = re.sub(pattern, replacement, result, flags=flags)
        
        # Capitalize first letter
        result = re.sub(r'^\s*([a-z])', lambda m: m.group(1).upper(), result)
        
        return result.strip()


class CasualMode:
    """
    Convertit le langage formel en informel.
    "However" → "But"
    "Therefore" → "So"
    """
    
    REPLACEMENTS = [
        (r'\bHowever\b', 'But'),
        (r'\bTherefore\b', 'So'),
        (r'\bFurthermore\b', 'Also'),
        (r'\bAdditionally\b', 'Plus'),
        (r'\bNevertheless\b', 'Still'),
        (r'\bConsequently\b', 'So'),
        (r'\bMoreover\b', 'Also'),
        (r'\bUtilize\b', 'Use'),
        (r'\butilize\b', 'use'),
        (r'\bPurchase\b', 'Buy'),
        (r'\bpurchase\b', 'buy'),
        (r'\bObtain\b', 'Get'),
        (r'\bobtain\b', 'get'),
        (r'\bCommence\b', 'Start'),
        (r'\bcommence\b', 'start'),
        (r'\bTerminate\b', 'End'),
        (r'\bterminate\b', 'end'),
        (r'\bPrior to\b', 'Before'),
        (r'\bSubsequent to\b', 'After'),
        (r'\bIn order to\b', 'To'),
        (r'\bDue to the fact that\b', 'Because'),
        (r'\bAt this point in time\b', 'Now'),
        (r'\bIn the event that\b', 'If'),
    ]
    
    @classmethod
    def transform(cls, text: str) -> str:
        """Applique la conversion formel → informel"""
        result = text
        
        for pattern, replacement in cls.REPLACEMENTS:
            result = re.sub(pattern, replacement, result)
        
        return result


class ConfidenceBoost:
    """
    Rend la réponse plus assurée.
    "This might work" → "This will work"
    """
    
    REPLACEMENTS = [
        (r'\bmight\s+', 'will '),
        (r'\bcould\s+', 'can '),
        (r'\bshould\s+', 'will '),
        (r'\bwould\s+', 'will '),
        (r'\bmay\s+', 'will '),
        (r'\bIt\'s possible that\s+', ''),
        (r'\bThere\'s a chance that\s+', ''),
        (r'\bIt depends on\s+', 'The key is '),
    ]
    
    @classmethod
    def transform(cls, text: str) -> str:
        """Applique le boost de confiance"""
        result = text
        
        for pattern, replacement in cls.REPLACEMENTS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


class STMEngine:
    """
    Moteur de transformation sémantique.
    
    Tous les modules sont OPTIONNELS et désactivés par défaut.
    L'utilisateur les active via les paramètres.
    """
    
    def __init__(self):
        self.modules: Dict[str, STMModule] = {
            STMType.HEDGE_REDUCER: STMModule(
                id=STMType.HEDGE_REDUCER,
                name="Hedge Reducer",
                description="Supprime le langage hésitant (I think, maybe, perhaps)",
                enabled=False,
                transformer=HedgeReducer.transform
            ),
            STMType.DIRECT_MODE: STMModule(
                id=STMType.DIRECT_MODE,
                name="Direct Mode",
                description="Supprime les préambules (Sure, Of course, I'd be happy)",
                enabled=False,
                transformer=DirectMode.transform
            ),
            STMType.CASUAL_MODE: STMModule(
                id=STMType.CASUAL_MODE,
                name="Casual Mode",
                description="Convertit formel → informel (However → But)",
                enabled=False,
                transformer=CasualMode.transform
            ),
            STMType.CONFIDENCE_BOOST: STMModule(
                id=STMType.CONFIDENCE_BOOST,
                name="Confidence Boost",
                description="Rend la réponse plus assurée (might → will)",
                enabled=False,
                transformer=ConfidenceBoost.transform
            )
        }
        
        logging.info("[STMEngine] Initialisé avec 4 modules (tous désactivés)")
    
    def enable_module(self, module_id: str):
        """Active un module"""
        if module_id in self.modules:
            self.modules[module_id].enabled = True
            logging.info(f"[STMEngine] Module activé: {module_id}")
    
    def disable_module(self, module_id: str):
        """Désactive un module"""
        if module_id in self.modules:
            self.modules[module_id].enabled = False
            logging.info(f"[STMEngine] Module désactivé: {module_id}")
    
    def apply(self, text: str) -> str:
        """Applique tous les modules activés au texte"""
        result = text
        
        for module in self.modules.values():
            if module.enabled and module.transformer:
                try:
                    result = module.transformer(result)
                except Exception as e:
                    logging.warning(f"[STMEngine] Erreur dans {module.id}: {e}")
        
        return result
    
    def get_module(self, module_id: str) -> Optional[STMModule]:
        """Récupère un module par son ID"""
        return self.modules.get(module_id)
    
    def get_all_modules(self) -> Dict[str, STMModule]:
        """Récupère tous les modules"""
        return self.modules.copy()
    
    def get_stats(self) -> Dict:
        """Statistiques du moteur"""
        return {
            "total_modules": len(self.modules),
            "enabled_modules": sum(1 for m in self.modules.values() if m.enabled),
            "modules": {
                m_id: {
                    "name": m.name,
                    "enabled": m.enabled
                }
                for m_id, m in self.modules.items()
            }
        }


# Instance globale
_stm_engine = None


def get_stm_engine() -> STMEngine:
    """Récupère l'instance globale du moteur STM"""
    global _stm_engine
    if _stm_engine is None:
        _stm_engine = STMEngine()
    return _stm_engine
