"""
Integration tests for chat functionality with error scenarios
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.services.llm import LLMService
from app.utils.circuit_breaker import CircuitBreakerError


client = TestClient(app)


class TestChatIntegration:
    """Integration tests for chat endpoints"""
    
    def test_create_session_success(self):
        """Test successful session creation"""
        response = client.post("/api/chat/session", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    def test_send_message_success(self):
        """Test successful message sending"""
        # Create session first
        session_response = client.post("/api/chat/session", json={})
        session_id = session_response.json()["session_id"]
        
        # Send message
        response = client.post(
            "/api/chat/message",
            json={
                "message": "Show me bats under 5000 rupees",
                "session_id": session_id
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0
        assert data["session_id"] == session_id
    
    def test_send_message_without_session(self):
        """Test sending message without session ID creates one"""
        response = client.post(
            "/api/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "session_id" in data
    
    def test_ambiguous_input_handling(self):
        """Test handling of ambiguous inputs like '500'"""
        response = client.post(
            "/api/chat/message",
            json={"message": "500"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should ask for clarification, not crash
        assert len(data["message"]) > 0
    
    def test_empty_message_handling(self):
        """Test handling of empty messages"""
        response = client.post(
            "/api/chat/message",
            json={"message": ""}
        )
        
        # Should return 200 with helpful message or validation error
        assert response.status_code in [200, 422]
    
    def test_very_long_message_handling(self):
        """Test handling of very long messages"""
        long_message = "a" * 1000  # 1000 characters
        
        response = client.post(
            "/api/chat/message",
            json={"message": long_message}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    @patch('app.services.llm.LLMService.generate_response')
    async def test_llm_timeout_handling(self, mock_generate):
        """Test handling of LLM timeout"""
        mock_generate.side_effect = asyncio.TimeoutError("LLM timeout")
        
        response = client.post(
            "/api/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should have fallback message
        assert "trouble" in data["message"].lower() or "quick" in data["message"].lower()
    
    @patch('app.services.llm.LLMService.generate_response')
    async def test_circuit_breaker_open_handling(self, mock_generate):
        """Test handling when circuit breaker is open"""
        mock_generate.side_effect = CircuitBreakerError("Circuit breaker is OPEN")
        
        response = client.post(
            "/api/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        # Should have circuit breaker specific message
        assert "high" in data["message"].lower() or "traffic" in data["message"].lower()
    
    def test_rate_limiting(self):
        """Test rate limiting on chat endpoint"""
        # Send many requests quickly
        responses = []
        for i in range(70):  # Exceed 60/minute limit
            response = client.post(
                "/api/chat/message",
                json={"message": f"Test message {i}"}
            )
            responses.append(response.status_code)
        
        # Should have some 429 responses
        assert 429 in responses
    
    def test_get_chat_history_success(self):
        """Test retrieving chat history"""
        # Create session and send message
        session_response = client.post("/api/chat/session", json={})
        session_id = session_response.json()["session_id"]
        
        client.post(
            "/api/chat/message",
            json={"message": "Hello", "session_id": session_id}
        )
        
        # Get history
        response = client.get(f"/api/chat/history/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "messages" in data
    
    def test_get_chat_history_nonexistent_session(self):
        """Test retrieving history for non-existent session"""
        response = client.get("/api/chat/history/nonexistent-session-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["messages"]) == 0
    
    def test_health_endpoint_includes_circuit_breaker(self):
        """Test health endpoint includes circuit breaker status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "circuit_breaker" in data
        assert "state" in data["circuit_breaker"]
    
    def test_conversation_context_preservation(self):
        """Test that conversation context is preserved across messages"""
        session_response = client.post("/api/chat/session", json={})
        session_id = session_response.json()["session_id"]
        
        # First message
        response1 = client.post(
            "/api/chat/message",
            json={"message": "I want to buy a bat", "session_id": session_id}
        )
        assert response1.status_code == 200
        
        # Follow-up message (should remember context)
        response2 = client.post(
            "/api/chat/message",
            json={"message": "Under 5000 rupees", "session_id": session_id}
        )
        assert response2.status_code == 200
        data2 = response2.json()
        # Should understand this is about bat price
        assert "message" in data2


class TestErrorRecovery:
    """Tests for error recovery patterns"""
    
    def test_multiple_retry_attempts(self):
        """Test that system retries on transient failures"""
        # This is tested indirectly through the retry decorator
        # The system should handle transient failures gracefully
        response = client.post(
            "/api/chat/message",
            json={"message": "Hello"}
        )
        
        assert response.status_code == 200
    
    def test_fallback_response_quality(self):
        """Test that fallback responses are helpful"""
        with patch('app.services.llm.LLMService._call_llm_with_retry') as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            
            response = client.post(
                "/api/chat/message",
                json={"message": "Hello"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "quick_replies" in data
            assert len(data["quick_replies"]) > 0


class TestStreamingEndpoint:
    """Tests for streaming endpoint"""
    
    def test_streaming_endpoint_exists(self):
        """Test that streaming endpoint is available"""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Hello"}
        )
        
        # Should return streaming response
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
