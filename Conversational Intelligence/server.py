import json
import os
import threading
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Try to import pyngrok, but handle gracefully if not available (for production)
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    print("Warning: pyngrok not available. Ngrok functionality disabled.")

# Load environment variables from .env file
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Store for received data
received_data = []

# Environment-aware port configuration
deployment_env = os.getenv('DEPLOYMENT_ENVIRONMENT', 'local')
PORT = int(os.getenv('PORT', 4000))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhooks from Twilio Conversational Intelligence"""
    try:
        # Get the JSON data from the webhook
        data = request.get_json()
        
        # Store the data
        received_data.append(data)
        
        # Print the complete webhook data to console with detailed formatting
        print("\n" + "="*80)
        print("WEBHOOK RECEIVED - COMPLETE PAYLOAD DETAILS")
        print("="*80)
        
        # Print raw JSON with pretty formatting
        print("RAW PAYLOAD:")
        print("-" * 40)
        print(json.dumps(data, indent=4, sort_keys=True))
        print("-" * 40)
        
        # Print detailed breakdown of payload structure
        print("\nPAYLOAD STRUCTURE ANALYSIS:")
        print("-" * 40)
        if data:
            for key, value in data.items():
                print(f"KEY: {key}")
                print(f"  TYPE: {type(value).__name__}")
                if isinstance(value, dict):
                    print(f"  NESTED KEYS: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"  LIST LENGTH: {len(value)}")
                    if value and isinstance(value[0], dict):
                        print(f"  FIRST ITEM KEYS: {list(value[0].keys())}")
                else:
                    print(f"  VALUE: {value}")
                print()
        
        # Handle different types of webhooks with more detailed output
        if 'TranscriptSid' in data:
            print(f"TRANSCRIPTION UPDATE DETAILS:")
            print(f"  Transcript SID: {data.get('TranscriptSid')}")
            print(f"  Status: {data.get('Status')}")
            print(f"  All transcription fields: {[k for k in data.keys() if 'transcript' in k.lower()]}")
            
            if data.get('Status') == 'completed':
                print("  → Transcription completed!")
            elif data.get('Status') == 'in-progress':
                print("  → Transcription in progress...")
                
        if 'OperatorResults' in data:
            print(f"OPERATOR RESULTS DETAILS:")
            for i, result in enumerate(data['OperatorResults']):
                print(f"  Result #{i+1}:")
                print(f"    Operator: {result.get('operator_type')}")
                print(f"    Result: {result.get('result')}")
                print(f"    All keys: {list(result.keys())}")
        
        # Handle real-time transcription streaming with more details
        if 'Channel' in data and 'Text' in data:
            print(f"REAL-TIME TRANSCRIPTION DETAILS:")
            print(f"  Channel: {data['Channel']}")
            print(f"  Text: '{data['Text']}'")
            print(f"  Partial: {data.get('Partial', 'Not specified')}")
            print(f"  Timestamp: {data.get('Timestamp', 'Not provided')}")
            print(f"  All transcription keys: {[k for k in data.keys()]}")
            
            if data.get('Partial'):
                print("  → (Partial transcription)")
            else:
                print("  → (Final transcription)")
        
        # Print any additional fields not covered above
        known_fields = {'TranscriptSid', 'Status', 'OperatorResults', 'Channel', 'Text', 'Partial', 'Timestamp'}
        additional_fields = set(data.keys()) - known_fields
        if additional_fields:
            print(f"ADDITIONAL FIELDS:")
            for field in sorted(additional_fields):
                print(f"  {field}: {data[field]}")
        
        print("="*80)
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        print(f"Raw request data: {request.get_data()}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for cloud deployments"""
    return jsonify({
        "status": "healthy",
        "service": "intelligence-webhook",
        "environment": deployment_env,
        "webhooks_received": len(received_data)
    })

@app.route('/status', methods=['GET'])
def status():
    """Status endpoint with detailed information"""
    return jsonify({
        "status": "running",
        "environment": deployment_env,
        "webhooks_received": len(received_data),
        "last_webhook": received_data[-1] if received_data else None,
        "ngrok_available": NGROK_AVAILABLE
    })

@app.route('/data', methods=['GET'])
def get_data():
    """Get all received webhook data - useful for dashboards"""
    return jsonify({
        "total_webhooks": len(received_data),
        "data": received_data
    })

@app.route('/data/clear', methods=['POST'])
def clear_data():
    """Clear all stored webhook data"""
    global received_data
    received_data = []
    return jsonify({"status": "cleared", "webhooks_received": 0})

def setup_ngrok():
    """Setup ngrok tunnel (only in local development)"""
    if not NGROK_AVAILABLE:
        print("Warning: pyngrok not available. Skipping ngrok setup.")
        return None
        
    ngrok_domain = os.getenv('NGROK_DOMAIN')
    
    print("Starting ngrok tunnel...")
    if ngrok_domain:
        print(f"Using ngrok domain from .env: {ngrok_domain}")
        public_url = ngrok.connect(PORT, domain=ngrok_domain)
    else:
        print("No NGROK_DOMAIN found in .env, generating new tunnel...")
        public_url = ngrok.connect(PORT)
    
    print(f"Public URL: {public_url}")
    print(f"Webhook URL: {public_url}/webhook")
    print(f"Status URL: {public_url}/status")
    print(f"Data URL: {public_url}/data")
    
    return public_url

if __name__ == "__main__":
    try:
        print(f"\n🚀 Starting Intelligence Webhook Server")
        print(f"Environment: {deployment_env}")
        print(f"Port: {PORT}")
        
        # Setup ngrok tunnel ONLY for local development
        public_url = None
        if deployment_env == 'local' and NGROK_AVAILABLE:
            public_url = setup_ngrok()
            print("You can check server status at:", f"{public_url}/status")
            print("You can get webhook data at:", f"{public_url}/data")
        else:
            print(f"Running in {deployment_env} environment - ngrok disabled")
            print(f"Health check: http://localhost:{PORT}/health")
            print(f"Status endpoint: http://localhost:{PORT}/status")
            print(f"Data endpoint: http://localhost:{PORT}/data")
        
        print("\n" + "="*60)
        print("Press Ctrl+C to stop the server")
        print("="*60)
        
        # Run the Flask server with environment-aware host
        if deployment_env in ['render', 'heroku', 'aws', 'gcp']:
            host = '0.0.0.0'  # Bind to all interfaces for cloud deployment
        else:
            host = '0.0.0.0'  # Also use 0.0.0.0 for local to allow external access
            
        app.run(host=host, port=PORT, debug=(deployment_env == 'local'))
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        if deployment_env == 'local' and NGROK_AVAILABLE:
            try:
                ngrok.disconnect(PORT)
            except:
                pass  # Ignore errors during shutdown
        print("Server stopped.")
    except Exception as e:
        print(f"Error starting server: {str(e)}")
