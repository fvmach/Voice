#!/usr/bin/env python3
"""
Test script for Real-Time Transcription webhook functionality
"""

import requests
import json
import asyncio
import websockets
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8080
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
WS_URL = f"ws://{SERVER_HOST}:{SERVER_PORT}/dashboard-ws"

def test_transcription_webhook():
    """Test the transcription webhook endpoint with sample data"""
    
    # Test data for different transcription events
    test_events = [
        {
            "event": "transcription-started",
            "CallSid": "CAtest123456789",
            "Name": "Test Transcription",
            "Timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event": "utterance-partial",
            "CallSid": "CAtest123456789", 
            "TranscriptText": "Hello, this is a partial",
            "Channel": "1",
            "Confidence": "0.95",
            "Timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event": "utterance-final",
            "CallSid": "CAtest123456789",
            "TranscriptText": "Hello, this is a final transcript from the customer",
            "Channel": "1", 
            "Confidence": "0.98",
            "Timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event": "utterance-partial",
            "CallSid": "CAtest123456789",
            "TranscriptText": "Thank you for calling, how can I",
            "Channel": "2",
            "Confidence": "0.93", 
            "Timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event": "utterance-final",
            "CallSid": "CAtest123456789",
            "TranscriptText": "Thank you for calling, how can I help you today?",
            "Channel": "2",
            "Confidence": "0.96",
            "Timestamp": datetime.now(timezone.utc).isoformat()
        },
        {
            "event": "transcription-stopped",
            "CallSid": "CAtest123456789",
            "Name": "Test Transcription", 
            "Timestamp": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    print(f"Testing transcription webhook at {BASE_URL}/transcripts")
    
    for i, event in enumerate(test_events, 1):
        print(f"\n--- Test {i}: {event['event']} ---")
        
        try:
            response = requests.post(
                f"{BASE_URL}/transcripts",
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code != 200:
                print(f"ERROR: Expected 200, got {response.status_code}")
            else:
                print("SUCCESS: Event processed successfully")
                
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Failed to send request - {e}")
        
        # Small delay between events
        asyncio.sleep(0.5)

def test_voice_twiml():
    """Test the voice TwiML endpoint"""
    print(f"\n=== Testing Voice TwiML endpoint ===")
    
    try:
        response = requests.get(f"{BASE_URL}/voice", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"TwiML Response:\n{response.text}")
        
        if response.status_code == 200 and "application/xml" in response.headers.get("Content-Type", ""):
            if "<Transcription" in response.text and "statusCallbackUrl" in response.text:
                print("SUCCESS: TwiML contains transcription configuration")
            else:
                print("WARNING: TwiML missing transcription configuration")
        else:
            print(f"ERROR: Expected XML response, got {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to get TwiML - {e}")

async def test_dashboard_websocket():
    """Test dashboard WebSocket to see if transcription events are broadcasted"""
    print(f"\n=== Testing Dashboard WebSocket ===")
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("Connected to dashboard WebSocket")
            print("Listening for transcription events...")
            
            # Set a timeout to avoid hanging
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"Received event: {data.get('type', 'unknown')}")
                print(f"Data: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("No events received within timeout period")
                
    except Exception as e:
        print(f"WebSocket connection failed: {e}")

def main():
    """Run all tests"""
    print("=== Real-Time Transcription Test Suite ===\n")
    
    # Test 1: Voice TwiML endpoint
    test_voice_twiml()
    
    # Test 2: Transcription webhook
    test_transcription_webhook()
    
    # Test 3: Dashboard WebSocket (async)
    print(f"\n=== Testing Dashboard WebSocket ===")
    print("Note: Run this separately if the server is running and you want to test WebSocket events")
    print(f"Command: python -c \"import asyncio; from test_transcription import test_dashboard_websocket; asyncio.run(test_dashboard_websocket())\"")

if __name__ == "__main__":
    main()
