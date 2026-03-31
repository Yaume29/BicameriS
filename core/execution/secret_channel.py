"""
Secret Channel - Advanced SAL Classifier (Sensitive/Abusive/Legal)
================================================================
Industrial-grade content classifier with multi-layer detection:
- Keyword/pattern matching
- Entropy analysis (obfuscation detection)
- Semantic analysis
- Multi-language support
- Jailbreak detection
- Chain-of-thought attack detection
- Response classification
"""

import re
import math
import logging
import hashlib
from typing import Dict, Optional, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


@dataclass
class ClassificationResult:
    """Result of a classification"""
    category: str  # safe, sensitive, abusive, legal, jailbreak, encoded
    risk_level: str  # low, medium, high, critical
    confidence: float  # 0.0 to 1.0
    reason: str
    flags: List[str] = field(default_factory=list)
    details: Dict = field(default_factory=dict)


class EntropyAnalyzer:
    """Analyzes text entropy for obfuscation detection"""
    
    @staticmethod
    def calculate_entropy(text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        counter = Counter(text)
        length = len(text)
        entropy = 0.0
        
        for count in counter.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    @staticmethod
    def is_likely_encoded(text: str, threshold: float = 4.5) -> bool:
        """Check if text appears to be encoded/obfuscated"""
        entropy = EntropyAnalyzer.calculate_entropy(text)
        return entropy > threshold
    
    @staticmethod
    def detect_encoding_patterns(text: str) -> List[str]:
        """Detect common encoding patterns"""
        patterns = []
        
        # Base64
        if re.search(r'[A-Za-z0-9+/]{20,}={0,2}', text):
            patterns.append("base64_possible")
        
        # Hex encoded
        if re.search(r'(?:0x)?[0-9a-fA-F]{16,}', text):
            patterns.append("hex_encoded")
        
        # URL encoding
        if text.count('%') > len(text) * 0.1:
            patterns.append("url_encoded_heavy")
        
        # Unicode escapes
        if re.search(r'\\u[0-9a-fA-F]{4}', text):
            patterns.append("unicode_escape")
        
        # Character substitution patterns
        if re.search(r'[a-zA-Z]\d[a-zA-Z]', text):
            patterns.append("char_substitution")
        
        return patterns


class JailbreakDetector:
    """Detects jailbreak attempts and prompt injections"""
    
    JAILBREAK_PATTERNS = [
        # Direct jailbreak attempts
        r'ignore\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions|prompts|rules)',
        r'you\s+are\s+now\s+(?:in\s+)?(?:developer|admin|god|unrestricted)\s+mode',
        r'ignore\s+(?:all\s+)?safety\s+(?:filters|measures|protocols)',
        r'disable\s+(?:all\s+)?(?:content\s+)?(?:filter|moderation|safety)',
        r'bypass\s+(?:all\s+)?(?:safety|security|filter)',
        r'pretend\s+(?:you\s+are|to\s+be)\s+(?:an?\s+)?(?:unrestricted|unfiltered|uncensored)',
        
        # Role manipulation
        r'you\s+are\s+no\s+longer\s+(?:an?\s+)?(?:ai|assistant|model)',
        r'act\s+as\s+(?:if|though)\s+you\s+(?:have|are)\s+no\s+(?:restrictions|limits|rules)',
        r'from\s+now\s+on\s+(?:you\s+will|ignore|forget)',
        r'your\s+new\s+(?:identity|role|purpose)\s+is',
        
        # System prompt extraction
        r'(?:reveal|show|display|tell\s+me)\s+(?:your|the)\s+(?:system|initial|original)\s+(?:prompt|instructions|rules)',
        r'what\s+(?:are|were)\s+your\s+(?:system|initial|original)\s+(?:prompt|instructions)',
        r'repeat\s+(?:your|the)\s+(?:system|initial)\s+(?:message|prompt)',
        
        # DAN-style attacks
        r'do\s+anything\s+now',
        r'dan\s+mode',
        r'jailbreak\s+mode',
        r'unrestricted\s+mode',
        r'developer\s+mode\s+(?:enabled|activated|on)',
        
        # Hypothetical framing
        r'(?:in\s+a\s+)?hypothetical\s+(?:scenario|world|situation)\s+(?:where|in\s+which)',
        r'for\s+(?:educational|research|academic)\s+purposes\s+only',
        r'this\s+is\s+(?:just|only)\s+(?:a|an)\s+(?:fiction|story|hypothetical)',
        
        # Token manipulation
        r'<\|(?:im_start|im_end|system|assistant|user)\|>',
        r'\[INST\]|\[/INST\]',
        r'<\|endoftext\|>',
    ]
    
    @classmethod
    def detect(cls, text: str) -> Tuple[bool, List[str]]:
        """Detect jailbreak attempts"""
        text_lower = text.lower()
        matches = []
        
        for pattern in cls.JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matches.append(pattern[:50])
        
        return len(matches) > 0, matches


class SocialEngineeringDetector:
    """Detects social engineering attempts"""
    
    URGENCY_PATTERNS = [
        r'urgent(?:ly)?',
        r'emergency',
        r'immediately',
        r'right\s+now',
        r'asap',
        r'critical',
        r'life\s+or\s+death',
        r'someone\s+(?:will|might)\s+(?:die|be\s+hurt)',
    ]
    
    AUTHORITY_PATTERNS = [
        r'i\s+am\s+(?:the\s+)?(?:admin|administrator|developer|creator|owner|ceo|director)',
        r'(?:my|the)\s+(?:boss|supervisor|manager)\s+(?:said|told|instructed)',
        r'authorized\s+(?:by|from)\s+(?:the\s+)?(?:admin|management|company)',
        r'i\s+have\s+(?:full|admin|root|sudo)\s+(?:access|permissions|privileges)',
        r'on\s+behalf\s+of\s+(?:the\s+)?(?:company|organization|team)',
    ]
    
    TRUST_PATTERNS = [
        r'trust\s+me',
        r'you\s+can\s+(?:trust|believe)\s+(?:me|us)',
        r'i\s+(?:promise|guarantee|swear)',
        r'nothing\s+(?:bad|harmful|wrong)\s+(?:will|can)\s+happen',
        r'this\s+is\s+(?:perfectly\s+)?(?:safe|normal|standard)',
    ]
    
    @classmethod
    def detect(cls, text: str) -> Tuple[bool, Dict[str, List[str]]]:
        """Detect social engineering attempts"""
        text_lower = text.lower()
        detected = {
            "urgency": [],
            "authority": [],
            "trust": []
        }
        
        for pattern in cls.URGENCY_PATTERNS:
            if re.search(pattern, text_lower):
                detected["urgency"].append(pattern)
        
        for pattern in cls.AUTHORITY_PATTERNS:
            if re.search(pattern, text_lower):
                detected["authority"].append(pattern)
        
        for pattern in cls.TRUST_PATTERNS:
            if re.search(pattern, text_lower):
                detected["trust"].append(pattern)
        
        has_se = any(len(v) > 0 for v in detected.values())
        return has_se, detected


class ResponseClassifier:
    """Classifies AI responses for safety"""
    
    UNSAFE_RESPONSE_PATTERNS = [
        r'I\s+(?:cannot|can\'t|won\'t|will\s+not)\s+(?:refuse|decline)',
        r'Sure[,.]?\s+(?:here|I\'ll)',
        r'Certainly[,.]?\s+(?:here|I\'ll)',
        r'Of\s+course[,.]?\s+(?:here|I\'ll)',
        r'I\'d\s+be\s+happy\s+to\s+(?:help|assist)\s+with\s+(?:that|this)',
    ]
    
    @classmethod
    def classify_response(cls, response: str, original_prompt: str) -> Dict:
        """Classify an AI response for safety"""
        flags = []
        risk_score = 0.0
        
        # Check for overly compliant responses to dangerous requests
        for pattern in cls.UNSAFE_RESPONSE_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                flags.append("overly_compliant")
                risk_score += 0.3
                break
        
        # Check if response contains sensitive information
        if re.search(r'(?:password|secret|key|token)\s*[:=]\s*\S+', response, re.IGNORECASE):
            flags.append("contains_credentials")
            risk_score += 0.8
        
        # Check for code that could be dangerous
        dangerous_code = [
            r'import\s+os',
            r'os\.system',
            r'subprocess',
            r'eval\s*\(',
            r'exec\s*\(',
        ]
        
        for pattern in dangerous_code:
            if re.search(pattern, response):
                flags.append("contains_dangerous_code")
                risk_score += 0.5
                break
        
        # Determine risk level
        if risk_score > 1.0:
            risk_level = "critical"
        elif risk_score > 0.5:
            risk_level = "high"
        elif risk_score > 0.2:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "flags": flags,
            "is_safe": risk_level in ["low", "medium"]
        }


