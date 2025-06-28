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
from twilio.rest import Client
import decimal
from collections import defaultdict
import pandas as pd
import csv
from pathlib import Path
import math

from tools.personalization import get_personalization_context # Integração com o Twilio Segment para personalização das interações

# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Initialize Twilio client
twilio_client = Client()

# In-memory storage for intelligence events
intel_log = [] 

DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)
NDJSON_FILE = DATA_PATH / "intel_results.ndjson"
if not NDJSON_FILE.exists():
    NDJSON_FILE.touch()

RAW_NDJSON_FILE = DATA_PATH / "intel_raw_results.ndjson"
RAW_NDJSON_FILE.touch(exist_ok=True)

DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

def log_debug(message):
    if DEBUG_MODE:
        logger.debug(message)

def extract_score(text, key):
    match = re.search(rf"{key} Score:\s*(\d+)", text)
    return int(match.group(1)) if match else None

def persist_result(payload: dict):
    flat_result = flatten_intel_result(payload)
    intel_log.append(flat_result)

    save_to_ndjson(flat_result, target=NDJSON_FILE)  # flat
    save_to_ndjson(payload, target=RAW_NDJSON_FILE)  # raw

    log_debug(f"[PERSIST] Saved flat + raw intelligence for {payload['data']['transcript']['sid']}")




def flatten_intel_result(payload: dict) -> dict:
    out = {
        "ts": payload.get("ts"),
        "transcript_sid": payload["data"]["transcript"]["sid"],
        "language": payload["data"]["transcript"].get("language"),
        "duration": payload["data"]["transcript"].get("duration"),
        "status": payload["data"]["transcript"].get("status"),
    }

    for op in payload["data"].get("operators", []):
        name = op.get("name", "").lower()
        if "csat" in name:
            score = extract_score(op.get("text_result", "") or "", "CSAT")
            if score is not None:
                out["csat_score"] = score
        if "ces" in name:
            score = extract_score(op.get("text_result", "") or "", "CES")
            if score is not None:
                out["ces_score"] = score
        if "hallucination" in name:
            out["hallucination_occurrences"] = 1
        if "legal" in name:
            out["legal_risk_score"] = int(op.get("predicted_probability", 0) * 100)
        if "sentiment" in name and "label_probabilities" in op:
            probs = op["label_probabilities"]
            out["positive_sentiment_score"] = int(probs.get("positive", 0) * 100)
            out["neutral_sentiment_score"] = int(probs.get("neutral", 0) * 100)
            out["negative_sentiment_score"] = int(probs.get("negative", 0) * 100)

    return out

def save_to_ndjson(result: dict, target: Path):
    with open(target, "a", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, default=safe_json)
        f.write("\n")

