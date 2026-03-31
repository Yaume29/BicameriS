"""
Unit tests for Switchboard state management
"""

import pytest
from core.system.switchboard import Switchboard


class TestSwitchboard:
    """Test Switchboard state management"""

    @pytest.fixture
    def switchboard(self):
        """Create fresh switchboard"""
        return Switchboard()

    def test_toggle_changes_state(self, switchboard):
        """Toggle should change state"""
        switchboard.toggle("autonomous_loop", True)
        assert switchboard.is_active("autonomous_loop") is True

        switchboard.toggle("autonomous_loop", False)
        assert switchboard.is_active("autonomous_loop") is False

    def test_toggle_unknown_feature_returns_false(self, switchboard):
        """Unknown feature should return False"""
        result = switchboard.toggle("nonexistent_feature", True)
        assert result is False

    def test_get_all_states_returns_dict(self, switchboard):
        """get_all_states should return dict"""
        states = switchboard.get_all_states()
        assert isinstance(states, dict)
        assert "autonomous_loop" in states

    def test_endocrine_config_bounds(self, switchboard):
        """Endocrine config should be bounded 0.0-1.0"""
        switchboard.set_endocrine_config(True, 1.5, 2.0)

        config = switchboard.get_endocrine_config()

        assert config["sensitivity"] <= 1.0
        assert config["impact"] <= 1.0
        assert config["sensitivity"] >= 0.0
        assert config["impact"] >= 0.0

    def test_endocrine_config_disabled(self, switchboard):
        """Endocrine can be disabled"""
        switchboard.set_endocrine_config(False, 0.5, 0.5)

        config = switchboard.get_endocrine_config()

        assert config["enabled"] is False
