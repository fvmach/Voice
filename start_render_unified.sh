#!/bin/bash

# Unified Render Startup Script (Bash version)
# Simple alternative to Python script for basic deployments

echo "🚀 Cross-Channel AI Agents - Unified Render Startup"
echo "=================================================="

# Get the PORT from Render (defaults to 8080)
MAIN_PORT=${PORT:-8080}
API_PORT=$((MAIN_PORT + 1))

echo "🌍 Environment:"
echo "   - Main Conversation Relay: $MAIN_PORT"
echo "   - Conversations API: $API_PORT"

# Export environment variables
export PORT=$MAIN_PORT
export NODE_ENV=production
export DEPLOYMENT_ENVIRONMENT=render

echo ""
echo "📡 Starting servers..."

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $CONVERSATION_PID 2>/dev/null
    kill $API_PID 2>/dev/null
    wait
    echo "✅ All servers stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Start Conversation Relay Server (Python)
echo "🚀 Starting Conversation Relay Server..."
PORT=$MAIN_PORT python server-backup.py &
CONVERSATION_PID=$!

# Give it time to start
sleep 3

# Start Conversations API Server (Node.js)
echo "🚀 Starting Conversations API Server..."
cd Conversations
PORT=$API_PORT node server.js &
API_PID=$!
cd ..

# Give it time to start
sleep 3

echo ""
echo "✅ All servers started!"
echo "🌐 Main endpoint: http://localhost:$MAIN_PORT"
echo "📊 Dashboard: http://localhost:$MAIN_PORT/dashboard"
echo "🔗 API endpoint: http://localhost:$API_PORT"
echo ""
echo "📡 Press Ctrl+C to stop all servers"
echo "=================================="

# Wait for both processes
wait $CONVERSATION_PID $API_PID