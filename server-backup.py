import asyncio
import json
import logging
import aiohttp_cors
from typing import Dict, Any
from dataclasses import dataclass
from openai import OpenAI
import os
from dotenv import load_dotenv
try:
    from config.environment import get_env_manager, ServiceType
except ImportError:
    # Fallback for deployments without the config module
    get_env_manager = None
    ServiceType = None
from aiohttp import web, WSMsgType
from colorama import Fore, Style, init as colorama_init
import aiohttp_jinja2
import jinja2
import pathlib
from datetime import datetime, timezone
import re

def detect_language_switch(text: str, current_lang: str = "pt-BR") -> str:
    text = text.lower()
    language_patterns = {
        "pt-BR": [
            r"(speak|talk|switch).*(portuguese|português)",
            r"(falar|fala).*(português|portuguese)"
        ],
        "en-US": [
            r"(speak|talk|switch).*(english|inglês)",
            r"(falar|fala).*(inglês|english)"
        ],
        "es-US": [
            r"(speak|talk|switch).*(spanish|espanhol|español)",
            r"(hablar|habla|falar|fala).*(espanhol|español|spanish)"
        ]
    }
    for lang_code, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return lang_code
    return current_lang


# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

@dataclass
class ConversationConfig:
    sentence_end_patterns = ['.', '!', '?', '\n']
    partial_timeout = 1.5
    max_buffer_size = 1000
    openai_model = "gpt-4.1"

import asyncio

class LLMClient:
    def __init__(self, config: ConversationConfig):
        self.config = config
        # Initialize OpenAI client with minimal parameters to avoid compatibility issues
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Initialize with explicit minimal parameters only
        try:
            self.client = OpenAI(
                api_key=api_key
            )
        except Exception as e:
            # Log the specific error for debugging
            logger.error(f"{Fore.RED}[ERR] OpenAI client init error: {e}{Style.RESET_ALL}\n")
            raise e

    async def initialize(self):
        pass

    async def close(self):
        pass

    async def get_completion(self, text: str, language: str):
        messages = [
            {"role": "system", "content": f"You are a helpful assistant named Olli speaking in {language}. You are talking with Twilio customers through voice conversations (phone calls). Keep responses concise and conversational and avoid formatting and special characters like emojis."},
            {"role": "user", "content": text}
        ]

        def sync_stream():
            return self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                stream=True
            )

        try:
            stream = await asyncio.to_thread(sync_stream)
            for chunk in stream:
                content = chunk.choices[0].delta.content  # ✅ FIXED HERE
                if content:
                    yield content
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Streaming LLM error: {e}{Style.RESET_ALL}\n")
            yield "Desculpe, ocorreu um erro."


