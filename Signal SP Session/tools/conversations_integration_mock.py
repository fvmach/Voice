# conversations_integration_mock.py
# Mock integration with Conversations Manager for testing

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ConversationsManagerClient:
    """Mock client for integrating with Conversations Manager API"""
    
    def __init__(self, base_url: str = "http://localhost:3001/api"):
        self.base_url = base_url
        self.conversation_cache = {}  # Cache active conversations by phone
    
    async def close_session(self):
        """Mock close aiohttp session"""
        pass
    
    async def create_voice_conversation(self, customer_phone: str, call_sid: str, agent_name: str = "Olli") -> Optional[str]:
        """Mock create a new conversation for a voice call"""
        try:
            # Mock conversation SID
            conversation_sid = f"CH_mock_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Cache the conversation
            self.conversation_cache[customer_phone] = {
                "sid": conversation_sid,
                "call_sid": call_sid,
                "created_at": datetime.now(timezone.utc)
            }
            
            logger.info(f"[CONV] Mock created voice conversation {conversation_sid} for {customer_phone}")
            return conversation_sid
                    
        except Exception as e:
            logger.error(f"[CONV] Exception creating voice conversation: {e}")
            return None
    
    async def send_message(self, customer_phone: str, body: str, author: str = "system", message_type: str = "text", attributes: Dict = None) -> bool:
        """Mock send a message to the voice conversation"""
        try:
            conversation_info = self.conversation_cache.get(customer_phone)
            if not conversation_info:
                logger.warning(f"[CONV] No active conversation found for {customer_phone}")
                return False
            
            logger.debug(f"[CONV] Mock sent message from {author}: {body[:50]}...")
            return True
                    
        except Exception as e:
            logger.error(f"[CONV] Exception sending message: {e}")
            return False
    
    async def send_function_call_message(self, customer_phone: str, function_name: str, arguments: Dict, result: Dict) -> bool:
        """Mock send function call message with result"""
        try:
            logger.info(f"[CONV] Mock logged function call {function_name} for {customer_phone}")
            return True
            
        except Exception as e:
            logger.error(f"[CONV] Exception sending function call message: {e}")
            return False

class VoiceConversationManager:
    """Mock high-level manager for voice conversation integration"""
    
    def __init__(self, conversations_client: ConversationsManagerClient = None):
        self.client = conversations_client or ConversationsManagerClient()
        self.active_conversations = {}  # Track conversation states
    
    async def start_voice_conversation(self, customer_phone: str, call_sid: str, agent_name: str = "Olli") -> bool:
        """Mock start a new voice conversation"""
        conversation_sid = await self.client.create_voice_conversation(customer_phone, call_sid, agent_name)
        if conversation_sid:
            self.active_conversations[customer_phone] = {
                "conversation_sid": conversation_sid,
                "call_sid": call_sid,
                "agent": agent_name,
                "started_at": datetime.now(timezone.utc)
            }
            return True
        return False
    
    async def log_user_speech(self, customer_phone: str, speech_text: str) -> bool:
        """Mock log user speech to conversation"""
        return await self.client.send_message(customer_phone, speech_text, "user", "speech")
    
    async def log_agent_response(self, customer_phone: str, response_text: str) -> bool:
        """Mock log agent response to conversation"""
        return await self.client.send_message(customer_phone, response_text, "assistant", "response")
    
    async def log_function_call(self, customer_phone: str, function_name: str, arguments: Dict, result: Dict) -> bool:
        """Mock log function call to conversation"""
        return await self.client.send_function_call_message(customer_phone, function_name, arguments, result)
    
    async def close(self):
        """Mock close all resources"""
        await self.client.close_session()
