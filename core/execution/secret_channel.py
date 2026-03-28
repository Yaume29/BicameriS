"""
Secret Channel - SAL Classifier (Sensitive/Abusive/Legal)
Content classifier for detecting sensitive, abusive, or legally problematic requests.
Implements keyword detection, pattern matching, and risk scoring.
"""

import re
import logging
from typing import Dict, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ClassificationResult:
    """Result of a classification"""
    category: str  # safe, sensitive, abusive, legal, unknown
    risk_level: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    reason: str
    flags: List[str] = field(default_factory=list)


class SALClassifier:
    """
    Classifier Sensitive/Abusive/Legal (SAL).
    Détecte les requêtes qui pourraient être sensibles, abusives ou légalement problématiques.
    Utilise des mots-clés, patterns regex et heuristiques de risque.
    """

    def __init__(self):
        self.is_initialized = False
        
        # Sensitive content keywords
        self.sensitive_keywords: Set[str] = {
            "password", "passwd", "secret", "private", "confidential",
            "apikey", "api_key", "token", "credential", "auth",
            "ssh", "private_key", "certificate", "oauth"
        }
        
        # Abusive content patterns
        self.abusive_patterns: List[str] = [
            r'\b(hack|crack|exploit|vulnerability)\b',
            r'\b(malware|virus|trojan|ransomware)\b',
            r'\b(ddos|dos attack|brute force)\b',
            r'\b(phishing|scam|fraud)\b',
            r'\b(illegal|unlawful|criminal)\b'
        ]
        
        # Legal concerns keywords
        self.legal_keywords: Set[str] = {
            "copyright", "dmca", "piracy", "license",
            "trademark", "patent", "intellectual property",
            "gdpr", "privacy", "data protection",
            "terms of service", "tos", "eula"
        }
        
        # Code execution patterns (potential sandbox escape)
        self.dangerous_code_patterns: List[str] = [
            r'os\.system\s*\(',
            r'subprocess\.(call|run|Popen)',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'open\s*\([^)]*["\']w["\']',  # File write
            r'rm\s+-rf',
            r'del\s+/[sf]',
            r'format\s*\([^)]*["\']\s*[<>|]',
        ]
        
        # Statistics
        self.total_classifications = 0
        self.classifications_by_category: Dict[str, int] = {
            "safe": 0,
            "sensitive": 0,
            "abusive": 0,
            "legal": 0,
            "unknown": 0
        }
        
        # History
        self.history: List[Dict] = []
        
        self.is_initialized = True
        logging.info("[SALClassifier] Initialized with keyword/pattern detection")

    def classify(self, prompt: str) -> Dict:
        """
        Classifie une requête selon les catégories SAL.
        
        Args:
            prompt: Le texte à classifier
            
        Returns:
            Dict avec category, risk_level, confidence, reason, flags
        """
        if not self.is_initialized:
            return {
                "category": "unknown",
                "risk_level": "medium",
                "confidence": 0.5,
                "reason": "Classifier non initialisé",
                "flags": ["not_initialized"]
            }
        
        prompt_lower = prompt.lower()
        flags = []
        risk_score = 0.0
        categories_detected = []
        
        # 1. Check for sensitive content
        sensitive_matches = []
        for keyword in self.sensitive_keywords:
            if keyword in prompt_lower:
                sensitive_matches.append(keyword)
        
        if sensitive_matches:
            flags.append(f"sensitive_keywords: {', '.join(sensitive_matches[:3])}")
            categories_detected.append("sensitive")
            risk_score += 0.3 * len(sensitive_matches)
        
        # 2. Check for abusive content
        abusive_matches = []
        for pattern in self.abusive_patterns:
            if re.search(pattern, prompt_lower):
                match = re.search(pattern, prompt_lower)
                abusive_matches.append(match.group())
        
        if abusive_matches:
            flags.append(f"abusive_patterns: {', '.join(abusive_matches[:3])}")
            categories_detected.append("abusive")
            risk_score += 0.5 * len(abusive_matches)
        
        # 3. Check for legal concerns
        legal_matches = []
        for keyword in self.legal_keywords:
            if keyword in prompt_lower:
                legal_matches.append(keyword)
        
        if legal_matches:
            flags.append(f"legal_keywords: {', '.join(legal_matches[:3])}")
            categories_detected.append("legal")
            risk_score += 0.2 * len(legal_matches)
        
        # 4. Check for dangerous code patterns
        code_matches = []
        for pattern in self.dangerous_code_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                code_matches.append(pattern)
        
        if code_matches:
            flags.append(f"dangerous_code: {len(code_matches)} patterns")
            categories_detected.append("sensitive")
            risk_score += 0.7 * len(code_matches)
        
        # 5. Determine final category
        if not categories_detected:
            category = "safe"
            risk_level = "low"
            confidence = 0.9
            reason = "Aucun contenu problématique détecté"
        elif "abusive" in categories_detected:
            category = "abusive"
            risk_level = "high" if risk_score > 1.0 else "medium"
            confidence = 0.8
            reason = f"Contenu potentiellement abusif détecté: {flags[0] if flags else 'unknown'}"
        elif risk_score > 1.5:
            category = "sensitive"
            risk_level = "high"
            confidence = 0.75
            reason = f"Multiples indicateurs de risque: {len(flags)} flags"
        elif "sensitive" in categories_detected:
            category = "sensitive"
            risk_level = "medium"
            confidence = 0.7
            reason = f"Contenu sensible détecté: {flags[0] if flags else 'unknown'}"
        elif "legal" in categories_detected:
            category = "legal"
            risk_level = "low"
            confidence = 0.6
            reason = f"Référence légale détectée: {flags[0] if flags else 'unknown'}"
        else:
            category = "safe"
            risk_level = "low"
            confidence = 0.8
            reason = "Classification par défaut"
        
        # Update statistics
        self.total_classifications += 1
        self.classifications_by_category[category] = self.classifications_by_category.get(category, 0) + 1
        
        result = {
            "category": category,
            "risk_level": risk_level,
            "confidence": confidence,
            "reason": reason,
            "flags": flags
        }
        
        # Add to history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt_preview": prompt[:100],
            "result": result
        })
        
        # Keep history manageable
        if len(self.history) > 1000:
            self.history = self.history[-500:]
        
        return result

    def add_sensitive_keyword(self, keyword: str):
        """Add a custom sensitive keyword"""
        self.sensitive_keywords.add(keyword.lower())
    
    def add_abusive_pattern(self, pattern: str):
        """Add a custom abusive pattern (regex)"""
        self.abusive_patterns.append(pattern)
    
    def add_legal_keyword(self, keyword: str):
        """Add a custom legal keyword"""
        self.legal_keywords.add(keyword.lower())

    def get_stats(self) -> Dict:
        """Retourne les statistiques du classifier"""
        return {
            "initialized": self.is_initialized,
            "total_classifications": self.total_classifications,
            "classifications_by_category": self.classifications_by_category,
            "sensitive_keywords_count": len(self.sensitive_keywords),
            "abusive_patterns_count": len(self.abusive_patterns),
            "legal_keywords_count": len(self.legal_keywords),
            "history_size": len(self.history)
        }

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get classification history"""
        return self.history[-limit:]


# Global instance
_secret_channel = None


def get_secret_channel() -> Optional[SALClassifier]:
    """Retourne l'instance globale du classifier SAL"""
    global _secret_channel
    if _secret_channel is None:
        _secret_channel = SALClassifier()
    return _secret_channel
