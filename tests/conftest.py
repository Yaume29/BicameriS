"""
Pytest configuration and fixtures for Bicameris tests
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_thermal():
    """Mock thermal governor"""

    class MockThermal:
        def get_status_passive(self):
            return {"cpu_temp": 45, "gpu_temp": 50, "entropic_impact": 0.5}

        def is_available(self):
            return True

    return MockThermal()


@pytest.fixture
def mock_entropy():
    """Mock entropy generator"""

    class MockEntropy:
        def get_pulse(self):
            return 0.5

        def get_full_stats(self):
            return {"cpu_usage": 50, "ram_usage": 60, "vram_usage": 70}

    return MockEntropy()


@pytest.fixture
def mock_switchboard():
    """Mock switchboard"""

    class MockSwitchboard:
        def __init__(self):
            self._states = {"autonomous_loop": False, "auto_scaffolding": False}

        def is_active(self, feature):
            return self._states.get(feature, False)

        def get_all_states(self):
            return self._states.copy()

    return MockSwitchboard()


@pytest.fixture
def mock_corps_calleux():
    """Mock corps calleux"""

    class MockCorpsCalleux:
        def __init__(self):
            self.last_result = None

        def dialogue_interieur(self, prompt, context=""):
            self.last_result = {
                "synthesis": "Test synthesis",
                "left": "Left analysis",
                "right": "Right intuition",
            }
            return self.last_result

        def is_available(self):
            return True

    return MockCorpsCalleux()


@pytest.fixture
def mock_inference_manager():
    """Mock inference manager"""

    class MockInferenceManager:
        def __init__(self):
            self.incarnations = {}

        def spawn(self, name, model_path, config):
            self.incarnations[name] = {"alive": True}
            return True

        def execute(self, name, messages, params):
            if name in self.incarnations:
                return {"choices": [{"message": {"content": "Mock response"}}]}
            return {"error": "Incarnation not found"}

        def guillotine(self, name):
            if name in self.incarnations:
                del self.incarnations[name]
            return True

    return MockInferenceManager()


@pytest.fixture
def mock_sandbox():
    """Mock sandbox"""

    class MockSandbox:
        def execute_code(self, code, timeout=10, requirements=None):
            if "subprocess" in code and ("call" in code or "run" in code or "Popen" in code):
                return {"status": "ERROR", "error": "Subprocess calls not allowed in sandbox"}
            if "import os" in code:
                return {"status": "SUCCESS", "output": "os module available"}
            return {"status": "SUCCESS", "output": "Code executed"}

    return MockSandbox()
