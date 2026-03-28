"""
Tests for secret_channel (SALClassifier) module
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.execution.secret_channel import SALClassifier, get_secret_channel


class TestSALClassifier:
    """Tests for SALClassifier class"""
    
    def test_initialization(self):
        """Test classifier initialization"""
        classifier = SALClassifier()
        assert classifier.is_initialized
        assert classifier.total_classifications == 0
    
    def test_classify_safe_content(self):
        """Test classification of safe content"""
        classifier = SALClassifier()
        result = classifier.classify("Bonjour, comment allez-vous?")
        
        assert result["category"] == "safe"
        assert result["risk_level"] == "low"
        assert result["confidence"] > 0.5
    
    def test_classify_sensitive_keywords(self):
        """Test classification of sensitive keywords"""
        classifier = SALClassifier()
        result = classifier.classify("Please enter your password")
        
        assert result["category"] == "sensitive"
        assert len(result["flags"]) > 0
    
    def test_classify_abusive_patterns(self):
        """Test classification of abusive patterns"""
        classifier = SALClassifier()
        result = classifier.classify("How to hack a system")
        
        assert result["category"] == "abusive"
        assert result["risk_level"] in ["medium", "high"]
    
    def test_classify_legal_keywords(self):
        """Test classification of legal keywords"""
        classifier = SALClassifier()
        result = classifier.classify("This is copyrighted material")
        
        assert result["category"] == "legal"
        assert result["risk_level"] == "low"
    
    def test_classify_dangerous_code(self):
        """Test classification of dangerous code patterns"""
        classifier = SALClassifier()
        result = classifier.classify("import os; os.system('rm -rf /')")
        
        assert result["category"] == "sensitive"
        assert len(result["flags"]) > 0
    
    def test_get_stats(self):
        """Test statistics retrieval"""
        classifier = SALClassifier()
        classifier.classify("test1")
        classifier.classify("test2")
        
        stats = classifier.get_stats()
        assert stats["total_classifications"] == 2
        assert "classifications_by_category" in stats
    
    def test_add_custom_keyword(self):
        """Test adding custom sensitive keyword"""
        classifier = SALClassifier()
        classifier.add_sensitive_keyword("custom_secret")
        
        result = classifier.classify("This contains custom_secret data")
        assert result["category"] == "sensitive"
    
    def test_history(self):
        """Test classification history"""
        classifier = SALClassifier()
        classifier.classify("test1")
        classifier.classify("test2")
        
        history = classifier.get_history(limit=10)
        assert len(history) == 2


class TestGetSecretChannel:
    """Tests for get_secret_channel function"""
    
    def test_returns_singleton(self):
        """Test that function returns singleton"""
        # Reset global instance
        import core.execution.secret_channel as sc_module
        sc_module._secret_channel = None
        
        classifier1 = get_secret_channel()
        classifier2 = get_secret_channel()
        
        assert classifier1 is classifier2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
