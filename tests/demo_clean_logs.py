#!/usr/bin/env python3
"""
Demo script to show clean logging output without intrusive Twilio SDK logs
"""

import os
import sys
import logging
from datetime import datetime, timezone

# Set up clean environment (simulating production mode)
os.environ['DEBUG_MODE'] = 'false'

# Add current directory to path so we can import server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_clean_logging():
    """Demonstrate the clean logging output"""
    print("=== Clean Logging Demo ===\n")
    
    try:
        # Import server components
        from server import twilio_client, logger, DEBUG_MODE
        from colorama import Fore, Style
        
        print(f"Debug Mode: {DEBUG_MODE}")
        print(f"Clean Logging: {'Enabled' if not DEBUG_MODE else 'Disabled'}")
        print()
        
        # Show clean log examples
        logger.info(f"{Fore.BLUE}[SYS] Server started with clean logging{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[TRANSCRIPT] Real-time transcription ready{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}[TWIML] Voice endpoint configured{Style.RESET_ALL}")
        logger.info(f"{Fore.MAGENTA}[SPI] WebSocket handler initialized{Style.RESET_ALL}")
        
        print("\n=== Testing Twilio Client (Should be Silent) ===")
        
        # This should now be silent (no HTTP request logs)
        try:
            # Get account info - this will make an HTTP request but shouldn't log it
            account = twilio_client.api.accounts.get()
            logger.info(f"{Fore.GREEN}[SYS] Twilio client connected to account: {account.sid[:8]}...{Style.RESET_ALL}")
        except Exception as e:
            logger.info(f"{Fore.YELLOW}[WARN] Twilio client test failed (expected if no credentials): {str(e)[:50]}...{Style.RESET_ALL}")
        
        print()
        logger.info(f"{Fore.BLUE}[SYS] Clean logging demo completed{Style.RESET_ALL}")
        print("\nSuccess: No intrusive HTTP logs should appear above!")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Note: This demo requires the server dependencies to be installed")
        
    except Exception as e:
        print(f"Error: {e}")

def show_comparison():
    """Show the difference between debug and production logging"""
    print("\n=== Logging Comparison ===")
    print()
    
    print("DEBUG_MODE=true (Verbose):")
    print("- Shows all HTTP requests and responses")
    print("- Displays detailed headers and payloads")
    print("- Shows aiohttp access logs")
    print("- Includes urllib3 connection details")
    print()
    
    print("DEBUG_MODE=false (Clean - Default):")
    print("- Only colorama-formatted application logs")
    print("- No HTTP request/response details")
    print("- No access logs")
    print("- Clean, demo-friendly output")
    print()
    
    print("To enable verbose logging:")
    print("   Set DEBUG_MODE=true in your .env file")

if __name__ == "__main__":
    demo_clean_logging()
    show_comparison()
