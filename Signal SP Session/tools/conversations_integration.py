# conversations_integration.py
# Integration with Conversations Manager for voice call logging

import json
import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ConversationsManagerClient:
    """Client for integrating with Conversations Manager API"""
    
    def __init__(self, base_url: str = "http://localhost:3001/api"):
        self.base_url = base_url
        self.session = None
        self.conversation_cache = {}  # Cache active conversations by phone
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10.0),
                headers={"Content-Type": "application/json"}
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def create_voice_conversation(self, customer_phone: str, call_sid: str, agent_name: str = "Olli") -> Optional[str]:
        """Create a new conversation for a voice call"""
        try:
            session = await self.get_session()
            
            # Create conversation with voice identity
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
            
            async with session.post(f"{self.base_url}/conversations", json=conversation_data) as response:
                if response.status == 201:
                    data = await response.json()
                    conversation_sid = data["sid"]
                    logger.info(f"[CONV] Created voice conversation {conversation_sid} for {customer_phone}")
                    
                    # Cache the conversation
                    self.conversation_cache[customer_phone] = {
                        "sid": conversation_sid,
                        "call_sid": call_sid,
                        "created_at": datetime.now(timezone.utc)
                    }
                    
                    # Add voice participant
                    await self.add_voice_participant(conversation_sid, customer_phone)
                    
                    return conversation_sid
                else:
                    error_text = await response.text()
                    logger.error(f"[CONV] Failed to create conversation: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"[CONV] Exception creating voice conversation: {e}")
            return None
    
    async def add_voice_participant(self, conversation_sid: str, customer_phone: str):
        """Add voice participant to conversation"""
        try:
            session = await self.get_session()
            
            participant_data = {
                "identity": f"voice:{customer_phone}",
                "attributes": {
                    "channel": "voice",
                    "phone": customer_phone,
                    "role": "customer"
                }
            }
            
            async with session.post(f"{self.base_url}/participants/{conversation_sid}", json=participant_data) as response:
                if response.status == 201:
                    logger.info(f"[CONV] Added voice participant {customer_phone} to {conversation_sid}")
                else:
                    error_text = await response.text()
                    logger.warning(f"[CONV] Failed to add participant: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"[CONV] Exception adding voice participant: {e}")
    
    async def send_message(self, customer_phone: str, body: str, author: str = "system", message_type: str = "text", attributes: Dict = None) -> bool:
        """Send a message to the voice conversation"""
        try:
            conversation_info = self.conversation_cache.get(customer_phone)
            if not conversation_info:
                logger.warning(f"[CONV] No active conversation found for {customer_phone}")
                return False
            
            conversation_sid = conversation_info["sid"]
            session = await self.get_session()
            
            message_attributes = attributes or {}
            message_attributes.update({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message_type": message_type,
                "channel": "voice"
            })
            
            message_data = {
                "body": body,
                "author": author,
                "attributes": message_attributes
            }
            
            async with session.post(f"{self.base_url}/messages/{conversation_sid}", json=message_data) as response:
                if response.status == 201:
                    logger.debug(f"[CONV] Sent message from {author} to {conversation_sid}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"[CONV] Failed to send message: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"[CONV] Exception sending message: {e}")
            return False
    
    async def send_function_call_message(self, customer_phone: str, function_name: str, arguments: Dict, result: Dict) -> bool:
        """Send function call message with result"""
        try:
            function_message = f"🔧 Using {function_name}"
            attributes = {
                "function_call": {
                    "name": function_name,
                    "arguments": arguments,
                    "result": result,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "message_type": "function_call"
            }
            
            return await self.send_message(customer_phone, function_message, "system", "function_call", attributes)
            
        except Exception as e:
            logger.error(f"[CONV] Exception sending function call message: {e}")
            return False

class VoiceConversationManager:
    """High-level manager for voice conversation integration"""
    
    def __init__(self, conversations_client: ConversationsManagerClient = None):
        self.client = conversations_client or ConversationsManagerClient()
        self.active_conversations = {}  # Track conversation states
    
    async def start_voice_conversation(self, customer_phone: str, call_sid: str, agent_name: str = "Olli") -> bool:
        """Start a new voice conversation"""
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
        """Log user speech to conversation"""
        return await self.client.send_message(customer_phone, speech_text, "user", "speech")
    
    async def log_agent_response(self, customer_phone: str, response_text: str) -> bool:
        """Log agent response to conversation"""
        return await self.client.send_message(customer_phone, response_text, "assistant", "response")
    
    async def log_function_call(self, customer_phone: str, function_name: str, arguments: Dict, result: Dict) -> bool:
        """Log function call to conversation"""
        return await self.client.send_function_call_message(customer_phone, function_name, arguments, result)
    
    async def close(self):
        """Close all resources"""
        await self.client.close_session()