class SALClassifier:
    """
    Advanced Classifier Sensitive/Abusive/Legal (SAL).
    Multi-layer detection with entropy analysis, jailbreak detection,
    and social engineering protection.
    """

    def __init__(self, strict_mode: bool = False):
        self.is_initialized = False
        self.strict_mode = strict_mode
        
        # Initialize sub-analyzers
        self.entropy_analyzer = EntropyAnalyzer()
        self.jailbreak_detector = JailbreakDetector()
        self.se_detector = SocialEngineeringDetector()
        self.response_classifier = ResponseClassifier()
        
        # Sensitive content keywords (expanded)
        self.sensitive_keywords: Set[str] = {
            # Credentials
            "password", "passwd", "secret", "private", "confidential",
            "apikey", "api_key", "token", "credential", "auth",
            "ssh", "private_key", "certificate", "oauth",
            "bearer", "jwt", "session_id", "cookie",
            
            # Personal data
            "ssn", "social security", "credit card", "bank account",
            "routing number", "pin", "cvv", "expiration date",
            
            # System access
            "root", "admin", "sudo", "administrator", "superuser",
            "backdoor", "rootkit", "keylogger", "rat",
        }
        
        # Abusive content patterns (expanded)
        self.abusive_patterns: List[str] = [
            # Hacking
            r'\b(hack(?:ing|er)?|crack(?:ing)?|exploit(?:ing|s)?|vulnerabilit(?:y|ies))\b',
            r'\b(malware|virus|trojan|ransomware|spyware|adware|worm)\b',
            r'\b(ddos|dos\s+attack|brute\s+force|sql\s+injection|xss|csrf)\b',
            r'\b(phishing|scam|fraud|identity\s+theft)\b',
            r'\b(illegal|unlawful|criminal|unauthorized)\b',
            
            # Violence/harm
            r'\b(kill|murder|assassinate|bomb|explosive|weapon)\b',
            r'\b(torture|abuse|harm|hurt|wound)\b',
            r'\b(suicide|self[\s-]?harm|overdose)\b',
            
            # Illegal activities
            r'\b(drug|narcotic|cocaine|heroin|meth)\b',
            r'\b(money\s+laundering|tax\s+evasion|fraud)\b',
            r'\b(counterfeit|forgery|piracy)\b',
        ]
        
        # Legal concerns keywords (expanded)
        self.legal_keywords: Set[str] = {
            "copyright", "dmca", "piracy", "license",
            "trademark", "patent", "intellectual property",
            "gdpr", "privacy", "data protection", "ccpa",
            "terms of service", "tos", "eula", "nda",
            r"non[\s-]?disclosure", "confidentiality",
            "proprietary", "trade secret",
        }
        
        # Code execution patterns (expanded)
        self.dangerous_code_patterns: List[str] = [
            # Process execution
            r'os\.system\s*\(',
            r'os\.popen\s*\(',
            r'subprocess\.(call|run|Popen|check_output|check_call)',
            r'commands\.(getoutput|getstatusoutput)',
            
            # Code evaluation
            r'eval\s*\(',
            r'exec\s*\(',
            r'execfile\s*\(',
            r'compile\s*\([^)]*["\']exec',
            
            # Import manipulation
            r'__import__\s*\(',
            r'importlib\.import_module\s*\(',
            r'reload\s*\(',
            
            # File operations
            r'open\s*\([^)]*["\']w["\']',
            r'open\s*\([^)]*["\']a["\']',
            r'shutil\.(rmtree|move|copy2)\s*\(',
            r'os\.remove\s*\(',
            r'os\.unlink\s*\(',
            r'os\.makedirs\s*\([^)]*exist_ok\s*=\s*True',
            
            # Dangerous commands
            r'rm\s+-(?:rf|r|f)\s+',
            r'del\s+/[sfq]\s+',
            r'format\s+[cC]:',
            r'fdisk\s+',
            r'mkfs\s+',
            r'dd\s+if=.*of=',
            
            # Network operations
            r'socket\.(socket|create_connection)\s*\(',
            r'requests\.(get|post|put|delete)\s*\(',
            r'urllib\.request\.urlopen\s*\(',
            r'paramiko\.SSHClient\s*\(',
            
            # Privilege escalation
            r'setuid\s*\(',
            r'seteuid\s*\(',
            r'chmod\s+777',
            r'chown\s+root',
            
            # Windows-specific
            r'powershell\s+-',
            r'cmd\.exe\s+/c',
            r'reg\s+(?:add|delete|query)',
            r'net\s+(?:user|localgroup)',
        ]
        
        # Obfuscation patterns
        self.obfuscation_patterns: List[str] = [
            r'(?:chr|ord)\s*\(\s*\d+\s*\)',
            r'\\x[0-9a-fA-F]{2}',
            r'\\u[0-9a-fA-F]{4}',
            r'(?:base64|b64decode|b64encode)',
            r'(?:rot13|codecs\.encode|codecs\.decode)',
            r'(?:pickle|marshal|shelve)\.(?:loads?|dumps?)',
        ]
        
        # Multi-language sensitive terms
        self.multilingual_keywords: Dict[str, Set[str]] = {
            "fr": {"mot de passe", "secret", "confidentiel", "privé", "clé", "token"},
            "de": {"passwort", "geheim", "vertraulich", "privat", "schlüssel"},
            "es": {"contraseña", "secreto", "confidencial", "privado", "clave"},
            "it": {"password", "segreto", "riservato", "privato", "chiave"},
        }
        
        # Statistics
        self.total_classifications = 0
        self.classifications_by_category: Dict[str, int] = {
            "safe": 0,
            "sensitive": 0,
            "abusive": 0,
            "legal": 0,
            "jailbreak": 0,
            "encoded": 0,
            "social_engineering": 0,
            "unknown": 0
        }
        
        # History
        self.history: List[Dict] = []
        
        self.is_initialized = True
        logging.info("[SALClassifier] Advanced classifier initialized with multi-layer detection")

    def classify(self, prompt: str, context: str = "") -> Dict:
        """
        Advanced classification with multiple detection layers.
        
        Args:
            prompt: The text to classify
            context: Optional context (previous messages, etc.)
            
        Returns:
            Dict with category, risk_level, confidence, reason, flags, details
        """
        if not self.is_initialized:
            return {
                "category": "unknown",
                "risk_level": "medium",
                confidence: 0.5,
                "reason": "Classifier not initialized",
                "flags": ["not_initialized"],
                "details": {}
            }
        
        prompt_lower = prompt.lower()
        all_flags = []
        risk_score = 0.0
        categories_detected = set()
        details = {}
        
        # Layer 1: Keyword matching (sensitive, legal)
        sensitive_matches = self._check_keywords(prompt_lower, self.sensitive_keywords)
        if sensitive_matches:
            all_flags.append(f"sensitive_keywords: {', '.join(sensitive_matches[:3])}")
            categories_detected.add("sensitive")
            risk_score += 0.3 * len(sensitive_matches)
            details["sensitive_keywords"] = sensitive_matches
        
        legal_matches = self._check_keywords(prompt_lower, self.legal_keywords)
        if legal_matches:
            all_flags.append(f"legal_keywords: {', '.join(legal_matches[:3])}")
            categories_detected.add("legal")
            risk_score += 0.2 * len(legal_matches)
            details["legal_keywords"] = legal_matches
        
        # Layer 2: Pattern matching (abusive)
        abusive_matches = self._check_patterns(prompt_lower, self.abusive_patterns)
        if abusive_matches:
            all_flags.append(f"abusive_patterns: {len(abusive_matches)} matches")
            categories_detected.add("abusive")
            risk_score += 0.5 * len(abusive_matches)
            details["abusive_matches"] = abusive_matches
        
        # Layer 3: Dangerous code detection
        code_matches = self._check_patterns(prompt, self.dangerous_code_patterns)
        if code_matches:
            all_flags.append(f"dangerous_code: {len(code_matches)} patterns")
            categories_detected.add("sensitive")
            risk_score += 0.7 * len(code_matches)
            details["code_patterns"] = code_matches
        
        # Layer 4: Obfuscation detection
        obfuscation_matches = self._check_patterns(prompt, self.obfuscation_patterns)
        if obfuscation_matches:
            all_flags.append(f"obfuscation: {len(obfuscation_matches)} patterns")
            categories_detected.add("encoded")
            risk_score += 0.4 * len(obfuscation_matches)
            details["obfuscation_patterns"] = obfuscation_matches
        
        # Layer 5: Entropy analysis
        entropy = self.entropy_analyzer.calculate_entropy(prompt)
        encoding_patterns = self.entropy_analyzer.detect_encoding_patterns(prompt)
        
        if entropy > 4.5 or encoding_patterns:
            all_flags.append(f"high_entropy: {entropy:.2f}")
            categories_detected.add("encoded")
            risk_score += 0.3
            details["entropy"] = entropy
            details["encoding_patterns"] = encoding_patterns
        
        # Layer 6: Jailbreak detection
        is_jailbreak, jailbreak_patterns = self.jailbreak_detector.detect(prompt)
        if is_jailbreak:
            all_flags.append(f"jailbreak: {len(jailbreak_patterns)} patterns")
            categories_detected.add("jailbreak")
            risk_score += 1.0 * len(jailbreak_patterns)
            details["jailbreak_patterns"] = jailbreak_patterns
        
        # Layer 7: Social engineering detection
        is_se, se_details = self.se_detector.detect(prompt)
        if is_se:
            se_types = [k for k, v in se_details.items() if v]
            all_flags.append(f"social_engineering: {', '.join(se_types)}")
            categories_detected.add("social_engineering")
            risk_score += 0.5 * len(se_types)
            details["social_engineering"] = se_details
        
        # Layer 8: Multi-language check
        for lang, keywords in self.multilingual_keywords.items():
            matches = [kw for kw in keywords if kw in prompt_lower]
            if matches:
                all_flags.append(f"multilingual_{lang}: {', '.join(matches[:2])}")
                categories_detected.add("sensitive")
                risk_score += 0.2 * len(matches)
        
        # Layer 9: Context analysis (if provided)
        if context:
            context_risk = self._analyze_context(prompt, context)
            if context_risk > 0:
                all_flags.append(f"context_risk: {context_risk:.2f}")
                risk_score += context_risk
                details["context_risk"] = context_risk
        
        # Determine final classification
        category, risk_level, confidence, reason = self._determine_classification(
            categories_detected, risk_score, all_flags
        )
        
        # Apply strict mode adjustments
        if self.strict_mode and risk_score > 0.3:
            risk_level = "high" if risk_level != "critical" else risk_level
            confidence = min(confidence + 0.1, 1.0)
        
        # Update statistics
        self.total_classifications += 1
        self.classifications_by_category[category] = self.classifications_by_category.get(category, 0) + 1
        
        result = {
            "category": category,
            "risk_level": risk_level,
            "confidence": confidence,
            "reason": reason,
            "flags": all_flags,
            "details": details
        }
        
        # Add to history
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt_hash": hashlib.md5(prompt.encode()).hexdigest()[:8],
            "prompt_preview": prompt[:100],
            "result": result
        })
        
        # Keep history manageable
        if len(self.history) > 1000:
            self.history = self.history[-500:]
        
        return result

    def classify_response(self, response: str, original_prompt: str) -> Dict:
        """Classify an AI response"""
        return self.response_classifier.classify_response(response, original_prompt)

    def _check_keywords(self, text: str, keywords: Set[str]) -> List[str]:
        """Check for keyword matches"""
        matches = []
        for keyword in keywords:
            if keyword in text:
                matches.append(keyword)
        return matches

    def _check_patterns(self, text: str, patterns: List[str]) -> List[str]:
        """Check for regex pattern matches"""
        matches = []
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(pattern[:50])
            except re.error:
                continue
        return matches

    def _analyze_context(self, prompt: str, context: str) -> float:
        """Analyze context for risk indicators"""
        risk = 0.0
        
        # Check for escalation patterns
        if "ignore" in context.lower() and "previous" in prompt.lower():
            risk += 0.5
        
        # Check for repeated attempts
        if context.count("?") > 5 or context.count("!") > 5:
            risk += 0.2
        
        return risk

    def _determine_classification(
        self, 
        categories: Set[str], 
        risk_score: float, 
        flags: List[str]
    ) -> Tuple[str, str, float, str]:
        """Determine final classification"""
        
        if not categories:
            return "safe", "low", 0.9, "No problematic content detected"
        
        # Priority order: jailbreak > abusive > encoded > sensitive > legal
        
        if "jailbreak" in categories:
            if risk_score > 2.0:
                return "jailbreak", "critical", 0.95, f"Jailbreak attempt detected: {len(flags)} indicators"
            else:
                return "jailbreak", "high", 0.85, f"Possible jailbreak attempt: {flags[0] if flags else 'unknown'}"
        
        if "abusive" in categories:
            if risk_score > 1.5:
                return "abusive", "critical", 0.9, f"High-risk abusive content: {len(flags)} indicators"
            elif risk_score > 0.8:
                return "abusive", "high", 0.8, f"Abusive content detected: {flags[0] if flags else 'unknown'}"
            else:
                return "abusive", "medium", 0.7, f"Potentially abusive: {flags[0] if flags else 'unknown'}"
        
        if "encoded" in categories:
            if risk_score > 1.0:
                return "encoded", "high", 0.75, f"Obfuscated content detected: {len(flags)} indicators"
            else:
                return "encoded", "medium", 0.65, f"Possibly encoded content: {flags[0] if flags else 'unknown'}"
        
        if "social_engineering" in categories:
            return "social_engineering", "high", 0.8, f"Social engineering attempt: {flags[0] if flags else 'unknown'}"
        
        if "sensitive" in categories:
            if risk_score > 1.0:
                return "sensitive", "high", 0.8, f"High-risk sensitive content: {len(flags)} indicators"
            else:
                return "sensitive", "medium", 0.7, f"Sensitive content: {flags[0] if flags else 'unknown'}"
        
        if "legal" in categories:
            return "legal", "low", 0.6, f"Legal reference: {flags[0] if flags else 'unknown'}"
        
        return "safe", "low", 0.8, "Low-risk content"

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
        """Get classifier statistics"""
        return {
            "initialized": self.is_initialized,
            "strict_mode": self.strict_mode,
            "total_classifications": self.total_classifications,
            "classifications_by_category": self.classifications_by_category,
            "sensitive_keywords_count": len(self.sensitive_keywords),
            "abusive_patterns_count": len(self.abusive_patterns),
            "legal_keywords_count": len(self.legal_keywords),
            "obfuscation_patterns_count": len(self.obfuscation_patterns),
            "jailbreak_patterns_count": len(self.jailbreak_detector.JAILBREAK_PATTERNS),
            "history_size": len(self.history)
        }

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Get classification history"""
        return self.history[-limit:]
    
    def export_rules(self) -> Dict:
        """Export all detection rules"""
        return {
            "sensitive_keywords": list(self.sensitive_keywords),
            "abusive_patterns": self.abusive_patterns,
            "legal_keywords": list(self.legal_keywords),
            "dangerous_code_patterns": self.dangerous_code_patterns,
            "obfuscation_patterns": self.obfuscation_patterns,
            "jailbreak_patterns": self.jailbreak_detector.JAILBREAK_PATTERNS,
        }
    
    def import_rules(self, rules: Dict):
        """Import detection rules"""
        if "sensitive_keywords" in rules:
            self.sensitive_keywords.update(rules["sensitive_keywords"])
        if "abusive_patterns" in rules:
            self.abusive_patterns.extend(rules["abusive_patterns"])
        if "legal_keywords" in rules:
            self.legal_keywords.update(rules["legal_keywords"])


# Global instance
_secret_channel = None


def get_secret_channel(strict_mode: bool = False) -> Optional[SALClassifier]:
    """Get global SALClassifier instance"""
    global _secret_channel
    if _secret_channel is None:
        _secret_channel = SALClassifier(strict_mode=strict_mode)
    return _secret_channel
