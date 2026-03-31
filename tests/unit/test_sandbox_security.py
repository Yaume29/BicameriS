"""
Unit tests for sandbox security - verify dangerous code is rejected
"""

import pytest
from core.cognition.sandbox_env import DockerSandbox


class TestSandboxSecurity:
    """Test sandbox security filters"""

    def test_rejects_subprocess_call(self, mock_sandbox):
        """subprocess.call should be rejected"""
        code = "import subprocess; subprocess.call(['ls'])"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "ERROR"
        assert "not allowed" in result["error"].lower()

    def test_rejects_subprocess_run(self, mock_sandbox):
        """subprocess.run should be rejected"""
        code = "import subprocess; subprocess.run(['ls'])"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "ERROR"

    def test_rejects_subprocess_popen(self, mock_sandbox):
        """subprocess.Popen should be rejected"""
        code = "import subprocess; subprocess.Popen(['ls'])"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "ERROR"

    def test_rejects_os_system(self, mock_sandbox):
        """os.system should be rejected"""
        code = "import os; os.system('rm -rf /')"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "ERROR"

    def test_allows_safe_code(self, mock_sandbox):
        """Safe Python code should execute"""
        code = "print('hello'); result = 1 + 1"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "SUCCESS"

    def test_allows_math_import(self, mock_sandbox):
        """Math imports should be allowed"""
        code = "import math; print(math.sqrt(4))"
        result = mock_sandbox.execute_code(code)
        assert result["status"] == "SUCCESS"
