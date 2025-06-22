import asyncio
import json
import logging
import aiohttp_cors
from typing import Dict, Any
from dataclasses import dataclass
from openai import OpenAI
import os
from dotenv import load_dotenv
from aiohttp import web, WSMsgType
from colorama import Fore, Style, init as colorama_init
import aiohttp_jinja2
import jinja2
import pathlib
from datetime import datetime, timezone
import re

# Partial update: architecture support for agent routing, tool and knowledge injection will be handled in structured classes
# Goal: Integrate mocked tools, multiple agents, and knowledge routing

import csv
from pathlib import Path

from tools.personalization import get_personalization_context # Integração com o Twilio Segment para personalização das interações

# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

class Agent:
    def __init__(self, name, role, knowledge_paths=None, tools_paths=None, logger=None):
        self.name = name
        self.role = role
        self.knowledge_paths = knowledge_paths or []
        self.tools_paths = tools_paths or []
        self.knowledge = ""
        self.tools = []
        self.logger = logger or logging.getLogger(__name__)


    def load_knowledge(self):
        contents = []
        for path in self.knowledge_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    contents.append(f.read())
            except Exception as e:
                logger.warning(f"[WARN] Could not load knowledge from {path}: {e}")
        self.knowledge = "\n".join(contents)

    def load_tools(self):
        for path in self.tools_paths:
            if Path(path).exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        if path.endswith('.json'):
                            tool_data = json.load(f)
                            self.tools.append(tool_data)
                        else:
                            self.tools.append(Path(path).name)
                except Exception as e:
                    logger.warning(f"[WARN] Could not load tool file {path}: {e}")


class AgentRegistry:
    def __init__(self):
        self.agents = {}

    def register(self, agent: Agent):
        agent.load_knowledge()
        agent.load_tools()
        self.agents[agent.name] = agent

    def get_agent(self, name):
        return self.agents.get(name)

    def list_agents(self):
        return list(self.agents.keys())

    def get_routing_index(self):
        return self.agents.get("Olli").tools_paths[0]  # route-to-specialist CSV file


# Initialize agents
registry = AgentRegistry()

registry.register(Agent(
    name="Olli",
    role="generalist",
    knowledge_paths=["./knowledge/owlbank_olli_faqs.txt", "./knowledge/owlbank_specialist_agents.csv"],
    tools_paths=["./tools/route-to-specialist"],
    logger=logger
))

registry.register(Agent(
    name="Sunny",
    role="onboarding",
    knowledge_paths=["./knowledge/owlbank_onboarding.txt"],
    tools_paths=["./tools/route-to-generalist"],
    logger=logger
))

registry.register(Agent(
    name="Max",
    role="wealth",
    knowledge_paths=["./knowledge/high-value-customer.csv", "./knowledge/owlbank_wealth-management.txt"],
    tools_paths=["./tools/route-to-generalist"],
    logger=logger
))

registry.register(Agent(
    name="Io",
    role="investments",
    knowledge_paths=["./knowledge/owlbank_investment_products.txt", "./knowledge/owlbank_investors-and-assets.csv"],
    logger=logger
))

def build_agent_context(agent_name: str, customer_profile: dict = None):
    agent = registry.get_agent(agent_name)
    if not agent:
        raise ValueError(f"Agent '{agent_name}' not found in registry")

    # Build personalization section
    personalization = ""
    if customer_profile and "traits" in customer_profile:
        traits = customer_profile["traits"]
        items = []
        if "first_name" in traits:
            items.append(f"- Name: {traits['first_name']}")
        if "company" in traits:
            items.append(f"- Company: {traits['company']}")
        if "email" in traits:
            items.append(f"- Email: {traits['email']}")
        if "current_stage" in traits:
            items.append(f"- Stage: {traits['current_stage']}")
        if "event" in traits:
            items.append(f"- Context: {traits['event']}")
        if "flex_last-interaction-outcome" in traits:
            items.append(f"- Last Outcome: {traits['flex_last-interaction-outcome']}")
        if items:
            personalization = "\n\nCustomer info:\n" + "\n".join(items)

    # Specialist routing logic for Olli
    extra_instruction = ""
    if agent.name == "Olli":
        for tool in agent.tools:
            if isinstance(tool, dict) and "agents" in tool:
                routes = tool["agents"]
                formatted = "\n".join(
                    f"- If the customer mentions: {', '.join(a['triggers'])}, route to {a['agent']} (role: {a['role']})"
                    for a in routes
                )
                extra_instruction = f"\n\nIf any of the following topics arise, route accordingly:\n{formatted}"

    return (
        f"You are {agent.name}, a {agent.role} support agent at Owl Bank.\n"
        f"Use the following knowledge base:\n{agent.knowledge}"
        f"{personalization}"
        f"\nYou have access to the following tools and escalation rules: {extra_instruction}\n"
        f"If needed, append your message with #route_to:<AgentName>."
    )



def detect_language_switch(text: str, current_lang: str = "pt-BR") -> str:
    text = text.lower()
    language_patterns = {
        "pt-BR": [
            r"(speak|talk|switch|change).*(portuguese|português)",
            r"(falar|fala).*(português|portuguese)"
        ],
        "en-US": [
            r"(speak|talk|switch|change).*(english|inglês)",
            r"(falar|fala).*(inglês|english)"
        ],
        "es-US": [
            r"(speak|talk|switch|change).*(spanish|espanhol|español)",
            r"(hablar|habla|falar|fala|cambiar).*(espanhol|español|spanish)"
        ]
    }
    for lang_code, patterns in language_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return lang_code
    return current_lang


