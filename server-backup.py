import asyncio
import json
import logging
import aiohttp_cors
from typing import Dict, Any, Optional
from dataclasses import dataclass
from openai import OpenAI
import os
from dotenv import load_dotenv
from aiohttp import web, WSMsgType

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ConversationConfig:
    sentence_end_patterns = ['.', '!', '?', '\n']
    partial_timeout = 1.5
    max_buffer_size = 1000
    openai_model = "gpt-4o"

class LLMClient:
    def __init__(self, config: ConversationConfig):
        self.config = config
        self.client = OpenAI()

    async def initialize(self):
        pass

    async def close(self):
        pass

    async def get_completion(self, text: str) -> str:
        try:
            logger.info(f"[OpenAI] Sending prompt: {text}")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant named Olli (Óli in pt_BR) speaking in Brazilian Portuguese with Twilio customers through voice conversations (phone calls). Keep responses concise and conversational and avoid formatting and special characters like emojis."},
                        {"role": "user", "content": text}
                    ]
                )
            )
            logger.info(f"[OpenAI] Raw response: {response}")
            result = response.choices[0].message.content.strip()
            logger.info(f"[OpenAI] Completion result: {result}")
            return result
        except Exception as e:
            logger.error(f"[OpenAI] API error: {e}")
            return "Desculpe, encontrei um erro ao processar sua solicitação."

class TwilioWebSocketHandler:
    def __init__(self):
        self.config = ConversationConfig()
        self.llm_client = LLMClient(self.config)
        self.websocket = None
        self.conversation_sid = None

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websocket = ws
        logger.info("New WebSocket connection established")

        try:
            await self.llm_client.initialize()
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.route_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.llm_client.close()
            logger.info("WebSocket connection closed")
        return ws

    async def route_message(self, message: str):
        try:
            data = json.loads(message)
            event_type = data.get("event") or data.get("type")
            if event_type is None:
                logger.warning(f"Missing 'event' field in message: {data}")
            else:
                await self.handle_conversation_relay_event(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error routing message: {e}")

    async def handle_conversation_relay_event(self, data: Dict[str, Any]):
        event_type = data.get("event") or data.get("type")
        if not event_type:
            logger.warning(f"No 'event' field found in: {data}")
            return

        match event_type:
            case "setup":
                await self.handle_setup(data)
            case "prompt":
                await self.handle_prompt(data)
            case "interrupt":
                await self.handle_interrupt(data)
            case "dtmf":
                await self.handle_dtmf(data)
            case _:
                logger.warning(f"Unhandled Conversation Relay event: {event_type}")

    async def handle_setup(self, data: Dict[str, Any]):
        logger.info(f"Conversation Relay setup: {data}")
        self.conversation_sid = data.get("callSid")
        logger.info(f"Conversation SID: {self.conversation_sid}")

    async def handle_prompt(self, data: Dict[str, Any]):
        text = data.get("voicePrompt", "")
        logger.info(f"[Prompt Transcription] {text}")
        if text.strip():
            await self.process_complete_input(text)

    async def handle_interrupt(self, data: Dict[str, Any]):
        logger.info(f"Interrupt received: {data}")

    async def handle_dtmf(self, data: Dict[str, Any]):
        digit = data.get("digit")
        logger.info(f"DTMF received: {digit}")
        if digit:
            await self.process_complete_input(f"User pressed {digit}")

    async def process_complete_input(self, text: str):
        logger.info(f"Processing complete input: {text}")
        try:
            response_text = await self.llm_client.get_completion(text)
            await self.send_response(response_text)
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            await self.send_response("Desculpe, não consegui processar sua solicitação.")

    async def send_response(self, text: str):
        if not self.websocket:
            logger.error("No WebSocket connection available")
            return
        message = {
            "type": "text",
            "token": text,
            "last": True,
            "interruptible": False,
            "preemptible": False
        }
        try:
            await self.websocket.send_str(json.dumps(message))
            logger.info(f"[TTS Response Sent] {message}")
        except Exception as e:
            logger.error(f"Error sending TTS response: {e}")

async def handle_event_streams_webhook(request):
    try:
        body = await request.text()
        logger.info(f"Event Streams webhook received: {body}")
        try:
            data = await request.json()
            logger.info(f"Event Streams data: {data}")
        except:
            logger.info(f"Event Streams raw body: {body}")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"Error handling Event Streams webhook: {e}")
        return web.Response(text="Error", status=500)

async def main():
    ws_handler = TwilioWebSocketHandler()
    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    app.router.add_get('/websocket', ws_handler.handle_websocket)
    app.router.add_post('/webhook', handle_event_streams_webhook)
    app.router.add_post('/events', handle_event_streams_webhook)
    app.router.add_get('/', lambda request: web.Response(text="Twilio WebSocket/HTTP Server Running"))
    for route in list(app.router.routes()):
        cors.add(route)
    host = "localhost"
    port = 8080
    logger.info(f"Starting Twilio WebSocket/HTTP server on {host}:{port}")
    logger.info(f"WebSocket endpoint: ws://{host}:{port}/websocket")
    logger.info(f"HTTP webhook endpoint: http://{host}:{port}/webhook")
    await web._run_app(app, host=host, port=port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
