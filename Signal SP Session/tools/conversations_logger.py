# conversations_logger.py
# Simple conversations logger for voice calls

import requests
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ConversationsLogger:
    """Simple logger for voice conversations to Conversations Manager"""
    
    def __init__(self, base_url: str = "http://localhost:3001/api"):
        self.base_url = base_url
        self.active_conversations = {}  # Track conversations by phone
    
    def create_voice_conversation(self, customer_phone: str, call_sid: str, agent_name: str = "Olli") -> Optional[str]:
        """Create a new conversation for a voice call"""
        try:
            conversation_data = {
                "friendlyName": f"Voice Call - {customer_phone}",
                "uniqueName": f"voice_{call_sid}",
                "attributes": {
                    "channel": "voice",
                    "customer_phone": customer_phone,
                    "call_sid": call_sid,
                    "agent": agent_name,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "status": "active"
                }
            }
            
            response = requests.post(f"{self.base_url}/conversations", json=conversation_data, timeout=5)
            
            if response.status_code == 201:
                data = response.json()
                conversation_sid = data["sid"]
                
                # Cache the conversation
                self.active_conversations[customer_phone] = {
                    "conversation_sid": conversation_sid,
                    "call_sid": call_sid,
                    "agent": agent_name,
                    "created_at": datetime.now(timezone.utc)
                }
                
                # Add participant
                self.add_voice_participant(conversation_sid, customer_phone)
                
                logger.info(f"[CONV] Created voice conversation {conversation_sid} for {customer_phone}")
                return conversation_sid
            else:
                logger.error(f"[CONV] Failed to create conversation: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"[CONV] Exception creating conversation: {e}")
            return None
    
    def add_voice_participant(self, conversation_sid: str, customer_phone: str):
        """Add voice participant to conversation"""
        try:
            participant_data = {
                "identity": f"voice:{customer_phone}",
                "attributes": {
                    "channel": "voice",
                    "phone": customer_phone,
                    "role": "customer"
                }
            }
            
            response = requests.post(f"{self.base_url}/participants/{conversation_sid}", json=participant_data, timeout=5)
            
            if response.status_code == 201:
                logger.info(f"[CONV] Added voice participant {customer_phone}")
            else:
                logger.warning(f"[CONV] Failed to add participant: {response.status_code}")
                
        except Exception as e:
            logger.error(f"[CONV] Exception adding participant: {e}")
    
    def log_message(self, customer_phone: str, body: str, author: str = "system", message_type: str = "text", extra_data: Dict = None) -> bool:
        """Log a message to the voice conversation"""
        try:
            conversation_info = self.active_conversations.get(customer_phone)
            if not conversation_info:
                logger.warning(f"[CONV] No active conversation for {customer_phone}")
                return False
            
            conversation_sid = conversation_info["conversation_sid"]
            
            message_data = {
                "body": body,
                "author": author,
                "attributes": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "message_type": message_type,
                    "channel": "voice",
                    **(extra_data or {})
                }
            }
            
            response = requests.post(f"{self.base_url}/messages/{conversation_sid}", json=message_data, timeout=5)
            
            if response.status_code == 201:
                logger.debug(f"[CONV] Logged message from {author}")
                return True
            else:
                logger.error(f"[CONV] Failed to log message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"[CONV] Exception logging message: {e}")
            return False
    
    def log_user_speech(self, customer_phone: str, speech_text: str) -> bool:
        """Log user speech"""
        return self.log_message(customer_phone, speech_text, "user", "speech")
    
    def log_agent_response(self, customer_phone: str, response_text: str) -> bool:
        """Log agent response"""
        return self.log_message(customer_phone, response_text, "assistant", "response")
    
    def log_banking_action(self, customer_phone: str, action: str, result: Dict) -> bool:
        """Log banking action"""
        message = f"🏦 Banking Action: {action}"
        return self.log_message(customer_phone, message, "system", "banking_action", {
            "banking_action": action,
            "result": result
        })

# Initialize global conversations logger
conversations_logger = ConversationsLogger()

def get_conversations_logger() -> ConversationsLogger:
    """Get the conversations logger instance"""
    return conversations_logger
