"""Test script to verify Gemini API connectivity and model availability"""
import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.config import settings


async def test_gemini_model(model_name: str):
    """Test a specific Gemini model"""
    print(f"\n{'='*60}")
    print(f"Testing model: {model_name}")
    print(f"{'='*60}")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✓ Model initialized successfully")
        
        # Test with a simple message
        test_message = "Hello! Please respond with 'Test successful' if you can read this."
        print(f"Sending test message: '{test_message}'")
        
        response = await llm.ainvoke([HumanMessage(content=test_message)])
        
        print(f"✓ SUCCESS!")
        print(f"Response: {response.content[:200]}")
        return True
        
    except Exception as e:
        print(f"✗ FAILED!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        return False


async def main():
    """Test multiple Gemini models to find which ones work"""
    print("="*60)
    print("GEMINI API CONNECTIVITY TEST")
    print("="*60)
    print(f"API Key (first 20 chars): {settings.gemini_api_key[:20]}...")
    print(f"Environment: {settings.environment}")
    
    # List of models to test (in order of preference)
    models_to_test = [
        "gemini-2.5-flash",      # Current model in code
        "gemini-2.0-flash-exp",  # Stable experimental
        "gemini-1.5-flash",      # Older stable
        "gemini-1.5-pro",        # Older pro version
        "gemini-2.0-flash",      # Try without -exp
    ]
    
    working_models = []
    
    for model in models_to_test:
        success = await test_gemini_model(model)
        if success:
            working_models.append(model)
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if working_models:
        print(f"✓ {len(working_models)} working model(s) found:")
        for model in working_models:
            print(f"  - {model}")
        print(f"\nRecommendation: Use '{working_models[0]}' in llm.py")
    else:
        print("✗ No working models found!")
        print("\nPossible issues:")
        print("  1. Invalid or expired API key")
        print("  2. API key restrictions (IP/domain whitelist)")
        print("  3. Quota exceeded or billing not enabled")
        print("  4. Network connectivity issues")
        print("\nNext steps:")
        print("  1. Verify API key at: https://aistudio.google.com/app/apikey")
        print("  2. Check API key restrictions")
        print("  3. Ensure billing is enabled (if required)")


if __name__ == "__main__":
    asyncio.run(main())
