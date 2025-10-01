#!/usr/bin/env python3
"""
Test script to verify that Twilio HTTP logs are properly filtered
"""

import os

def test_print_filtering():
    """Test that our print filtering works correctly"""
    
    print("=== Testing Print Filtering ===\n")
    
    # Set environment to non-debug mode
    os.environ['DEBUG_MODE'] = 'false'
    
    try:
        # Import our server which should set up the print filtering
        from server import DEBUG_MODE
        
        print(f"DEBUG_MODE: {DEBUG_MODE}")
        print("Server imported successfully")
        print()
        
        # Test normal prints (should show)
        print("Normal print - should appear")
        
        # Test Twilio-style prints (should be suppressed)
        print("-- BEGIN Twilio API Request --")
        print("This should be suppressed")
        print("-- END Twilio API Request --")
        print("Response Status Code: 200") 
        print("Response Headers: {'Content-Type': 'application/json'}")
        print("Query Params: {'PageSize': 100}")
        print("Headers:")
        
        # Test normal print after (should show)
        print("Normal print after filtering - should appear")
        
        print()
        print("Test completed - only normal prints should appear above")
        
    except ImportError as e:
        print(f"Import issue (expected if dependencies missing): {e}")
        
    except Exception as e:
        print(f"Error: {e}")

def test_debug_mode():
    """Test that debug mode allows all prints"""
    print("\n=== Testing Debug Mode ===")
    
    # Set debug mode
    os.environ['DEBUG_MODE'] = 'true'
    
    print("In debug mode, all prints should appear:")
    print("-- BEGIN Twilio API Request --")
    print("This should appear in debug mode")
    print("-- END Twilio API Request --")

if __name__ == "__main__":
    test_print_filtering()
    test_debug_mode()
