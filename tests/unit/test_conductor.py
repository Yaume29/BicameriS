"""
Unit tests for Conductor arbitration based on pulse levels
"""

import pytest
from unittest.mock import MagicMock, patch


class TestConductorArbitration:
    """Test Conductor mode selection based on hardware pulse"""

    @pytest.fixture
    def conductor(self):
        """Create conductor with mocked dependencies"""
        from core.cognition.conductor import Conductor

        return Conductor()

    def test_low_pulse_uses_audit_mode(self, conductor):
        """Pulse < 0.75 should use audit mode"""
        with patch.object(conductor.entropy, "get_pulse", return_value=0.3):
            with patch("core.cognition.conductor.get_left_hemisphere") as mock_left:
                with patch("core.cognition.conductor.get_right_hemisphere") as mock_right:
                    mock_left_instance = MagicMock()
                    mock_right_instance = MagicMock()
                    mock_left.return_value = mock_left_instance
                    mock_right.return_value = mock_right_instance
                    mock_left_instance.is_loaded = True
                    mock_right_instance.is_loaded = True
                    mock_left_instance.think_with_tools.return_value = {"response": "Audit result"}

                    with patch("core.cognition.conductor.get_switchboard") as mock_sb:
                        mock_sb_instance = MagicMock()
                        mock_sb.return_value = mock_sb_instance
                        mock_sb_instance.is_active.side_effect = lambda x: False

                        result = conductor.orchestrate_task("test prompt")
                        assert result["mode"] == "AUDIT_TOOLS"

    def test_high_pulse_uses_autonomous_drift(self, conductor):
        """Pulse > 0.75 should use autonomous drift mode"""
        with patch.object(conductor.entropy, "get_pulse", return_value=0.8):
            with patch("core.cognition.conductor.get_left_hemisphere") as mock_left:
                with patch("core.cognition.conductor.get_right_hemisphere") as mock_right:
                    mock_left_instance = MagicMock()
                    mock_right_instance = MagicMock()
                    mock_left.return_value = mock_left_instance
                    mock_right.return_value = mock_right_instance
                    mock_left_instance.is_loaded = True
                    mock_right_instance.is_loaded = True
                    mock_left_instance.think.return_value = "Drift synthesis"
                    mock_right_instance.feel.return_value = "Intuition"

                    result = conductor.orchestrate_task("test prompt")
                    assert result["mode"] == "AUTONOMOUS_DRIFT"
                    assert result["leader"] == "RIGHT (Gemma)"

    def test_missing_hemispheres_returns_error(self, conductor):
        """Missing hemispheres should return error"""
        with patch("core.cognition.conductor.get_left_hemisphere", return_value=None):
            with patch("core.cognition.conductor.get_right_hemisphere", return_value=None):
                result = conductor.orchestrate_task("test prompt")
                assert "error" in result
                assert result["leader"] == "NONE"
