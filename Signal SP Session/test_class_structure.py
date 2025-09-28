#!/usr/bin/env python3
"""
Test script to verify TwilioWebSocketHandler class structure
"""

def test_class_structure():
    """Test that the class has the expected methods"""
    
    print("Testing TwilioWebSocketHandler class structure...")
    
    # Read the server.py file and check for method definitions
    with open('server.py', 'r') as f:
        content = f.read()
    
    # Check for required methods
    required_methods = [
        'def handle_websocket',
        'def broadcast_to_dashboard', 
        'def update_transcription_state',
        'def handle_setup',
        'def handle_prompt',
        'def route_message',
        'def send_response'
    ]
    
    found_methods = []
    missing_methods = []
    
    for method in required_methods:
        if method in content:
            found_methods.append(method)
        else:
            missing_methods.append(method)
    
    print(f"Found methods: {found_methods}")
    
    if missing_methods:
        print(f"Missing methods: {missing_methods}")
        return False
    else:
        print("All required methods found!")
        
    # Check class definition
    if 'class TwilioWebSocketHandler:' in content:
        print("TwilioWebSocketHandler class definition found!")
    else:
        print("ERROR: TwilioWebSocketHandler class definition not found!")
        return False
        
    # Check for PWA functions
    pwa_functions = [
        'def broadcast_to_pwa_clients',
        'def handle_pwa_websocket'
    ]
    
    for func in pwa_functions:
        if func in content:
            print(f"Found: {func}")
        else:
            print(f"ERROR: Missing {func}")
            return False
    
    print("Class structure test: PASSED")
    return True

def test_syntax():
    """Test Python syntax"""
    import subprocess
    
    print("Testing Python syntax...")
    
    result = subprocess.run(['python3', '-m', 'py_compile', 'server.py'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Syntax test: PASSED")
        return True
    else:
        print("Syntax test: FAILED")
        print(f"Error: {result.stderr}")
        return False

if __name__ == "__main__":
    print("=== Server Structure Test ===\n")
    
    structure_ok = test_class_structure()
    syntax_ok = test_syntax()
    
    print(f"\n=== Results ===")
    print(f"Structure: {'PASS' if structure_ok else 'FAIL'}")
    print(f"Syntax: {'PASS' if syntax_ok else 'FAIL'}")
    
    if structure_ok and syntax_ok:
        print("\nServer should now start without the 'handle_websocket' error!")
    else:
        print("\nThere are still issues that need to be fixed.")
