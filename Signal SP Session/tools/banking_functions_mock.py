# banking_functions_mock.py
# Mock banking API integration for testing and demonstration

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import asyncio
import random

logger = logging.getLogger(__name__)

class BankingAPIClient:
    """Mock client for Owl Bank API integration"""
    
    def __init__(self, base_url: str = "https://owl-bank-finserv-demo-1-1-8657.twil.io"):
        self.base_url = base_url
    
    async def get_banking_data(self, customer_phone: str) -> Dict[str, Any]:
        """Mock get customer banking data"""
        await asyncio.sleep(0.1)  # Simulate API call latency
        
        # Mock data based on phone number
        account_balance = round(random.uniform(100, 10000), 2)
        
        mock_data = {
            "account": {
                "balance": account_balance,
                "currency": "BRL",
                "account_number": f"****{customer_phone[-4:]}",
                "status": "active"
            },
            "recent_transactions": [
                {
                    "id": "tx_001",
                    "type": "credit",
                    "amount": 250.00,
                    "description": "Salary deposit",
                    "date": "2024-01-15"
                },
                {
                    "id": "tx_002", 
                    "type": "debit",
                    "amount": 89.50,
                    "description": "Grocery store",
                    "date": "2024-01-14"
                }
            ]
        }
        
        logger.info(f"[BANK] Mock banking data retrieved for {customer_phone}")
        return {
            "success": True,
            "data": mock_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def transfer_money(self, from_account: str, to_account: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Mock money transfer"""
        await asyncio.sleep(0.2)  # Simulate transfer processing
        
        transfer_id = f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[BANK] Mock transfer: {amount} BRL from {from_account} to {to_account}")
        return {
            "success": True,
            "data": {
                "transfer_id": transfer_id,
                "amount": amount,
                "from_account": from_account,
                "to_account": to_account,
                "description": description,
                "status": "completed"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def pix_transfer(self, pix_key: str, amount: float, description: str = "") -> Dict[str, Any]:
        """Mock PIX transfer"""
        await asyncio.sleep(0.15)  # Simulate PIX processing
        
        pix_id = f"pix_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"[BANK] Mock PIX transfer: {amount} BRL to {pix_key}")
        return {
            "success": True,
            "data": {
                "pix_id": pix_id,
                "amount": amount,
                "pix_key": pix_key,
                "description": description,
                "status": "completed",
                "recipient_name": "João Silva"  # Mock recipient
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def close_session(self):
        """Mock close session"""
        pass

# OpenAI Function Definitions for banking operations
BANKING_FUNCTION_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_account_balance",
            "description": "Get customer's current account balance and recent transactions",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number in E.164 format (e.g., +5511999887766)"
                    }
                },
                "required": ["customer_phone"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_money",
            "description": "Transfer money between accounts",
            "parameters": {
                "type": "object",
                "properties": {
                    "to_account": {
                        "type": "string",
                        "description": "Recipient account number or identifier"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to transfer (in BRL)"
                    },
                    "description": {
                        "type": "string",
                        "description": "Transfer description or memo"
                    }
                },
                "required": ["to_account", "amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pix_transfer",
            "description": "Perform PIX transfer using PIX key (phone, email, CPF, or random key)",
            "parameters": {
                "type": "object",
                "properties": {
                    "pix_key": {
                        "type": "string",
                        "description": "PIX key (phone number, email, CPF, or random key)"
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to transfer via PIX (in BRL)"
                    },
                    "description": {
                        "type": "string",
                        "description": "PIX transfer description"
                    }
                },
                "required": ["pix_key", "amount"]
            }
        }
    }
]

class BankingFunctionHandler:
    """Mock handler for banking function calls from OpenAI"""
    
    def __init__(self):
        self.api_client = BankingAPIClient()
    
    async def handle_function_call(self, function_name: str, arguments: Dict[str, Any], customer_phone: str = None) -> Dict[str, Any]:
        """Handle function call and return response"""
        try:
            if function_name == "get_account_balance":
                phone = arguments.get("customer_phone") or customer_phone
                if not phone:
                    return {"error": "Customer phone number required"}
                return await self.api_client.get_banking_data(phone)
            
            elif function_name == "transfer_money":
                if not customer_phone:
                    return {"error": "Customer phone number required for transfers"}
                
                return await self.api_client.transfer_money(
                    from_account=customer_phone,
                    to_account=arguments["to_account"],
                    amount=arguments["amount"],
                    description=arguments.get("description", "")
                )
            
            elif function_name == "pix_transfer":
                return await self.api_client.pix_transfer(
                    pix_key=arguments["pix_key"],
                    amount=arguments["amount"],
                    description=arguments.get("description", "")
                )
            
            else:
                return {"error": f"Unknown function: {function_name}"}
        
        except Exception as e:
            logger.error(f"[BANK] Function call error: {e}")
            return {"error": "Function call failed", "message": str(e)}
    
    async def close(self):
        """Close API client session"""
        await self.api_client.close_session()
