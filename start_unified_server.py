#!/usr/bin/env python3
"""
Unified Render Startup Script
Manages multiple server processes for deployment on Render
"""

import os
import sys
import subprocess
import signal
import threading
import time
import asyncio
from pathlib import Path

class ProcessManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_process(self, name, command, cwd=None, env_vars=None):
        """Start a subprocess with proper logging"""
        print(f"🚀 Starting {name}...")
        
        # Prepare environment
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        try:
            # Start the process
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start thread to handle output
            output_thread = threading.Thread(
                target=self._handle_output,
                args=(process, name),
                daemon=True
            )
            output_thread.start()
            
            self.processes.append({
                'name': name,
                'process': process,
                'thread': output_thread
            })
            
            print(f"✅ {name} started (PID: {process.pid})")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return None
    
    def _handle_output(self, process, name):
        """Handle process output in separate thread"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[{name}] {line.strip()}")
        except Exception as e:
            print(f"[{name}] Output handler error: {e}")
    
    def wait_for_processes(self):
        """Wait for all processes and handle cleanup"""
        try:
            while self.running:
                # Check if any process has died
                for proc_info in self.processes:
                    if proc_info['process'].poll() is not None:
                        print(f"💀 Process {proc_info['name']} died with code {proc_info['process'].returncode}")
                        self.running = False
                        break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal, shutting down...")
            self.running = False
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes"""
        print("🧹 Cleaning up processes...")
        
        for proc_info in self.processes:
            process = proc_info['process']
            name = proc_info['name']
            
            if process.poll() is None:
                print(f"🔄 Terminating {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    print(f"⚡ Force killing {name}...")
                    process.kill()
                except Exception as e:
                    print(f"⚠️ Error stopping {name}: {e}")
        
        print("✅ All processes cleaned up")

def get_render_port():
    """Get the PORT environment variable from Render"""
    return os.environ.get('PORT', '8080')

def setup_environment():
    """Setup environment variables for unified deployment"""
    render_port = get_render_port()
    
    # Set ports for different services
    # Main conversation relay gets the Render PORT
    os.environ['CONVERSATION_RELAY_PORT'] = render_port
    
    # Other services get offset ports
    base_port = int(render_port)
    os.environ['CONVERSATIONS_API_PORT'] = str(base_port + 1)
    os.environ['INTELLIGENCE_WEBHOOK_PORT'] = str(base_port + 2)
    
    # Set deployment environment
    os.environ['DEPLOYMENT_ENVIRONMENT'] = 'render'
    os.environ['NODE_ENV'] = 'production'
    
    print(f"🌍 Environment configured:")
    print(f"   - Main port: {render_port}")
    print(f"   - Conversations API: {base_port + 1}")
    print(f"   - Intelligence webhook: {base_port + 2}")

def main():
    """Main startup function"""
    print("=" * 60)
    print("🚀 Cross-Channel AI Agents - Unified Render Startup")
    print("=" * 60)
    
    # Setup environment
    setup_environment()
    
    # Initialize process manager
    manager = ProcessManager()
    
    # Get current directory
    base_dir = Path(__file__).parent.absolute()
    
    # Define server configurations
    servers = [
        {
            'name': 'ConversationRelay',
            'command': f'python server-backup.py',
            'cwd': base_dir,
            'env': {
                'PORT': os.environ['CONVERSATION_RELAY_PORT']
            }
        },
        {
            'name': 'ConversationsAPI', 
            'command': 'node server.js',
            'cwd': base_dir / 'Conversations',
            'env': {
                'PORT': os.environ['CONVERSATIONS_API_PORT']
            }
        }
    ]
    
    # Start all servers
    print(f"\n📡 Starting {len(servers)} servers...")
    
    for server in servers:
        process = manager.start_process(
            name=server['name'],
            command=server['command'],
            cwd=server['cwd'],
            env_vars=server.get('env', {})
        )
        
        if not process:
            print(f"❌ Failed to start {server['name']}, aborting...")
            manager.cleanup()
            sys.exit(1)
        
        # Small delay between starts
        time.sleep(2)
    
    print(f"\n✅ All servers started successfully!")
    print(f"🌐 Main endpoint: http://localhost:{get_render_port()}")
    print("📊 Use Ctrl+C to stop all servers")
    print("-" * 60)
    
    # Wait for processes
    manager.wait_for_processes()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)