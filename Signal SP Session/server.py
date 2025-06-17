import asyncio
import websockets
import json
import logging
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import deque
from openai import OpenAI
import os
from dotenv import load_dotenv
from aiohttp import web, WSMsgType
import aiohttp_cors

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationConfig:
    """Configuration for conversation handling"""
    sentence_end_patterns = ['.', '!', '?', '\n']
    partial_timeout = 1.5  # seconds to wait for more partials
    max_buffer_size = 1000
    openai_model = "gpt-4o-2024-11-20"

class ConversationBuffer:
    """Manages buffering of partial speech-to-text results"""
    
    def __init__(self, config: ConversationConfig):
        self.config = config
        self.buffer = ""
        self.last_update = None
        self.sentence_queue = deque()
        
    def add_partial(self, text: str) -> None:
        """Add partial text to buffer"""
        self.buffer = text
        self.last_update = asyncio.get_event_loop().time()
        
    def add_final(self, text: str) -> Optional[str]:
        """Add final text and check if we have a complete sentence"""
        self.buffer = text
        
        # Check for sentence endings
        for pattern in self.config.sentence_end_patterns:
            if pattern in text:
                sentence = text.strip()
                if sentence:
                    self.clear()
                    return sentence
        return None
        
    def get_if_timeout(self) -> Optional[str]:
        """Get buffer content if timeout reached"""
        if (self.last_update and 
            asyncio.get_event_loop().time() - self.last_update > self.config.partial_timeout):
            if self.buffer.strip():
                sentence = self.buffer.strip()
                self.clear()
                return sentence
        return None
        
    def clear(self) -> None:
        """Clear the buffer"""
        self.buffer = ""
        self.last_update = None

