"""Direct test of the chat endpoint to see detailed errors"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.routes.chat import send_message
from app.models.chat import ChatMessageRequest
from app.services.llm import get_llm_service
from app.db.database import get_db
from fastapi import Request
from unittest.mock import Mock

async def test_endpoint():
    """Test the chat endpoint directly"""
    print("Testing chat endpoint...")
    
    try:
        # Create mock request
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        
        # Create chat request
        chat_request = ChatMessageRequest(
            message="Hello, I'm looking for cricket bats",
            session_id=None
        )
        
        # Get dependencies
        llm_service = await get_llm_service()
        db = await get_db()
        
        # Call endpoint
        print("Calling send_message...")
        response = await send_message(
            http_request=mock_request,
            request=chat_request,
            llm_service=llm_service,
            db=db
        )
        
        print(f"✓ SUCCESS!")
        print(f"Response: {response.message[:200]}")
        print(f"Session ID: {response.session_id}")
        print(f"Quick replies: {response.quick_replies}")
        
    except Exception as e:
        print(f"✗ ERROR!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_endpoint())
