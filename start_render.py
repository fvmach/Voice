#!/usr/bin/env python3

"""
Render Deployment Startup Script
Dual-service deployment: Python server (conversation relay) + Node.js server (API)
"""

import os
import subprocess
import sys
import signal
import time
import threading
from datetime import datetime

def log(message):
    """Simple logging with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_python_server(env, main_port):
    """Run the Python conversation relay server"""
    log("🐍 Starting Python Conversation Relay Server...")
    try:
        python_env = env.copy()
        python_env['PORT'] = str(main_port)
        
        process = subprocess.Popen([
            sys.executable, 'server-backup.py'
        ], env=python_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
        universal_newlines=True, bufsize=1)
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[PYTHON] {line.rstrip()}")
                
        process.wait()
        return process.returncode
        
    except Exception as e:
        log(f"❌ Python server error: {e}")
        return 1

def run_node_server(env, api_port):
    """Run the Node.js conversations API server"""
    log("📦 Starting Node.js Conversations API Server...")
    try:
        node_env = env.copy()
        node_env['PORT'] = str(api_port)
        node_env['NODE_ENV'] = 'production'
        
        # First install dependencies if needed
        log("Installing Node.js dependencies...")
        install_result = subprocess.run([
            'npm', 'install'
        ], cwd='Conversations', env=node_env, capture_output=True, text=True)
        
        if install_result.returncode != 0:
            log(f"❌ npm install failed: {install_result.stderr}")
            return 1
            
        log("✅ Node.js dependencies installed")
        
        # Start the server
        process = subprocess.Popen([
            'node', 'server.js'
        ], cwd='Conversations', env=node_env, stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1)
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[NODE] {line.rstrip()}")
                
        process.wait()
        return process.returncode
        
    except Exception as e:
        log(f"❌ Node.js server error: {e}")
        return 1

def main():
    """Main startup function for Render deployment"""
    
    log("Starting Cross-Channel AI Agents on Render (Dual Service)")
    log("=" * 60)
    
    # Verify environment
    deployment_env = os.getenv('DEPLOYMENT_ENVIRONMENT', 'render')
    main_port = int(os.getenv('PORT', '8080'))
    api_port = main_port + 1  # API runs on PORT + 1
    
    log(f"Environment: {deployment_env}")
    log(f"Python server port: {main_port}")
    log(f"Node.js API port: {api_port}")
    
    # Verify required environment variables
    required_vars = ['OPENAI_API_KEY', 'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        log(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        log("Please configure these in your Render dashboard")
        sys.exit(1)
    
    log("Environment variables verified")
    
    # Set up environment for subprocesses
    env = os.environ.copy()
    env['DEPLOYMENT_ENVIRONMENT'] = 'render'
    
    # Global process references for cleanup
    python_process = None
    node_process = None
    
    def cleanup_processes():
        """Clean up both processes on exit"""
        log("Cleaning up processes...")
        if python_process and python_process.poll() is None:
            python_process.terminate()
            try:
                python_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                python_process.kill()
        if node_process and node_process.poll() is None:
            node_process.terminate()
            try:
                node_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                node_process.kill()
        log("Cleanup completed")
    
    def signal_handler(signum, frame):
        log("Received shutdown signal")
        cleanup_processes()
        sys.exit(0)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start Python server in background
        log("Starting Python server...")
        python_env = env.copy()
        python_env['PORT'] = str(main_port)
        
        python_process = subprocess.Popen([
            sys.executable, 'server-backup.py'
        ], env=python_env)
        
        # Give Python server time to start
        time.sleep(5)
        
        # Check if Python server started successfully
        if python_process.poll() is not None:
            log(f"ERROR: Python server failed to start (exit code: {python_process.returncode})")
            cleanup_processes()
            sys.exit(1)
        
        log("Python server started successfully")
        # Install Node.js dependencies
        log("Installing Node.js dependencies...")
        node_env = env.copy()
        node_env['NODE_ENV'] = 'production'
        
        install_result = subprocess.run([
            'npm', 'install'
        ], cwd='Conversations', env=node_env, capture_output=True, text=True, timeout=300)
        
        if install_result.returncode != 0:
            log(f"ERROR: npm install failed: {install_result.stderr}")
            cleanup_processes()
            sys.exit(1)
            
        log("Node.js dependencies installed")
        
        # Start Node.js server
        log("Starting Node.js server...")
        node_env['PORT'] = str(api_port)
        
        node_process = subprocess.Popen([
            'node', 'server.js'
        ], cwd='Conversations', env=node_env)
        
        # Give Node server time to start
        time.sleep(3)
        
        # Check if Node server started successfully
        if node_process.poll() is not None:
            log(f"ERROR: Node.js server failed to start (exit code: {node_process.returncode})")
            cleanup_processes()
            sys.exit(1)
            
        log("Node.js server started successfully")
        
        log("Both servers are running!")
        log(f"Python server: http://0.0.0.0:{main_port}")
        log(f"Node.js API: http://0.0.0.0:{api_port}")
        log("Waiting for processes...")
        
        # Wait for both processes (this keeps the script alive)
        while True:
            python_alive = python_process.poll() is None
            node_alive = node_process.poll() is None
            
            if not python_alive:
                log(f"Python server exited with code: {python_process.returncode}")
                break
            if not node_alive:
                log(f"Node.js server exited with code: {node_process.returncode}")
                break
                
            time.sleep(1)
            
        cleanup_processes()
        # Don't exit with error code if servers exit cleanly
        if python_process.returncode == 0 and node_process.returncode == 0:
            log("Both servers completed successfully")
            sys.exit(0)
        else:
            sys.exit(1)
        
    except KeyboardInterrupt:
        log("Servers stopped by user")
        cleanup_processes()
    except Exception as e:
        log(f"ERROR: Unexpected error: {e}")
        cleanup_processes()
        sys.exit(1)

if __name__ == "__main__":
    main()