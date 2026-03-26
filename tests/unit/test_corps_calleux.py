"""
Unit tests for Corps Calleux dialogue synthesis
"""

import pytest
from unittest.mock import MagicMock, patch


class TestCorpsCalleux:
    """Test Corps Calleux dialogue synthesis"""

    @pytest.fixture
    def corps_calleux(self):
        """Create corps calleux with mocked dependencies"""
        from core.cognition.corps_calleux import CorpsCalleux

        return CorpsCalleux()

    def test_dialogue_returns_synthesis_with_both_hemispheres(self, corps_calleux):
        """Should return synthesis when both hemispheres available"""
        with patch("core.cognition.corps_calleux.get_left_hemisphere") as mock_left:
            with patch("core.cognition.corps_calleux.get_right_hemisphere") as mock_right:
                mock_left_instance = MagicMock()
                mock_right_instance = MagicMock()
                mock_left.return_value = mock_left_instance
                mock_right.return_value = mock_right_instance

                mock_left_instance.think.return_value = "Left analysis"
                mock_right_instance.think.return_value = "Right intuition"

                result = corps_calleux.dialogue_interieur("test prompt")

                assert "synthesis" in result or "final_synthesis" in result

    def test_dialogue_returns_synthesis_with_left_only(self, corps_calleux):
        """Should return synthesis when only left hemisphere available"""
        with patch("core.cognition.corps_calleux.get_left_hemisphere") as mock_left:
            with patch("core.cognition.corps_calleux.get_right_hemisphere", return_value=None):
                mock_left_instance = MagicMock()
                mock_left.return_value = mock_left_instance

                mock_left_instance.think.return_value = "Left only analysis"

                result = corps_calleux.dialogue_interieur("test prompt")

                assert "synthesis" in result or "final_synthesis" in result

    def test_dialogue_returns_synthesis_with_right_only(self, corps_calleux):
        """Should return synthesis when only right hemisphere available"""
        with patch("core.cognition.corps_calleux.get_left_hemisphere", return_value=None):
            with patch("core.cognition.corps_calleux.get_right_hemisphere") as mock_right:
                mock_right_instance = MagicMock()
                mock_right.return_value = mock_right_instance

                mock_right_instance.think.return_value = "Right only intuition"

                result = corps_calleux.dialogue_interieur("test prompt")

                assert "synthesis" in result or "final_synthesis" in result

    def test_dialogue_returns_synthesis_without_hemispheres(self, corps_calleux):
        """Should return synthesis even without hemispheres"""
        with patch("core.cognition.corps_calleux.get_left_hemisphere", return_value=None):
            with patch("core.cognition.corps_calleux.get_right_hemisphere", return_value=None):
                result = corps_calleux.dialogue_interieur("test prompt")

                assert result is not None
                assert isinstance(result, dict)
