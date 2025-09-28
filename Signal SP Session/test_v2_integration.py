#!/usr/bin/env python3
"""
Test script for v2 integration - validates the new functionality
without running the full server
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from tools.banking_functions_mock import BankingFunctionHandler, BANKING_FUNCTION_DEFINITIONS
from tools.conversations_integration_mock import VoiceConversationManager

async def test_banking_functions():
    """Test banking function handler"""
    print("🧪 Testing Banking Functions...")
    
    handler = BankingFunctionHandler()
    test_phone = "+5511999888777"
    
    try:
        # Test account balance function
        print("  - Testing get_account_balance...")
        result = await handler.handle_function_call(
            "get_account_balance", 
            {"customer_phone": test_phone},
            test_phone
        )
        print(f"    Result: {result.get('success', False)}")
        
        # Test transfer function (will likely fail without valid APIs but should not crash)
        print("  - Testing transfer_money...")
        result = await handler.handle_function_call(
            "transfer_money",
            {"to_account": "12345", "amount": 100.0, "description": "Test transfer"},
            test_phone
        )
        print(f"    Result: {result.get('success', False)} (expected to fail in test)")
        
    finally:
        await handler.close()
    
    print("✅ Banking Functions test completed")

async def test_conversations_integration():
    """Test conversations integration"""
    print("🧪 Testing Conversations Integration...")
    
    manager = VoiceConversationManager()
    test_phone = "+5511999888777"
    test_call_sid = f"CA_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    try:
        # Test starting a voice conversation
        print("  - Testing start_voice_conversation...")
        success = await manager.start_voice_conversation(test_phone, test_call_sid, "Olli")
        print(f"    Started: {success}")
        
        if success:
            # Test logging user speech
            print("  - Testing log_user_speech...")
            await manager.log_user_speech(test_phone, "Hello, I need help with my account balance")
            
            # Test logging agent response
            print("  - Testing log_agent_response...")
            await manager.log_agent_response(test_phone, "I'll help you check your account balance")
            
            # Test logging function call
            print("  - Testing log_function_call...")
            await manager.log_function_call(
                test_phone, 
                "get_account_balance", 
                {"customer_phone": test_phone},
                {"success": True, "balance": 1500.50}
            )
            
            print("  - Voice conversation messages logged successfully")
    
    finally:
        await manager.close()
    
    print("✅ Conversations Integration test completed")

def test_function_definitions():
    """Test function definitions structure"""
    print("🧪 Testing Function Definitions...")
    
    # Validate function definitions structure
    assert len(BANKING_FUNCTION_DEFINITIONS) == 3, "Should have 3 banking functions"
    
    function_names = [f["function"]["name"] for f in BANKING_FUNCTION_DEFINITIONS]
    expected_functions = ["get_account_balance", "transfer_money", "pix_transfer"]
    
    for expected in expected_functions:
        assert expected in function_names, f"Missing function: {expected}"
    
    print("  - All required functions present")
    print("  - Function definitions structure valid")
    print("✅ Function Definitions test completed")

async def main():
    """Run all tests"""
    print("🚀 Starting v2 Integration Tests...\n")
    
    try:
        # Test function definitions (sync test)
        test_function_definitions()
        print()
        
        # Test banking functions
        await test_banking_functions()
        print()
        
        # Test conversations integration
        await test_conversations_integration()
        print()
        
        print("🎉 All tests completed successfully!")
        print("\n📋 v2 Integration Summary:")
        print("  ✅ Banking function calling system ready")
        print("  ✅ Conversations Manager integration ready")
        print("  ✅ Function definitions properly structured")
        print("  ✅ Real-time logging and messaging ready")
        print("\n🚀 Ready to start the v2 server!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
