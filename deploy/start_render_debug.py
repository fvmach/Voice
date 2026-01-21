#!/usr/bin/env python3
"""
Diagnostic startup script for Render deployment debugging.
This script performs comprehensive checks before starting the main server.
"""

import sys
import os
import subprocess
import importlib.util

# Add colorama for colored output
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    colors_available = True
except ImportError:
    # Fallback without colors
    class MockFore:
        RED = GREEN = CYAN = YELLOW = BLUE = MAGENTA = ""
    class MockStyle:
        RESET_ALL = ""
    Fore = MockFore()
    Style = MockStyle()
    colors_available = False

def log_info(message):
    print(f"{Fore.CYAN}[DEBUG] {message}{Style.RESET_ALL}")

def log_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")

def log_error(message):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")

def log_warning(message):
    print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")

def main():
    log_info("=== Render Deployment Diagnostic Startup ===")
    
    # 1. System environment checks
    log_info(f"Python version: {sys.version}")
    log_info(f"Python executable: {sys.executable}")
    log_info(f"Current working directory: {os.getcwd()}")
    
    # 2. Check critical environment variables
    required_env_vars = [
        "OPENAI_API_KEY",
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN"
    ]
    
    optional_env_vars = [
        "OPENAI_MODEL",
        "DEPLOYMENT_ENVIRONMENT",
        "USE_OPENAI_FUNCTIONS",
        "DEBUG_MODE"
    ]
    
    log_info("=== Environment Variables Check ===")
    for var in required_env_vars:
        if os.getenv(var):
            log_success(f"{var}: ✓ Set")
        else:
            log_error(f"{var}: ✗ Missing (required)")
    
    for var in optional_env_vars:
        value = os.getenv(var, "not_set")
        log_info(f"{var}: {value}")
    
    # 3. Check Python package versions
    log_info("=== Package Version Checks ===")
    critical_packages = [
        "openai",
        "twilio",
        "aiohttp",
        "pandas"
    ]
    
    for package in critical_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                # Try to import and get version
                module = importlib.import_module(package)
                version = getattr(module, "__version__", "version_unknown")
                log_success(f"{package}: {version} ✓")
            else:
                log_error(f"{package}: Not found ✗")
        except ImportError as e:
            log_error(f"{package}: Import error - {e}")
        except Exception as e:
            log_warning(f"{package}: Version check failed - {e}")
    
    # 4. Specific OpenAI client test
    log_info("=== OpenAI Client Test ===")
    try:
        from openai import OpenAI
        log_success("OpenAI import successful")
        
        # Test client creation without any arguments (most basic)
        log_info("Testing basic OpenAI() client creation...")
        try:
            test_client = OpenAI()
            log_success("Basic OpenAI() client creation successful")
            
            # Clean up
            del test_client
            
        except TypeError as e:
            log_error(f"OpenAI client creation failed with TypeError: {e}")
            if "proxies" in str(e):
                log_error("⚠️  This is the 'proxies' error - OpenAI library version incompatibility")
                log_error("⚠️  Recommendation: Update OpenAI library to >= 1.51.2")
            return False
        except Exception as e:
            log_error(f"OpenAI client creation failed: {e}")
            return False
            
    except ImportError as e:
        log_error(f"OpenAI import failed: {e}")
        return False
    
    # 5. Check if Signal SP Session directory exists and has server.py
    signal_sp_path = os.path.join(os.getcwd(), "Signal SP Session")
    if os.path.exists(signal_sp_path):
        log_success(f"Signal SP Session directory found: {signal_sp_path}")
        
        server_py_path = os.path.join(signal_sp_path, "server.py")
        if os.path.exists(server_py_path):
            log_success("server.py found in Signal SP Session directory")
        else:
            log_error("server.py NOT found in Signal SP Session directory")
            return False
    else:
        log_error("Signal SP Session directory NOT found")
        return False
    
    # 6. If all checks pass, start the actual server
    log_success("=== All diagnostic checks passed! ===")
    log_info("Starting Signal SP Session server...")
    
    # Change to Signal SP Session directory and run server
    try:
        os.chdir(signal_sp_path)
        log_info(f"Changed directory to: {os.getcwd()}")
        
        # Use subprocess to run the server with proper error handling
        import subprocess
        result = subprocess.run([sys.executable, "server.py"], check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        log_error(f"Server startup failed with exit code {e.returncode}")
        return False
    except Exception as e:
        log_error(f"Server startup error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        log_error("Diagnostic startup failed - see errors above")
        sys.exit(1)