@dataclass
class ConversationConfig:
    sentence_end_patterns = ['.', '!', '?', '\n']
    partial_timeout = 1.5
    max_buffer_size = 1000
    openai_model = "gpt-4o-2024-11-20"  # Fixed model name

import asyncio

class LLMClient:
    def __init__(self, config: ConversationConfig):
        self.config = config
        self.client = OpenAI()

    async def initialize(self):
        pass

    async def close(self):
        pass

    async def get_completion(self, text: str, language: str, agent_name: str = "Olli", customer_profile: dict = None):
        context = build_agent_context(agent_name, customer_profile)
        messages = [
            {
                "role": "system",
                "content": (
                    f"{context}\n\n"
                    f"You are talking to a customer through a phone call. "
                    f"Speak in {language}. "
                    f"Respond conversationally. Avoid special characters or emojis.\n"
                    f"If a specialist agent is needed, end your message with #route_to:<AgentName> "
                    f"(e.g., #route_to:Sunny)."
                )
            },
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
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Streaming LLM error: {e}{Style.RESET_ALL}\n")
            yield "Desculpe, ocorreu um erro."


class TwilioWebSocketHandler:
    def __init__(self):
        self.config = ConversationConfig()
        self.llm_client = LLMClient(self.config)
        self.websocket = None
        self.conversation_sid = None
        self.latest_prompt_flags = {
            "interruptible": False,
            "preemptible": False,
            "last": True
        }
        self.dashboard_clients = set()
        self.language = 'pt-BR'  # default
        self.active_agent = "Olli"

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
            await self.llm_client.initialize()
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.route_message(msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"{Fore.RED}[ERR] WebSocket error: {ws.exception()}{Style.RESET_ALL}\n")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] WebSocket error: {e}{Style.RESET_ALL}\n")
        finally:
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

        # Buscar contexto de personalização do cliente no Twilio Segment
        self.personalization = get_personalization_context(data)
        logger.info(f"{Fore.CYAN}[CX] Customer context: {json.dumps(self.personalization, indent=2)}{Style.RESET_ALL}\n")

        await self.broadcast_to_dashboard({"type": "setup", "ts": datetime.now(timezone.utc).isoformat(), "data": data})

    async def handle_prompt(self, data: Dict[str, Any]):
        logger.info(f"{Fore.YELLOW}[AGENT] Current active agent: {self.active_agent}{Style.RESET_ALL}")
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

        await self.broadcast_to_dashboard({"type": 'prompt', "ts": datetime.now(timezone.utc).isoformat(), "data": data})

    async def handle_interrupt(self, data: Dict[str, Any]):
        logger.info(f"{Fore.MAGENTA}[SPI] Interrupt received: {json.dumps(data, indent=2)}{Style.RESET_ALL}\n")
        await self.broadcast_to_dashboard({"type": "interrupt", "ts": datetime.now(timezone.utc).isoformat(), "data": data})

    async def handle_dtmf(self, data: Dict[str, Any]):
        digit = data.get("digit")
        logger.info(f"{Fore.MAGENTA}[SPI] DTMF received: {digit}{Style.RESET_ALL}\n")
        if digit:
            await self.process_complete_input(f"User pressed {digit}")
        await self.broadcast_to_dashboard({"type": "dtmf", "ts": datetime.now(timezone.utc).isoformat(), "data": data})

    async def handle_info_debug(self, event_type: str, data: Dict[str, Any]):
        formatted = json.dumps(data, indent=2, ensure_ascii=False)
        logger.info(f"{Fore.MAGENTA}[SPI] {event_type.capitalize()} event:\n{formatted}{Style.RESET_ALL}\n")
        await self.broadcast_to_dashboard({"type": event_type, "ts": datetime.now(timezone.utc).isoformat(), "data": data})

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

            # Collect tokens from LLM
            response_buffer = []
            async for token in self.llm_client.get_completion(text, self.language, self.active_agent, self.personalization):
                response_buffer.append(token)
                await self.send_response(token, partial=True)

            full_response = ''.join(response_buffer).strip()

            # Check for #route_to:<Agent>
            match = re.search(r"#route_to:(\w+)", full_response)
            if match:
                requested_agent = match.group(1)
                if registry.get_agent(requested_agent):
                    logger.info(f"{Fore.YELLOW}[ROUTE] Routing to agent: {requested_agent}{Style.RESET_ALL}")

                    # Optional: store as active agent
                    self.active_agent = requested_agent

                    logger.info(f"{Fore.GREEN}[AGENT] Active agent updated: {self.active_agent}{Style.RESET_ALL}")
                    await self.broadcast_to_dashboard({
                        "type": "agent-switch",
                        "data": {"from": "Olli", "to": requested_agent}
})
                    return  # Skip sending final response, next prompt will use new agent
                else:
                    logger.warning(f"{Fore.YELLOW}[WARN] Unknown agent requested: {requested_agent}{Style.RESET_ALL}")

            # Send final marker
            await self.send_response("", partial=False)
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Error processing input: {e}{Style.RESET_ALL}\n")
            await self.send_response("Desculpe, não consegui processar sua solicitação.", partial=False)

    async def send_response(self, text: str, partial: bool = True):
        if not self.websocket: 
            return
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

    for route in list(app.router.routes()):
        cors.add(route)
    host = "localhost"
    port = 8080
    logger.info(f"{Fore.BLUE}[SYS] Starting Twilio WebSocket/HTTP server on {host}:{port}{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] WebSocket endpoint: ws://{host}:{port}/websocket{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] HTTP webhook endpoint: http://{host}:{port}/webhook{Style.RESET_ALL}\n")
    await web._run_app(app, host=host, port=port)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{Fore.BLUE}[SYS] Server stopped by user{Style.RESET_ALL}\n")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Server error: {e}{Style.RESET_ALL}\n")