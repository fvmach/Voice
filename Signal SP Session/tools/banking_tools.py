# banking_tools.py
# Simple banking tools that can be called directly

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import re
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class BankingTools:
    """Simple banking tools that can be invoked by text analysis"""
    
    def __init__(self, base_url: str = "https://owl-bank-finserv-demo-1-1-8657.twil.io"):
        self.base_url = base_url
    
    def detect_banking_intent(self, text: str) -> Optional[str]:
        """Detect if user wants banking information"""
        text_lower = text.lower()
        
        # Account balance patterns
        balance_patterns = [
            r'(saldo|balance|conta|account)',
            r'(quanto|how much|cuanto).*(tenho|have|dinheiro|money)',
            r'(consulta|check|ver).*(conta|account|saldo|balance)'
        ]
        
        # Transfer patterns  
        transfer_patterns = [
            r'(transfer|transferir|enviar|send).*(dinheiro|money|reais)',
            r'(pix|PIX)',
            r'(mandar|enviar).*(para|to|pra)'
        ]
        
        for pattern in balance_patterns:
            if re.search(pattern, text_lower):
                return "check_balance"
        
        for pattern in transfer_patterns:
            if re.search(pattern, text_lower):
                return "transfer_money"
                
        return None
    
    def _normalize_user_id(self, customer_phone: str) -> str:
        """Derive the userId expected by the banking API from the caller identifier."""
        # If Conversation Relay sends identifiers like "client:email@example.com", strip the prefix
        if customer_phone.startswith("client:"):
            possible_email = customer_phone.split(":", 1)[1]
            if "@" in possible_email:
                return possible_email
        # If it's already an email, keep it
        if "@" in customer_phone:
            return customer_phone
        # Fallback demo user
        return "owl.anunes@gmail.com"
    
    def get_banking_data(self, customer_phone: str) -> Dict[str, Any]:
        """Get banking data from the Owl Bank demo API using the standard library (no external deps)."""
        try:
            user_id = self._normalize_user_id(customer_phone)
            url = f"{self.base_url}/get-banking-data"
            payload = json.dumps({"userId": user_id}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                status = resp.getcode()
                body = resp.read().decode("utf-8")
                if status == 200:
                    data = json.loads(body)
                    logger.info(f"[BANK] Retrieved banking data for {customer_phone} (as {user_id})")
                    return {"success": True, "data": data, "message": "Banking data retrieved successfully"}
                else:
                    logger.error(f"[BANK] API error {status}: {body}")
                    return {"success": False, "error": f"API error {status}", "message": "Could not retrieve banking data"}
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = str(e)
            logger.error(f"[BANK] HTTPError getting banking data for {customer_phone}: {e.code} {body}")
            return {"success": False, "error": f"http_{e.code}", "message": body}
        except urllib.error.URLError as e:
            logger.error(f"[BANK] URLError getting banking data for {customer_phone}: {e}")
            return {"success": False, "error": "network_error", "message": str(e)}
        except Exception as e:
            logger.error(f"[BANK] Exception getting banking data: {e}")
            return {"success": False, "error": "exception", "message": str(e)}
    
    def format_balance_response(self, banking_data: Dict[str, Any], language: str = "pt-BR") -> str:
        """Format banking data into a natural language response"""
        if not banking_data.get("success"):
            if language == "pt-BR":
                return "Desculpe, não consegui acessar os dados da sua conta no momento."
            else:
                return "Sorry, I couldn't access your account information at the moment."
        
        data = banking_data.get("data", {})
        # The API returns balance, creditDebt, loyaltyPoints directly
        balance = data.get("balance", 0)
        credit_debt = data.get("creditDebt", 0)
        loyalty_points = data.get("loyaltyPoints", 0)
        
        if language == "pt-BR":
            response = f"Seu saldo atual é R$ {balance:,.2f}."
            
            if credit_debt > 0:
                response += f" Você tem uma dívida no cartão de crédito de R$ {credit_debt:,.2f}."
            
            if loyalty_points > 0:
                response += f" Seus pontos de fidelidade são {loyalty_points:,} pontos."
        else:
            response = f"Your current balance is R$ {balance:,.2f}."
            
            if credit_debt > 0:
                response += f" You have a credit card debt of R$ {credit_debt:,.2f}."
            
            if loyalty_points > 0:
                response += f" Your loyalty points are {loyalty_points:,} points."
        
        return response
    
    def process_user_input(self, text: str, customer_phone: str, language: str = "pt-BR") -> Optional[str]:
        """Process user input and return banking response if applicable"""
        intent = self.detect_banking_intent(text)
        
        if intent == "check_balance":
            logger.info(f"[BANK] Detected balance check request from {customer_phone}")
            banking_data = self.get_banking_data(customer_phone)
            return self.format_balance_response(banking_data, language)
        
        elif intent == "transfer_money":
            if language == "pt-BR":
                return "Para fazer transferências, preciso de mais informações. Para qual conta ou PIX você gostaria de transferir?"
            else:
                return "To make transfers, I need more information. Which account or PIX would you like to transfer to?"
        
        return None

# Initialize global banking tools instance
banking_tools = BankingTools()

def get_banking_tools() -> BankingTools:
    """Get the banking tools instance"""
    return banking_tools