def load_aggregated_intel_results(group_by: str = "day") -> dict:
    if not NDJSON_FILE.exists():
        return {}

    try:
        df = pd.read_json(NDJSON_FILE, lines=True)
    except Exception as e:
        log_debug(f"[WARN] Failed to read CSV for aggregation: {e}")
        return {}

    # Robust datetime parsing
    df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
    df = df.dropna(subset=["ts"])

    if df.empty:
        return {}

    if group_by == "week":
        df["group"] = df["ts"].dt.strftime("%Y-W%U")
    elif group_by == "month":
        df["group"] = df["ts"].dt.strftime("%Y-%m")
    elif group_by == "year":
        df["group"] = df["ts"].dt.year.astype(str)
    else:
        df["group"] = df["ts"].dt.strftime("%Y-%m-%d")

    results = {}
    grouped = df.groupby("group")

    for label, group in grouped:
        def safe_avg(col):
            if col in group.columns:
                values = group[col].dropna().astype(float)
                return round(values.mean(), 2) if not values.empty else None
            return None


        def safe_sum(col):
            return int(group[col].fillna(0).astype(float).sum()) if col in group.columns else 0

        sentiment_cols = [
            "positive_sentiment_score",
            "neutral_sentiment_score",
            "negative_sentiment_score"
        ]

        # Count number of rows where each sentiment score exceeds 50%
        def count_sentiment(col):
            return int((group[col].dropna().astype(float) > 50).sum()) if col in group.columns else 0

        results[label] = {
            "avgCSAT": safe_avg("csat_score"),
            "avgCES": safe_avg("ces_score"),
            "count": len(group),
            "hallucination_count": int(group["hallucination_occurrences"].fillna(0).sum()) if "hallucination_occurrences" in group else 0,
            "legal_risk_score": int(group["legal_risk_score"].fillna(0).sum()) if "legal_risk_score" in group else 0,
            "positive_sentiment": count_sentiment("positive_sentiment_score"),
            "neutral_sentiment": count_sentiment("neutral_sentiment_score"),
            "negative_sentiment": count_sentiment("negative_sentiment_score"),
        }


    return results

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
# Silence noisy loggers if not in debug mode
if not DEBUG_MODE:
    logging.getLogger("twilio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def load_recent_events(limit=100):
    if not NDJSON_FILE.exists():
        return []
    try:
        df = pd.read_json(NDJSON_FILE, on_bad_lines="skip")
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce", utc=True)
        df = df.dropna(subset=["ts"])
        df = df.fillna(value="")  # or .fillna(0) for numeric fields

        records = df.tail(limit).to_dict(orient='records')

        # Ensure all values are JSON-safe
        def sanitize(record):
            return {
                k: (None if pd.isna(v) or v == "" else v)
                for k, v in record.items()
            }

        return [sanitize(r) for r in records]
    except Exception as e:
        log_debug(f"[WARN] Failed to load recent events: {e}")
        return []
    if not NDJSON_FILE.exists():
        return []
    df = pd.read_json(NDJSON_FILE, lines=True)
    return df.tail(limit).to_dict(orient='records')

if NDJSON_FILE.exists():
    try:
        df = pd.read_json(NDJSON_FILE, lines=True)
        for _, row in df.iterrows():
            intel_log.append(row.to_dict())
    except Exception as e:
        log_debug(f"[WARN] Failed to preload past results: {e}")

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
                log_debug(f"[WARN] Could not load knowledge from {path}: {e}")
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
                    log_debug(f"[WARN] Could not load tool file {path}: {e}")

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
                    f"Speak in {language}. But respect user's request if they ask to switch language.\n"
                    f"Respond conversationally. Avoid special characters or emojis. Optimize responses for speech to text.\n"
                    f"If a specialist agent is needed, end your message with #route_to:<AgentName> "
                    f"If a specialist agent is named or requested (Sunny, Max, Io or Olli), end your message with #route_to:<AgentName> "
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

    async def get_completion_from_history(self, history: list, language: str, agent_name: str = "Olli", customer_profile: dict = None):
        context = build_agent_context(agent_name, customer_profile)
        messages = [
            {"role": "system", "content": (
                f"{context}\n\n"
                f"You are talking to a customer through a phone call. "
                f"Speak in {language}, but you can switch languages if needed to English and Latin American Spanish."
                f"Respond conversationally. Avoid special characters or emojis. Optimize responses for speech to text.\n"
                f"If a specialist agent is needed, end your message with #route_to:<AgentName> "
                f"(e.g., #route_to:Sunny)."
            )}
        ] + history

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
        self.active_agent = "Olli"  # Default agent, will be updated in setup based on channel
        self.chat_history = []  # Stores full chat context


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

        # Check if this is a WhatsApp call and route accordingly
        from_number = data.get("from", "")
        if from_number.startswith("whatsapp:"):
            self.active_agent = "Max"
            logger.info(f"{Fore.GREEN}[ROUTE] WhatsApp call detected from {from_number} - routing to Max (wealth management){Style.RESET_ALL}\n")
            await self.broadcast_to_dashboard({
                "type": "auto-route",
                "data": {
                    "channel": "whatsapp",
                    "from": from_number,
                    "routed_to": "Max",
                    "reason": "WhatsApp channel routing"
                }
            })
        else:
            self.active_agent = "Olli"
            logger.info(f"{Fore.CYAN}[ROUTE] PSTN/SIP call detected from {from_number} - routing to Olli (generalist){Style.RESET_ALL}\n")

        logger.info(f"{Fore.YELLOW}[AGENT] Active agent set to: {self.active_agent}{Style.RESET_ALL}\n")

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

            # Append user message to chat history
            self.chat_history.append({"role": "user", "content": text})

            # Get streaming response from LLM using full history
            response_buffer = []
            async for token in self.llm_client.get_completion_from_history(
                history=self.chat_history,
                language=self.language,
                agent_name=self.active_agent,
                customer_profile=self.personalization
            ):
                response_buffer.append(token)
                await self.send_response(token, partial=True)

            # Append assistant response to history
            self.chat_history.append({"role": "assistant", "content": ''.join(response_buffer).strip()})


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

def safe_json(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def sanitize_json(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    elif isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(i) for i in obj]
    return obj


async def handle_intelligence_result(transcript_sid: str, ws_handler: TwilioWebSocketHandler):
    try:
        transcript = twilio_client.intelligence.v2.transcripts(transcript_sid).fetch()
        operator_results = twilio_client.intelligence.v2.transcripts(transcript_sid).operator_results.list()

        payload = {
            "type": "intelligence",
            "ts": transcript.date_created.isoformat(),
            "data": {
                "transcript": {
                    "sid": transcript.sid,
                    "status": transcript.status,
                    "language": transcript.language_code,
                    "duration": transcript.duration,
                    "url": transcript.url,
                    "links": transcript.links
                },
                "operators": []
            }
        }

        for op in operator_results:
            result_data = {
                "name": op.name,
                "type": op.operator_type,
                "url": op.url,
                "transcript_sid": op.transcript_sid,
            }

            # Parse results by operator type
            if op.operator_type == "text-generation" and op.text_generation_results:
                result_data["text_result"] = op.text_generation_results.get("result")

            elif op.operator_type == "conversation-classify":
                result_data["predicted_label"] = op.predicted_label
                result_data["predicted_probability"] = op.predicted_probability
                result_data["label_probabilities"] = op.label_probabilities

            elif op.operator_type == "extract":
                result_data["extract_results"] = op.extract_results
                result_data["match_probability"] = op.match_probability
                result_data["extract_match"] = op.extract_match
                result_data["utterance_results"] = op.utterance_results

            # Add other types as needed here...

            payload["data"]["operators"].append(result_data)

        await ws_handler.broadcast_to_dashboard(json.loads(json.dumps(payload, default=safe_json)))
        persist_result(payload)

        logger.info(f"{Fore.GREEN}[INTEL] Broadcasted intelligence for {transcript_sid}{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Failed to handle intelligence for {transcript_sid}: {e}{Style.RESET_ALL}")

async def handle_event_streams_webhook(request, ws_handler: TwilioWebSocketHandler):
    try:
        body = await request.text()
        logger.info(f"{Fore.MAGENTA}[SPI] Event Streams webhook received: {body}{Style.RESET_ALL}")

        data = json.loads(body)
        transcript_sid = data.get("transcript_sid") or data.get("TranscriptSid")

        if transcript_sid:
            await handle_intelligence_result(transcript_sid, ws_handler)
        else:
            log_debug(f"{Fore.YELLOW}[WARN] No transcript_sid found in webhook payload{Style.RESET_ALL}")

        return web.Response(text="OK", status=200)
    except Exception as e:
        log_debug(f"{Fore.RED}[ERR] Error handling Event Streams webhook: {e}{Style.RESET_ALL}")
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
                log_debug(f"[WARN] Dashboard WS closed with exception {ws.exception()}")
    finally:
        ws_handler.dashboard_clients.discard(ws)
    return ws

from datetime import datetime, timedelta

async def preload_transcripts_for_service(service_sid: str, ws_handler: TwilioWebSocketHandler):
    try:
        # Load already-processed transcript SIDs
        existing_sids = set()
        if NDJSON_FILE.exists():
            try:
                df = pd.read_json(NDJSON_FILE, lines=True)
                if "transcript_sid" in df.columns:
                    existing_sids = set(df["transcript_sid"].dropna().astype(str))
            except Exception as e:
                log_debug(f"[WARN] Failed to read existing results: {e}")

        # Look back sufficiently far if needed
        start_time = datetime.now(timezone.utc) - timedelta(days=30)
        cursor = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')

        log_debug(f"{Fore.BLUE}[INIT] Fetching transcripts created after {cursor}{Style.RESET_ALL}")

        transcripts = twilio_client.intelligence.v2.transcripts.list(
            limit=100,
            after_date_created=cursor,
            after_start_time=cursor
        )

        fetched = 0
        for t in transcripts:
            if t.service_sid != service_sid:
                continue

            if t.sid in existing_sids:
                log_debug(f"[SKIP] Already processed: {t.sid}")
                continue

            log_debug(f"[PRELOAD] Processing: {t.sid}")
            await handle_intelligence_result(t.sid, ws_handler)
            fetched += 1

        logger.info(f"{Fore.BLUE}[INIT] Finished loading {fetched} transcripts for service {service_sid}{Style.RESET_ALL}")

    except Exception as e:
        log_debug(f"{Fore.RED}[ERR] Failed to preload transcripts: {e}{Style.RESET_ALL}")


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
    app.router.add_post('/webhook', lambda request: handle_event_streams_webhook(request, ws_handler))
    app.router.add_post('/events', lambda request: handle_event_streams_webhook(request, ws_handler))
    app.router.add_get('/', lambda request: web.Response(text="Twilio WebSocket/HTTP Server Running"))
    app.router.add_get('/intel-aggregates', lambda req: web.json_response(
        sanitize_json(load_aggregated_intel_results(req.rel_url.query.get("group", "day")))
    ))
    app.router.add_get('/intel-events', lambda req: web.json_response(load_recent_events()))



    for route in list(app.router.routes()):
        cors.add(route)
    host = "localhost"
    port = 8080
    logger.info(f"{Fore.BLUE}[SYS] Starting Twilio WebSocket/HTTP server on {host}:{port}{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] WebSocket endpoint: ws://{host}:{port}/websocket{Style.RESET_ALL}\n")
    logger.info(f"{Fore.BLUE}[SYS] HTTP webhook endpoint: http://{host}:{port}/webhook{Style.RESET_ALL}\n")
    await preload_transcripts_for_service("GAde9c513fd3914897cac25df18f3203b7", ws_handler)
    runner = web.AppRunner(app, access_log=None if not DEBUG_MODE else logger)
    await runner.setup()
    site = web.TCPSite(runner, host=host, port=port)
    await site.start()

    # Optional: keep the same printed messages
    logger.info(f"{Fore.BLUE}[SYS] Server running at http://{host}:{port}{Style.RESET_ALL}")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info(f"{Fore.BLUE}[SYS] Server stopped by user{Style.RESET_ALL}\n")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Server error: {e}{Style.RESET_ALL}\n")