class LLMClient:
    """Handles communication with OpenAI API"""
    
    def __init__(self, config: ConversationConfig):
        self.config = config
        self.client = OpenAI()
        
    async def initialize(self):
        """Initialize OpenAI client"""
        pass
        
    async def close(self):
        """Close OpenAI client"""
        pass
            
    async def get_completion(self, text: str) -> str:
        """Get completion from OpenAI API"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant speaking in Brazilian Portuguese. Keep responses concise and conversational."},
                        {"role": "user", "content": text}
                    ]
                )
            )
            
            return response.choices[0].message.content
                    
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "Desculpe, encontrei um erro ao processar sua solicitação."

class TwilioWebSocketHandler:
    """Handles Twilio Conversation Relay WebSocket messages"""
    
    def __init__(self):
        self.config = ConversationConfig()
        self.buffer = ConversationBuffer(self.config)
        self.llm_client = LLMClient(self.config)
        self.websocket = None
        self.conversation_sid = None
        
    async def handle_websocket(self, request):
        """Handle WebSocket connection via aiohttp"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket = ws
        logger.info("New WebSocket connection established")
        
        try:
            await self.llm_client.initialize()
            
            # Start timeout checker task
            timeout_task = asyncio.create_task(self.check_timeouts())
            
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.route_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            timeout_task.cancel()
            await self.llm_client.close()
            logger.info("WebSocket connection closed")
            
        return ws
        
    async def route_message(self, message: str):
        """Route messages to appropriate handlers based on event type"""
        try:
            data = json.loads(message)
            event_type = data.get("event")
            
            logger.info(f"Received event: {event_type}")
            logger.debug(f"Full message: {data}")
            
            # Route Conversation Relay events specifically
            if event_type in ["setup", "interrupt", "utterance", "dtmf"]:
                await self.handle_conversation_relay_event(data)
            # Handle other event types (Media Streams, etc.) - ignore for now
            elif event_type in ["connected", "start", "media", "stop"]:
                logger.info(f"Ignoring non-Conversation Relay event: {event_type}")
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            logger.error(f"Raw message: {message}")
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            
    async def handle_conversation_relay_event(self, data: Dict[str, Any]):
        """Handle Conversation Relay specific events"""
        event_type = data.get("event")
        
        if event_type == "setup":
            await self.handle_setup(data)
        elif event_type == "utterance":
            await self.handle_utterance(data)
        elif event_type == "interrupt":
            await self.handle_interrupt(data)
        elif event_type == "dtmf":
            await self.handle_dtmf(data)
        else:
            logger.warning(f"Unhandled Conversation Relay event: {event_type}")
            
    async def handle_setup(self, data: Dict[str, Any]):
        """Handle setup event from Conversation Relay"""
        logger.info(f"Conversation Relay setup: {data}")
        
        conversation = data.get("conversation", {})
        self.conversation_sid = conversation.get("sid")
        
        logger.info(f"Conversation SID: {self.conversation_sid}")
        
    async def handle_utterance(self, data: Dict[str, Any]):
        """Handle utterance events (speech-to-text results)"""
        utterance = data.get("utterance", {})
        
        utterance_type = utterance.get("type")
        text = utterance.get("text", "")
        
        logger.info(f"Utterance - Type: {utterance_type}, Text: '{text}'")
        
        if utterance_type == "partial":
            self.buffer.add_partial(text)
        elif utterance_type == "final":
            sentence = self.buffer.add_final(text)
            if sentence:
                await self.process_complete_input(sentence)
                
    async def handle_interrupt(self, data: Dict[str, Any]):
        """Handle interrupt events"""
        logger.info(f"Interrupt received: {data}")
        self.buffer.clear()
        
    async def handle_dtmf(self, data: Dict[str, Any]):
        """Handle DTMF events"""
        dtmf = data.get("dtmf", {})
        digit = dtmf.get("digit")
        
        logger.info(f"DTMF received: {digit}")
        
        if digit:
            await self.process_complete_input(f"User pressed {digit}")
        
    async def check_timeouts(self):
        """Periodically check for timeouts in partial results"""
        while True:
            try:
                await asyncio.sleep(0.1)
                sentence = self.buffer.get_if_timeout()
                if sentence:
                    await self.process_complete_input(sentence)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in timeout checker: {e}")
                
    async def process_complete_input(self, text: str):
        """Process complete input sentence with LLM"""
        logger.info(f"Processing complete input: {text}")
        
        try:
            response = await self.llm_client.get_completion(text)
            logger.info(f"LLM Response: {response}")
            
            await self.send_response(response)
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            
    async def send_response(self, text: str):
        """Send response back to Conversation Relay"""
        if not self.websocket:
            logger.error("No websocket connection available")
            return
            
        message = {
            "event": "response",
            "response": {
                "text": text
            }
        }
        
        try:
            await self.websocket.send_str(json.dumps(message))
            logger.info(f"Response sent: {text}")
            
        except Exception as e:
            logger.error(f"Error sending response: {e}")

async def handle_event_streams_webhook(request):
    """Handle HTTP POST requests from Event Streams"""
    try:
        # Get the request body
        body = await request.text()
        logger.info(f"Event Streams webhook received: {body}")
        
        # Parse JSON if it's JSON
        try:
            data = await request.json()
            logger.info(f"Event Streams data: {data}")
        except:
            logger.info(f"Event Streams raw body: {body}")
        
        # Return success response
        return web.Response(text="OK", status=200)
        
    except Exception as e:
        logger.error(f"Error handling Event Streams webhook: {e}")
        return web.Response(text="Error", status=500)

async def main():
    """Main server function using aiohttp"""
    
    # Create WebSocket handler
    ws_handler = TwilioWebSocketHandler()
    
    # Create aiohttp app
    app = web.Application()
    
    # Add CORS support
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Add routes
    app.router.add_get('/websocket', ws_handler.handle_websocket)  # WebSocket for Conversation Relay
    app.router.add_post('/webhook', handle_event_streams_webhook)  # HTTP for Event Streams
    app.router.add_post('/events', handle_event_streams_webhook)   # Alternative path
    app.router.add_get('/', lambda request: web.Response(text="Twilio WebSocket/HTTP Server Running"))
    
    # Add CORS to all routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Start server
    host = "localhost"
    port = 8080
    
    logger.info(f"Starting Twilio WebSocket/HTTP server on {host}:{port}")
    logger.info(f"WebSocket endpoint: ws://{host}:{port}/websocket")
    logger.info(f"HTTP webhook endpoint: http://{host}:{port}/webhook")
    
    # Run the server
    await web._run_app(app, host=host, port=port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