class TwilioWebSocketHandler:
    def __init__(self):
        self.config = ConversationConfig()
        self.llm_client = None  # Initialize later to avoid startup failures
        self.websocket = None
        self.conversation_sid = None
        self.latest_prompt_flags = {
            "interruptible": False,
            "preemptible": False,
            "last": True
        }
        self.dashboard_clients = set()
        self.language = 'pt-BR'  # default
        self._llm_initialized = False

    def _ensure_llm_client(self):
        """Initialize LLM client if not already done"""
        if not self._llm_initialized:
            try:
                # Only initialize if we have an API key
                if not os.getenv('OPENAI_API_KEY'):
                    logger.warning(f"{Fore.YELLOW}[WARN] No OpenAI API key, skipping LLM client initialization{Style.RESET_ALL}\n")
                    self.llm_client = None
                    self._llm_initialized = True  # Mark as "initialized" to avoid retries
                    return
                    
                self.llm_client = LLMClient(self.config)
                self._llm_initialized = True
                logger.info(f"{Fore.GREEN}[SYS] LLM client initialized successfully{Style.RESET_ALL}\n")
            except Exception as e:
                logger.warning(f"{Fore.YELLOW}[WARN] Failed to initialize LLM client: {e}{Style.RESET_ALL}\n")
                logger.warning(f"{Fore.YELLOW}[WARN] LLM features will be disabled{Style.RESET_ALL}\n")
                self.llm_client = None
                self._llm_initialized = True  # Mark as "initialized" to avoid retries

    async def broadcast_to_dashboard(self, payload: dict):
        msg = json.dumps(payload)
        for ws in self.dashboard_clients:
            try:
                await ws.send_str(msg)
            except Exception as e:
                logger.error(f"{Fore.RED}[ERR] Dashboard WS send failed: {e}{Style.RESET_ALL}\n")


    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.websocket = ws
        logger.info(f"{Fore.BLUE}[SYS] New WebSocket connection established{Style.RESET_ALL}\n")

        try:
            # Initialize LLM client on first connection
            self._ensure_llm_client()
            if self.llm_client:
                await self.llm_client.initialize()
                
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.route_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"{Fore.RED}[ERR] WebSocket error: {ws.exception()}{Style.RESET_ALL}\n")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] WebSocket error: {e}{Style.RESET_ALL}\n")
        finally:
            if self.llm_client:
                await self.llm_client.close()
            logger.info(f"{Fore.BLUE}[SYS] WebSocket connection closed{Style.RESET_ALL}\n")
        return ws

    async def route_message(self, message: str):
        try:
            data = json.loads(message)
            event_type = data.get("event") or data.get("type")
            if event_type is None:
                logger.warning(f"{Fore.YELLOW}[WARN] Missing 'event' field in message: {data}{Style.RESET_ALL}\n")
            else:
                logger.info(f"{Fore.MAGENTA}[SPI] Event received: {event_type}{Style.RESET_ALL}\n")
                await self.handle_conversation_relay_event(data)
        except json.JSONDecodeError as e:
            logger.error(f"{Fore.RED}[ERR] Invalid JSON received: {e}{Style.RESET_ALL}\n")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Error routing message: {e}{Style.RESET_ALL}\n")

    async def handle_conversation_relay_event(self, data: Dict[str, Any]):
        event_type = data.get("event") or data.get("type")
        if not event_type:
            logger.warning(f"{Fore.YELLOW}[WARN] No 'event' field found in: {data}{Style.RESET_ALL}\n")
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
            case "info" | "debug":
                await self.handle_info_debug(event_type, data)
            case _:
                logger.warning(f"{Fore.YELLOW}[WARN] Unhandled Conversation Relay event: {event_type}{Style.RESET_ALL}\n")

    async def handle_setup(self, data: Dict[str, Any]):
        self.conversation_sid = data.get("callSid")
        logger.info(f"{Fore.BLUE}[SYS] Conversation setup - SID: {self.conversation_sid}{Style.RESET_ALL}\n")
        self.language = 'pt-BR'
        await self.broadcast_to_dashboard({"type": "setup", "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})
        



    async def handle_prompt(self, data: Dict[str, Any]):
        text = data.get("voicePrompt", "")
        interruptible = data.get("interruptible", True)
        preemptible = data.get("preemptible", True)
        last = data.get("last", True)

        # Store the latest flags to use in the TTS response
        self.latest_prompt_flags = {
            "interruptible": interruptible,
            "preemptible": preemptible,
            "last": last
        }

        logger.info(f"{Fore.CYAN}[STT] {text}{Style.RESET_ALL}\n")
        if text.strip():
            await self.process_complete_input(text)

        await self.broadcast_to_dashboard({"type": 'prompt', "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})



    async def handle_interrupt(self, data: Dict[str, Any]):
        logger.info(f"{Fore.MAGENTA}[SPI] Interrupt received: {json.dumps(data, indent=2)}{Style.RESET_ALL}\n")
        await self.broadcast_to_dashboard({"type": "interrupt", "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})


    async def handle_dtmf(self, data: Dict[str, Any]):
        digit = data.get("digit")
        logger.info(f"{Fore.MAGENTA}[SPI] DTMF received: {digit}{Style.RESET_ALL}\n")
        if digit:
            await self.process_complete_input(f"User pressed {digit}")
        await self.broadcast_to_dashboard({"type": "dtmf", "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})

    async def handle_info_debug(self, event_type: str, data: Dict[str, Any]):
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        logger.info(f"{Fore.MAGENTA}[SPI] {event_type.capitalize()} event:\n{formatted}{Style.RESET_ALL}\n")
        await self.broadcast_to_dashboard({"type": event_type, "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})


    async def process_complete_input(self, text: str):
        SUPPORTED_LANGUAGES = ["pt-BR", "es-US", "en-US"]

        try:
            # Detect language switch
            new_lang = detect_language_switch(text, self.language)
            old_lang = self.language

            if new_lang != self.language:
                logger.info(f"{Fore.YELLOW}[LANG] Language switched: {self.language} → {new_lang}{Style.RESET_ALL}\n")
                self.language = new_lang

                # Send language switch message to Conversation Relay
                if self.websocket and new_lang in SUPPORTED_LANGUAGES:
                    language_message = {
                        "type": "language",
                        "ttsLanguage": new_lang,
                        "transcriptionLanguage": new_lang,
                    }
                    try:
                        await self.websocket.send_str(json.dumps(language_message))
                        logger.info(f"{Fore.YELLOW}[LANG] Sent language change to Conversation Relay: {language_message}{Style.RESET_ALL}\n")
                    except Exception as e:
                        logger.error(f"{Fore.RED}[ERR] Failed to send language switch: {e}{Style.RESET_ALL}\n")

                # Broadcast language switch
                await self.broadcast_to_dashboard({
                    "type": "language-switch",
                    "data": {"from": old_lang, "to": new_lang}
                })

            # 🔁 Streaming response from LLM (token by token)
            async for token in self.llm_client.get_completion(text, self.language):
                await self.send_response(token, partial=True)

            # ✅ Send final marker
            await self.send_response("", partial=False)

        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Error processing input: {e}{Style.RESET_ALL}\n")
            await self.send_response("Desculpe, não consegui processar sua solicitação.", partial=False)



    async def send_response(self, text: str, partial: bool = True):
        if not self.websocket: return
        msg = {
            "type": "text",
            "token": text,
            "last": not partial,
            "interruptible": self.latest_prompt_flags["interruptible"],
            "preemptible":  self.latest_prompt_flags["preemptible"]
        }
        try:
            await self.websocket.send_str(json.dumps(msg))
        except Exception as e:
            logger.error(f"[ERR] Send TTS failed: {e}")




async def handle_event_streams_webhook(request):
    try:
        body = await request.text()
        logger.info(f"{Fore.MAGENTA}[SPI] Event Streams webhook received: {body}{Style.RESET_ALL}\n")
        return web.Response(text="OK", status=200)
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Error handling Event Streams webhook: {e}{Style.RESET_ALL}\n")
        return web.Response(text="Error", status=500)

@aiohttp_jinja2.template('dashboard.html')
async def handle_dashboard(request):
    return {}

async def handle_dashboard_ws(request, ws_handler):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    ws_handler.dashboard_clients.add(ws)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.ERROR:
                logger.warning(f"[WARN] Dashboard WS closed with exception {ws.exception()}")
    finally:
        ws_handler.dashboard_clients.discard(ws)
    return ws

async def main():
    ws_handler = TwilioWebSocketHandler()
    app = web.Application()
    
    # Setup Jinja2 templates
    BASE_DIR = pathlib.Path(__file__).parent
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(BASE_DIR / "templates")))

    app.router.add_get('/dashboard', handle_dashboard)
    app.router.add_get('/dashboard-ws', lambda req: handle_dashboard_ws(req, ws_handler))

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
    app.router.add_get('/health', lambda request: web.json_response({
        "status": "healthy",
        "service": "conversation-relay",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv('DEPLOYMENT_ENVIRONMENT', 'local')
    }))


    for route in list(app.router.routes()):
        cors.add(route)
    
    # Environment-aware host and port configuration
    deployment_env = os.getenv('DEPLOYMENT_ENVIRONMENT', 'local')
    if deployment_env in ['render', 'heroku', 'aws', 'gcp']:
        host = "0.0.0.0"  # Bind to all interfaces for cloud deployment
        port = int(os.getenv('PORT', 8080))
    else:
        host = "localhost"
        port = int(os.getenv('PORT', 8080))
    
    logger.info(f"{Fore.BLUE}[SYS] Starting Twilio WebSocket/HTTP server on {host}:{port}{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] Environment: {deployment_env}{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] WebSocket endpoint: ws://{host}:{port}/websocket{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] HTTP webhook endpoint: http://{host}:{port}/webhook{Style.RESET_ALL}\n")
    # Use the proper aiohttp runner for production deployment
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"{Fore.GREEN}[SYS] Server started successfully and listening{Style.RESET_ALL}\n")
    
    # Keep the server running indefinitely
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info(f"{Fore.BLUE}[SYS] Server shutdown requested{Style.RESET_ALL}\n")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        # Test OpenAI client initialization before starting server
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info(f"{Fore.BLUE}[SYS] OpenAI API key found, testing client...{Style.RESET_ALL}\n")
            try:
                test_client = OpenAI(api_key=api_key)
                logger.info(f"{Fore.GREEN}[SYS] OpenAI client test successful{Style.RESET_ALL}\n")
            except Exception as openai_error:
                logger.warning(f"{Fore.YELLOW}[WARN] OpenAI client test failed: {openai_error}{Style.RESET_ALL}\n")
                logger.warning(f"{Fore.YELLOW}[WARN] Server will start anyway, LLM features will be disabled{Style.RESET_ALL}\n")
        else:
            logger.warning(f"{Fore.YELLOW}[WARN] No OpenAI API key found, LLM features will be disabled{Style.RESET_ALL}\n")
            
        # Start the server regardless of OpenAI status
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{Fore.BLUE}[SYS] Server stopped by user{Style.RESET_ALL}\n")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Server error: {e}{Style.RESET_ALL}\n")
