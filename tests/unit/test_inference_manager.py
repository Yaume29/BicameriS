"""
Unit tests for InferenceManager - spawn, execute, guillotine
"""

import pytest
from unittest.mock import MagicMock, patch


class TestInferenceManager:
    """Test InferenceManager lifecycle"""

    @pytest.fixture
    def inference_manager(self):
        """Get InferenceManager class"""
        from core.execution.inference_manager import InferenceManager

        return InferenceManager

    def test_spawn_creates_incarnation(self, inference_manager):
        """Spawn should create a new incarnation"""
        with patch("core.execution.inference_manager.mp.Process") as mock_process:
            with patch("core.execution.inference_manager.zmq") as mock_zmq:
                mock_context = MagicMock()
                mock_socket = MagicMock()
                mock_zmq.Context.return_value = mock_context
                mock_context.socket.return_value = mock_socket
                mock_socket.recv.return_value = b"READY"

                result = inference_manager.spawn("test_model", "/path/to/model.gguf", {})

                assert result is True

    def test_execute_sends_to_worker(self, inference_manager):
        """Execute should send messages to worker"""
        with patch.object(
            inference_manager,
            "_incarnations",
            {"test": {"socket": MagicMock(), "lock": MagicMock()}},
        ):
            with patch.object(
                inference_manager, "_send_message", return_value=b'{"response": "test"}'
            ):
                result = inference_manager.execute(
                    "test", [{"role": "user", "content": "hello"}], {}
                )
                assert result is not None

    def test_guillotine_kills_incarnation(self, inference_manager):
        """Guillotine should remove incarnation"""
        mock_socket = MagicMock()
        mock_context = MagicMock()

        inference_manager._incarnations = {
            "test": {"socket": mock_socket, "context": mock_context, "process": MagicMock()}
        }

        result = inference_manager.guillotine("test")

        assert result is True
        assert "test" not in inference_manager._incarnations

    def test_guillotine_nonexistent_returns_true(self, inference_manager):
        """Guillotine non-existent should return True"""
        result = inference_manager.guillotine("nonexistent")
        assert result is True

    def test_get_incarnations_lists_all(self, inference_manager):
        """get_incarnations should return all active incarnations"""
        inference_manager._incarnations = {
            "model1": {"alive": True, "spawn_time": 1000},
            "model2": {"alive": True, "spawn_time": 2000},
        }

        result = inference_manager.get_incarnations()

        assert len(result) == 2
