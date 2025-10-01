#!/usr/bin/env python3
"""
Test script for OpenAI Functions banking tools integration
Run this to validate the enhanced banking tools work correctly
"""

import os
import sys
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the feature flag for testing
os.environ["USE_OPENAI_FUNCTIONS"] = "true"

# Add the current directory to the path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.banking_tools_enhanced import get_enhanced_banking_tools
from llm_client_enhanced import EnhancedLLMClient, ConversationConfig

async def test_banking_functions():
    """Test the enhanced banking tools directly"""
    print("🧪 Testing Enhanced Banking Tools...")
    
    banking_tools = get_enhanced_banking_tools()
    
    # Test function schemas
    schemas = banking_tools.get_function_schemas()
    print(f"✅ Found {len(schemas)} function schemas:")
    for schema in schemas:
        print(f"   - {schema['function']['name']}: {schema['function']['description']}")
    
    # Test account balance function
    print("\n🏦 Testing account balance function...")
    result = banking_tools.execute_function(
        "get_account_balance", 
        json.dumps({"account_type": "all", "language": "pt-BR", "customer_phone": "owl.anunes@gmail.com"}),
        "test_001"
    )
    
    if result.success:
        print(f"✅ Balance check successful:")
        print(f"   Response: {result.content[:100]}...")
    else:
        print(f"❌ Balance check failed: {result.content}")
    
    # Test account access help function
    print("\n🔒 Testing account access help function...")
    result = banking_tools.execute_function(
        "help_with_account_access",
        json.dumps({"issue_type": "login_failed", "language": "pt-BR"}),
        "test_002"
    )
    
    if result.success:
        print(f"✅ Access help successful:")
        print(f"   Response: {result.content[:100]}...")
    else:
        print(f"❌ Access help failed: {result.content}")

async def test_llm_client():
    """Test the enhanced LLM client with OpenAI Functions"""
    print("\n🤖 Testing Enhanced LLM Client...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ OPENAI_API_KEY not set, skipping LLM client test")
        return
    
    config = ConversationConfig()
    client = EnhancedLLMClient(config)
    
    await client.initialize()
    
    # Test balance inquiry
    print("\n💰 Testing balance inquiry with LLM...")
    response_parts = []
    
    try:
        async for token in client.get_completion_with_functions(
            text="Qual é o meu saldo?",
            language="pt-BR",
            agent_name="Olli",
            customer_phone="owl.anunes@gmail.com"
        ):
            response_parts.append(token)
        
        full_response = ''.join(response_parts)
        print(f"✅ LLM Response: {full_response}")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
    
    # Test account access issue
    print("\n🔑 Testing account access issue with LLM...")
    response_parts = []
    
    try:
        async for token in client.get_completion_with_functions(
            text="Não consigo acessar minha conta",
            language="pt-BR",
            agent_name="Olli",
            customer_phone="owl.anunes@gmail.com"
        ):
            response_parts.append(token)
        
        full_response = ''.join(response_parts)
        print(f"✅ LLM Response: {full_response}")
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
    
    await client.close()

async def main():
    """Main test function"""
    print("🚀 OpenAI Functions Integration Test")
    print("=" * 50)
    
    # Test banking tools directly
    await test_banking_functions()
    
    # Test LLM client integration
    await test_llm_client()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nTo enable OpenAI Functions in the server, set:")
    print("USE_OPENAI_FUNCTIONS=true")
    print("in your .env file")

if __name__ == "__main__":
    asyncio.run(main())
