"""
Tests for chat API
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from fastapi.testclient import TestClient
from server.main import app


class TestChatAPI:
    """Tests for chat API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)
    
    def test_chat_history_empty(self):
        """Test getting empty chat history"""
        response = self.client.get("/api/chat/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
    
    def test_chat_send_message(self):
        """Test sending a chat message"""
        response = self.client.post("/api/chat/send", json={
            "message": "Bonjour"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "response" in data
    
    def test_chat_send_empty_message(self):
        """Test sending empty message"""
        response = self.client.post("/api/chat/send", json={
            "message": ""
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
    
    def test_chat_clear(self):
        """Test clearing chat history"""
        # First send a message
        self.client.post("/api/chat/send", json={"message": "test"})
        
        # Then clear
        response = self.client.post("/api/chat/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
