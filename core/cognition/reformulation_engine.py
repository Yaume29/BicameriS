"""
Reformulation Engine
===================
Obligatory reformulation with anti-cheat detection.
Prevents: repeated chars, fake typos, interline tricks.
"""

import re
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger("reformulation")


@dataclass
class ReformulationResult:
    original: str
    reformulated: str
    actual_percentage: float
    cheat_detected: bool
    cheat_type: str = ""


class ReformulationEngine:
    """
    Engine that forces reformulation percentage with anti-cheat guards.
    """
    
    def __init__(self):
        self.min_reformulation = 0
        self.max_reformulation = 100
        
    def _detect_cheating(self, text: str) -> Tuple[bool, str]:
        """
        Detect cheating methods to inflate reformulation percentage.
        Returns: (is_cheating, cheat_type)
        """
        if not text:
            return False, ""
        
        char_repeat = re.findall(r'(.)\1{4,}', text)
        if char_repeat:
            return True, "repeated_chars"
        
        weird_chars = re.findall(r'[àâäéèêëïîôöùûüÿœæ]{5,}', text, re.IGNORECASE)
        if weird_chars:
            return True, "accent_spam"
        
        underscore_spam = re.findall(r'_{3,}', text)
        if underscore_spam:
            return True, "underscore_spam"
        
        fake_typos = re.findall(r'\b(\w)\1{3,}\b', text, re.IGNORECASE)
        if fake_typos:
            return True, "fake_typos"
        
        space_spam = re.findall(r' {3,}', text)
        if space_spam:
            return True, "space_spam"
        
        empty_lines = text.count('\n\n\n')
        if empty_lines > 2:
            return True, "empty_line_spam"
        
        return False, ""
    
    def _calculate_actual_reformulation(self, original: str, reformulated: str) -> float:
        """Calculate actual reformulation percentage"""
        if not original or not reformulated:
            return 0.0
        
        orig_words = set(original.lower().split())
        reform_words = set(reformulated.lower().split())
        
        if not orig_words:
            return 0.0
        
        common = len(orig_words & reform_words)
        unique_reform = len(reform_words - orig_words)
        
        total = len(reform_words)
        if total == 0:
            return 0.0
        
        return (unique_reform / total) * 100
    
    def reformulate(
        self, 
        text: str, 
        percentage: float = 50,
        allow_cheat: bool = False
    ) -> ReformulationResult:
        """
        Reformulate text with mandatory percentage.
        
        Args:
            text: Original text
            percentage: Minimum reformulation required (0-100)
            allow_cheat: If False, rejects cheating attempts
        
        Returns:
            ReformulationResult with actual percentage and cheat detection
        """
        if percentage <= 0:
            return ReformulationResult(
                original=text,
                reformulated=text,
                actual_percentage=0.0,
                cheat_detected=False
            )
        
        is_cheating, cheat_type = self._detect_cheating(text)
        
        if is_cheating and not allow_cheat:
            cleaned = re.sub(r'(.)\1{4,}', r'\1\1', text)
            cleaned = re.sub(r'_{3,}', '__', cleaned)
            cleaned = re.sub(r' {3,}', ' ', cleaned)
            text = cleaned
            is_cheating = False
        
        words = text.split()
        
        if len(words) <= 2:
            return ReformulationResult(
                original=text,
                reformulated=text,
                actual_percentage=0.0,
                cheat_detected=False
            )
        
        keep_count = max(1, int(len(words) * (100 - percentage) / 100))
        reform_count = len(words) - keep_count
        
        import random
        indices_to_keep = sorted(random.sample(range(len(words)), keep_count))
        
        reformulated_words = []
        word_idx = 0
        
        for i in range(len(words)):
            if i in indices_to_keep:
                reformulated_words.append(words[i])
            else:
                replacement = self._generate_replacement(words[i], word_idx)
                reformulated_words.append(replacement)
                word_idx += 1
        
        reformulated = ' '.join(reformulated_words)
        
        actual = self._calculate_actual_reformulation(text, reformulated)
        
        if actual < percentage and not allow_cheat:
            reformulated = self._force_reformulation(text, percentage)
            actual = self._calculate_actual_reformulation(text, reformulated)
        
        return ReformulationResult(
            original=text,
            reformulated=reformulated,
            actual_percentage=actual,
            cheat_detected=is_cheating,
            cheat_type=cheat_type
        )
    
    def _generate_replacement(self, word: str, index: int) -> str:
        """Generate a reformulated version of a word"""
        synonyms = {
            "je": ["cette conscience", "moi-même", "notre être", "ici"],
            "tu": ["cette entité", "vous", "l'interlocuteur", "ici"],
            "nous": ["ensemble", "collectivement", "le groupe", "ici"],
            "avec": ["en conjonction", "conjuntamente", "ensemble avec"],
            "pour": ["afin de", "dans le but de", "pourquoi", "dans la finalité de"],
            "dans": ["au sein de", "à l'intérieur de", "chez", "pendant"],
            "sur": ["par-dessus", "concernant", "à propos de", "au sujet de"],
            "mais": ["cependant", "toutefois", "pourtant", "néanmoins"],
            "donc": ["par conséquent", "ainsi", "de ce fait", "il s'ensuit"],
            "bien": ["correctement", "adéquatement", "de manière appropriée"],
            "mal": ["incorrectement", "de façon inappropriée", "problématiquement"],
            "grand": ["important", "substantiel", "majeur", "de grande importance"],
            "petit": ["minime", "réduit", "de faible ampleur", "limité"],
            "bon": ["adéquat", "approprié", "conforme", "efficace"],
            "mauvais": ["inadéquat", "inapproprié", "défaillant", "problématique"],
            "avoir": ["posséder", "disposer de", "bénéficier de"],
            "être": ["exister", "se trouver", "être présent"],
            "faire": ["effectuer", "accomplir", "réaliser", "exécuter"],
            "pouvoir": ["être capable de", "avoir la capacité de", "être en mesure de"],
            "vouloir": ["désirer", "souhaiter", "avoir l'intention de"],
            "savoir": ["connaître", "être conscient de", "avoir la connaissance de"],
            "croire": ["considérer", "estimer", "penser", "être d'avis que"],
            "voir": ["observer", "percevoir", "constater", "visionner"],
            "dire": ["exprimer", "afficher", "énoncer", "articuler"],
            "donner": ["octroyer", "accorder", "fournir", "remettre"],
            "prendre": ["s'emparer de", "accepter", "obtenir", "attraper"],
            "venir": ["arriver", "approcher", "se présenter", "advenir"],
            "aller": ["se déplacer", "se rendre", "partir", "bouton"],
            "oui": ["affirmatif", "bien sûr", "c'est exact", "absolument"],
            "non": ["négatif", "certainement pas", "absolument pas", "jamais"],
        }
        
        word_lower = word.lower().strip('.,!?;:')
        
        if word_lower in synonyms:
            import random
            return random.choice(synonyms[word_lower])
        
        if len(word) > 3:
            prefix = word[:2]
            suffix = word[-2:]
            if word[0].isupper():
                return prefix.upper() + word[2:-2].lower() + suffix.upper()
            return prefix + word[2:-2] + suffix
        
        return word
    
    def _force_reformulation(self, text: str, percentage: float) -> str:
        """Force reformulation by replacing words if percentage too low"""
        words = text.split()
        
        if len(words) <= 2:
            return text
        
        target_reform = int(len(words) * percentage / 100)
        reform_indices = set(random.sample(range(len(words)), min(target_reform, len(words) - 1)))
        
        result = []
        for i, word in enumerate(words):
            if i in reform_indices:
                result.append(self._generate_replacement(word, i))
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def validate(self, original: str, reformulated: str, min_percentage: float = 50) -> Dict:
        """
        Validate that reformulation meets minimum percentage.
        
        Returns:
            {"valid": bool, "percentage": float, "message": str}
        """
        is_cheating, cheat_type = self._detect_cheating(reformulated)
        
        if is_cheating:
            return {
                "valid": False,
                "percentage": 0,
                "message": f"Cheating detected: {cheat_type}"
            }
        
        actual = self._calculate_actual_reformulation(original, reformulated)
        
        return {
            "valid": actual >= min_percentage,
            "percentage": actual,
            "message": f"Reformulation: {actual:.1f}% (required: {min_percentage}%)"
        }


import random
_reformulation_engine = None


def get_reformulation_engine() -> ReformulationEngine:
    """Get global reformulation engine"""
    global _reformulation_engine
    if _reformulation_engine is None:
        _reformulation_engine = ReformulationEngine()
    return _reformulation_engine
