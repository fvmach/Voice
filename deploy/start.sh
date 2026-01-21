#!/bin/bash

# Startup script for Render - runs both Python and Node.js servers
echo "Starting Cross-Channel AI Agents..."

# Set environment
export DEPLOYMENT_ENVIRONMENT=render

# Start Node.js Conversations API server in background
echo "Starting Conversations API server..."
cd Conversations && npm start &
NODE_PID=$!
echo "Conversations server started with PID: $NODE_PID"

# Give Node.js server time to start
sleep 3

# Start Python server in foreground (main process)
echo "Starting Python server..."
cd "Signal SP Session" && python server.py &
PYTHON_PID=$!
echo "Python server started with PID: $PYTHON_PID"

# Function to cleanup processes on exit
cleanup() {
    echo "Shutting down servers..."
    kill $NODE_PID 2>/dev/null
    kill $PYTHON_PID 2>/dev/null
    exit
}

# Trap signals to cleanup processes
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait