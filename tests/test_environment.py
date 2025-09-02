#!/usr/bin/env python3
"""
Test all API keys and environment configuration
"""

import os
from dotenv import load_dotenv
import openai
import langfuse

def test_environment():
    """Test all environment variables and API connections"""
    
    print("🧪 Testing Environment Configuration")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Test basic environment variables
    print("\n1. 📋 Environment Variables:")
    env_vars = [
        "APP_NAME", "ENV", "REDIS_URL", "OPENAI_API_KEY", 
        "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "AGENT_MODEL"
    ]
    
    for var in env_vars:
        value = os.getenv(var, "NOT_SET")
        if "KEY" in var:
            print(f"   ✅ {var}: {value[:20]}..." if value != "NOT_SET" else f"   ❌ {var}: NOT_SET")
        else:
            print(f"   ✅ {var}: {value}")
    
    # Test OpenAI API
    print("\n2. 🤖 OpenAI API Test:")
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("AGENT_MODEL", "gpt-3.5-turbo"),
            messages=[{"role": "user", "content": "Say 'API test successful' in Spanish"}],
            max_tokens=20
        )
        print(f"   ✅ OpenAI Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ OpenAI Error: {e}")
    
    # Test Langfuse
    print("\n3. 📊 Langfuse Observability Test:")
    try:
        lf = langfuse.Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        auth_result = lf.auth_check()
        print(f"   ✅ Langfuse Auth: {auth_result}")
        
        # Create a test event
        lf.create_event(
            name="environment_test",
            metadata={"test": "successful", "timestamp": "2025-08-30"}
        )
        print("   ✅ Langfuse Event Created Successfully")
        
    except Exception as e:
        print(f"   ❌ Langfuse Error: {e}")
    
    # Test configuration values
    print("\n4. ⚙️  Agent Configuration:")
    config_vars = {
        "AGENT_MODEL": os.getenv("AGENT_MODEL", "NOT_SET"),
        "AGENT_TEMPERATURE": os.getenv("AGENT_TEMPERATURE", "NOT_SET"),
        "AGENT_MAX_TOKENS": os.getenv("AGENT_MAX_TOKENS", "NOT_SET"),
        "SESSION_EXPIRY_HOURS": os.getenv("SESSION_EXPIRY_HOURS", "NOT_SET"),
        "LANGFUSE_ENABLED": os.getenv("LANGFUSE_ENABLED", "NOT_SET")
    }
    
    for key, value in config_vars.items():
        print(f"   ✅ {key}: {value}")
    
    print("\n🎉 Environment test completed!")
    print("🚀 Ready for AI Agent development!")

if __name__ == "__main__":
    test_environment()
