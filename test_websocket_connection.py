#!/usr/bin/env python3
"""
Test script to verify WebSocket connection stability
Usage: python test_websocket_connection.py wss://your-ngrok-url.ngrok.io/websocket
"""

import asyncio
import json
import sys
import websockets
from datetime import datetime

async def test_websocket_connection(uri):
    """Test WebSocket connection with conversation relay events"""
    print(f"🔌 Testing WebSocket connection to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send setup event
            setup_event = {
                "event": "setup",
                "callSid": "test-call-sid-12345",
                "from": "+1234567890",
                "to": "+0987654321"
            }
            
            print("📤 Sending setup event...")
            await websocket.send(json.dumps(setup_event))
            print("✅ Setup event sent")
            
            # Send prompt event  
            prompt_event = {
                "event": "prompt",
                "voicePrompt": "Hello, this is a test message",
                "interruptible": True,
                "preemptible": True,
                "last": True
            }
            
            print("📤 Sending prompt event...")
            await websocket.send(json.dumps(prompt_event))
            print("✅ Prompt event sent")
            
            # Wait for response
            print("⏳ Waiting for AI response...")
            timeout_seconds = 30
            
            start_time = datetime.now()
            response_received = False
            
            try:
                while (datetime.now() - start_time).seconds < timeout_seconds:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    print(f"📥 Received: {response_data}")
                    
                    if response_data.get("type") == "text":
                        response_received = True
                        if response_data.get("last", False):
                            print("✅ Complete response received!")
                            break
                            
            except asyncio.TimeoutError:
                if response_received:
                    print("⚠️  Partial response received, but connection is working")
                else:
                    print("❌ No response received within timeout")
                    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False
        
    return True

async def main():
    if len(sys.argv) != 2:
        print("Usage: python test_websocket_connection.py wss://your-url.ngrok.io/websocket")
        print("\nFor local testing:")
        print("python test_websocket_connection.py ws://localhost:8080/websocket")
        sys.exit(1)
        
    uri = sys.argv[1]
    success = await test_websocket_connection(uri)
    
    if success:
        print("\n🎉 WebSocket connection test completed successfully!")
    else:
        print("\n💥 WebSocket connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())