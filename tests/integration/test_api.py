"""
Integration tests for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestAPIEndpoints:
    """Test critical API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch("server.main.registry") as mock_registry:
            from server.main import app

            mock_registry.switchboard = MagicMock()
            mock_registry.switchboard.get_all_states.return_value = {
                "autonomous_loop": False,
                "auto_scaffolding": False,
            }
            mock_registry.corps_calleux = None
            mock_registry.autonomous_thinker = None
            mock_registry.conductor = None
            mock_registry.inference_manager = None
            mock_registry.entropy = MagicMock()
            mock_registry.entropy.get_pulse.return_value = 0.5
            return TestClient(app)

    def test_get_switches(self, client):
        """GET /api/system/switches should return states"""
        with patch("server.routes.api_system.get_switchboard") as mock_sb:
            mock_sb.return_value.get_all_states.return_value = {"autonomous_loop": False}
            response = client.get("/api/system/switches")
            assert response.status_code == 200

    def test_get_system_status(self, client):
        """GET /api/system/status should return status"""
        response = client.get("/api/system/status")
        assert response.status_code == 200
        data = response.json()
        assert "switchboard" in data

    def test_post_toggle_switch(self, client):
        """POST /api/system/switches/{feature} should toggle"""
        with patch("server.routes.api_system.get_switchboard") as mock_sb:
            mock_sb.return_value.toggle.return_value = True
            response = client.post("/api/system/switches/autonomous_loop", json={"state": True})
            assert response.status_code == 200

    def test_put_endocrine_config(self, client):
        """PUT /api/system/endocrine should update config"""
        with patch("server.routes.api_system.get_switchboard") as mock_sb:
            mock_sb.return_value.set_endocrine_config = MagicMock()
            response = client.put(
                "/api/system/endocrine", json={"enabled": True, "sensitivity": 0.5, "impact": 0.5}
            )
            assert response.status_code == 200

    def test_get_conductor_stats(self, client):
        """GET /api/cognitive/conductor/stats should return stats"""
        with patch("server.routes.api_cognitive.get_conductor") as mock_conductor:
            mock_conductor.return_value.get_stats.return_value = {"pulse": 0.5, "tasks_total": 0}
            response = client.get("/api/cognitive/conductor/stats")
            assert response.status_code in [200, 501]
