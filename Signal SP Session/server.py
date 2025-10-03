import asyncio
import json
import logging
import sys
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
# Import pyngrok conditionally for local development
try:
    from pyngrok import ngrok
    NGROK_AVAILABLE = True
except ImportError:
    NGROK_AVAILABLE = False
    logger.info(f"{Fore.YELLOW}[SYS] pyngrok not available - ngrok features disabled{Style.RESET_ALL}")

from tools.personalization import get_personalization_context # Integração com o Twilio Segment para personalização das interações

# Initialize colorama
colorama_init(autoreset=True)

# Load environment variables from .env file
load_dotenv()

# Get DEBUG_MODE early since it's used in multiple places
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Test debug logging early
if DEBUG_MODE:
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")
    print(f"{timestamp} [DEBUG] Debug mode is ENABLED - detailed logging active")

# OpenAI Functions feature disabled to simplify deployment

# Initialize Twilio client
from twilio.http.http_client import TwilioHttpClient

# Disable Twilio SDK HTTP logging
if not DEBUG_MODE:
    # Monkey patch print function globally to suppress Twilio HTTP logs
    original_print = print
    
    def filtered_print(*args, **kwargs):
        # Suppress Twilio HTTP debug prints
        if args and isinstance(args[0], str):
            content = str(args[0])
            # Check for Twilio HTTP log patterns
            twilio_patterns = [
                "-- BEGIN Twilio API Request --",
                "-- END Twilio API Request --", 
                "Response Status Code:",
                "Response Headers:",
                "Query Params:",
                "Headers:"
            ]
            if any(pattern in content for pattern in twilio_patterns):
                return  # Suppress this print
        # Allow all other prints
        return original_print(*args, **kwargs)
    
    # Replace print globally
    import builtins
    builtins.print = filtered_print

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

def log_debug(message):
    if DEBUG_MODE:
        # Use direct print with timestamp since logger might not be initialized yet
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")
        print(f"{timestamp} [DEBUG] {message}")

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

# Early startup debugging and library version checks
logger.info(f"{Fore.CYAN}[DEBUG] Starting server startup debugging{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] Python executable: {sys.executable}{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] Current working directory: {os.getcwd()}{Style.RESET_ALL}")

# Log critical environment variables
logger.info(f"{Fore.CYAN}[DEBUG] DEPLOYMENT_ENVIRONMENT: {os.getenv('DEPLOYMENT_ENVIRONMENT', 'not_set')}{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not_set'}{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'not_set')}{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] OpenAI Functions: Disabled{Style.RESET_ALL}")
logger.info(f"{Fore.CYAN}[DEBUG] DEBUG_MODE: {DEBUG_MODE}{Style.RESET_ALL}")

# Check OpenAI library version and compatibility
try:
    import openai
    logger.info(f"{Fore.GREEN}[DEBUG] OpenAI library version: {openai.__version__}{Style.RESET_ALL}")
    
    # Test basic OpenAI client instantiation
    from openai import OpenAI
    logger.info(f"{Fore.CYAN}[DEBUG] OpenAI import successful, testing client creation{Style.RESET_ALL}")
    
    # Test without any arguments first
    test_client = OpenAI()
    logger.info(f"{Fore.GREEN}[DEBUG] Basic OpenAI() client creation successful{Style.RESET_ALL}")
    del test_client
    
except ImportError as e:
    logger.error(f"{Fore.RED}[ERR] OpenAI library not available: {e}{Style.RESET_ALL}")
except Exception as e:
    logger.error(f"{Fore.RED}[ERR] OpenAI client creation failed during startup test: {e}{Style.RESET_ALL}")
    import traceback
    logger.error(f"{Fore.RED}[ERR] OpenAI startup test traceback:\n{traceback.format_exc()}{Style.RESET_ALL}")

# Silence noisy loggers if not in debug mode
if not DEBUG_MODE:
    # Silence Twilio SDK HTTP logging
    logging.getLogger("twilio.http_client").setLevel(logging.WARNING)
    logging.getLogger("twilio").setLevel(logging.WARNING)
    
    # Silence aiohttp access logs
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.server").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.web").setLevel(logging.WARNING)
    
    # Silence urllib3 connection logs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    
    # Silence requests library logs
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("requests.packages.urllib3").setLevel(logging.WARNING)
else:
    # In debug mode, show these logs but at a controlled level
    logging.getLogger("twilio.http_client").setLevel(logging.DEBUG)
    logging.getLogger("aiohttp.access").setLevel(logging.INFO)

# Import simple banking tools and conversations logger
try:
    logger.info(f"{Fore.CYAN}[DEBUG] About to import banking tools{Style.RESET_ALL}")
    from tools.banking_tools import get_banking_tools
    logger.info(f"{Fore.CYAN}[DEBUG] Banking tools imported successfully{Style.RESET_ALL}")
    
    logger.info(f"{Fore.CYAN}[DEBUG] About to import conversations logger{Style.RESET_ALL}")
    from tools.conversations_logger import get_conversations_logger
    logger.info(f"{Fore.CYAN}[DEBUG] Conversations logger imported successfully{Style.RESET_ALL}")
    
    logger.info(f"{Fore.GREEN}[SYS] Banking tools and conversations logger loaded{Style.RESET_ALL}")
except ImportError as e:
    logger.error(f"{Fore.RED}[ERR] Failed to load banking tools: {e}{Style.RESET_ALL}")
    import traceback
    logger.error(f"{Fore.RED}[ERR] Import traceback:\n{traceback.format_exc()}{Style.RESET_ALL}")
    # Create dummy functions to prevent crashes
    def get_banking_tools():
        return None
    def get_conversations_logger():
        return None


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

async def get_conversation_intelligence(request):
    """Get intelligence data for a specific conversation"""
    try:
        conversation_sid = request.match_info['conversation_sid']
        intelligence_service_sid = os.getenv("TWILIO_INTELLIGENCE_SERVICE_SID", "GA283e1ef3f15a071f01a91a96a4c16621")
        
        log_debug(f"[INTEL] Looking for intelligence data for conversation: {conversation_sid}")
        
        # First, get the conversation details to extract the call SID
        call_sid = None
        try:
            # Get conversation from Twilio Conversations API to extract call_sid from attributes
            conversation = twilio_client.conversations.v1.conversations(conversation_sid).fetch()
            if conversation.attributes:
                attributes = json.loads(conversation.attributes)
                call_sid = attributes.get('call_sid')
                log_debug(f"[INTEL] Found call_sid in conversation attributes: {call_sid}")
        except Exception as e:
            log_debug(f"[WARN] Failed to fetch conversation details: {e}")
        
        # Search for transcripts related to this call
        conversation_transcript = None
        transcript_sentences = []
        operator_results = []
        
        try:
            transcripts = twilio_client.intelligence.v2.transcripts.list(
                limit=50  # Increased limit to find more potential matches
            )
            
            log_debug(f"[INTEL] Found {len(transcripts)} transcripts in Intelligence service")
            
            # For voice conversations, match by call SID
            if call_sid:
                log_debug(f"[INTEL] Voice conversation detected, matching by call SID: {call_sid}")
                
                for transcript in transcripts:
                    log_debug(f"[INTEL] Examining transcript {transcript.sid} for call SID {call_sid}")
                    
                    match_found = False
                    
                    # Strategy 1: String search for call SID in transcript (most reliable)
                    transcript_str = str(transcript.__dict__)
                    if call_sid in transcript_str:
                        match_found = True
                        log_debug(f"[INTEL] ✓ Matched transcript by call SID string search: {call_sid} -> {transcript.sid}")
                    
                    if match_found:
                        conversation_transcript = transcript
                        break
            else:
                # For messaging conversations, match by conversation SID
                log_debug(f"[INTEL] Messaging conversation detected, matching by conversation SID: {conversation_sid}")
                
                for transcript in transcripts:
                    if conversation_sid in str(transcript.__dict__):
                        conversation_transcript = transcript
                        log_debug(f"[INTEL] Matched transcript by conversation SID: {conversation_sid}")
                        break
            
            # If still no match, try to use local NDJSON data or recent transcript as fallback
            if not conversation_transcript:
                log_debug(f"[INTEL] No direct match found, trying fallback strategies...")
                
                # Strategy 1: Use local NDJSON data if available
                if NDJSON_FILE.exists():
                    try:
                        # Read the most recent intelligence results
                        df = pd.read_json(NDJSON_FILE, lines=True)
                        if not df.empty and "transcript_sid" in df.columns:
                            # Get the most recent transcript SID
                            recent_transcript_sid = df["transcript_sid"].dropna().iloc[-1] if not df["transcript_sid"].dropna().empty else None
                            
                            if recent_transcript_sid:
                                log_debug(f"[INTEL] Found recent transcript in local data: {recent_transcript_sid}")
                                # Try to fetch this transcript from Intelligence API
                                try:
                                    conversation_transcript = twilio_client.intelligence.v2.services(intelligence_service_sid).transcripts(recent_transcript_sid).fetch()
                                    log_debug(f"[INTEL] Successfully fetched transcript from local data: {recent_transcript_sid}")
                                except Exception as e:
                                    log_debug(f"[WARN] Failed to fetch transcript from local data: {e}")
                    except Exception as e:
                        log_debug(f"[WARN] Failed to read local NDJSON file: {e}")
                
                # Strategy 2: If still no match, use the most recent transcript as final fallback
                if not conversation_transcript and transcripts:
                    log_debug(f"[INTEL] Using most recent available transcript as final fallback")
                    conversation_transcript = transcripts[0]
            
        except Exception as e:
            log_debug(f"[WARN] Failed to search Intelligence API: {e}")
        
        if conversation_transcript:
            log_debug(f"[INTEL] Found transcript: {conversation_transcript.sid}")
            
            # Get transcript sentences
            try:
                log_debug(f"[INTEL] Fetching sentences for transcript: {conversation_transcript.sid}")
                sentences = twilio_client.intelligence.v2.transcripts(conversation_transcript.sid).sentences.list(limit=1000)
                
                log_debug(f"[INTEL] Raw sentences API response: {len(sentences)} sentences found")
                
                transcript_sentences = []
                for sentence in sentences:
                    # Debug: Check what attributes are actually available
                    sentence_attrs = [attr for attr in dir(sentence) if not attr.startswith('_')]
                    log_debug(f"[INTEL] Sentence attributes: {sentence_attrs[:10]}...")  # Show first 10 attrs
                    
                    # Map media channel to speaker label
                    media_channel = getattr(sentence, 'media_channel', None)
                    speaker_label = 'unknown'
                    if media_channel == 1:
                        speaker_label = 'customer'
                    elif media_channel == 2:
                        speaker_label = 'agent'
                    
                    sentence_data = {
                        "sid": getattr(sentence, 'sid', None),
                        "text": getattr(sentence, 'transcript', 'No text available'),  # Based on CLI output
                        "confidence": getattr(sentence, 'confidence', None),
                        "start_time": getattr(sentence, 'start_time', None),
                        "end_time": getattr(sentence, 'end_time', None),
                        "speaker": speaker_label,
                        "media_channel": media_channel,  # Keep original for debugging
                        "date_created": getattr(sentence, 'date_created', None)
                    }
                    if sentence_data["date_created"]:
                        try:
                            sentence_data["date_created"] = sentence_data["date_created"].isoformat()
                        except:
                            sentence_data["date_created"] = str(sentence_data["date_created"])
                    
                    transcript_sentences.append(sentence_data)
                    log_debug(f"[INTEL] Processed sentence: {sentence_data['text'][:50] if sentence_data['text'] else 'No text'}...")
                
                log_debug(f"[INTEL] ✅ Successfully processed {len(transcript_sentences)} transcript sentences")
                    
            except Exception as e:
                log_debug(f"[ERR] ❌ Failed to fetch transcript sentences: {type(e).__name__}: {e}")
                logger.error(f"[ERR] Sentences API error: {type(e).__name__}: {e}")
            
            # Get operator results
            try:
                log_debug(f"[INTEL] Fetching operator results for transcript: {conversation_transcript.sid}")
                ops = twilio_client.intelligence.v2.transcripts(conversation_transcript.sid).operator_results.list()
                
                log_debug(f"[INTEL] Raw operator results API response: {len(ops)} results found")
                
                for i, op in enumerate(ops):
                    # Debug: Check what attributes are actually available
                    op_attrs = [attr for attr in dir(op) if not attr.startswith('_')]
                    log_debug(f"[INTEL] Processing operator result {i+1}/{len(ops)}")
                    log_debug(f"[INTEL] Operator attributes: {op_attrs[:15]}...")  # Show first 15 attrs
                    
                    result_data = {
                        "sid": getattr(op, 'operator_sid', None),  # From CLI: operatorSid
                        "name": getattr(op, 'name', 'Unknown'),
                        "operator_type": getattr(op, 'operator_type', 'unknown'),
                        "url": getattr(op, 'url', None),
                        "transcript_sid": getattr(op, 'transcript_sid', None),
                        "date_created": getattr(op, 'date_created', None),
                        # Add CLI-based attributes
                        "extract_results": getattr(op, 'extract_results', {}),
                        "text_generation_results": getattr(op, 'text_generation_results', None),
                        "predicted_label": getattr(op, 'predicted_label', None),
                        "predicted_probability": getattr(op, 'predicted_probability', None),
                        "label_probabilities": getattr(op, 'label_probabilities', {})
                    }
                    
                    if result_data["date_created"]:
                        try:
                            result_data["date_created"] = result_data["date_created"].isoformat()
                        except:
                            result_data["date_created"] = str(result_data["date_created"])
                    
                    log_debug(f"[INTEL] Processing {result_data['name']} ({result_data['operator_type']})")
                    
                    # Parse results by operator type
                    if op.operator_type == "text-generation":
                        # For CSAT, CES, Agent Effectiveness, etc.
                        if hasattr(op, 'text_generation_results') and op.text_generation_results:
                            result_data["text_result"] = getattr(op.text_generation_results, 'result', None)
                            log_debug(f"[INTEL] Text generation result: {result_data['text_result'][:100] if result_data['text_result'] else 'None'}...")
                        else:
                            # Fallback to check for direct text result
                            result_data["text_result"] = getattr(op, 'text_result', None)
                    
                    elif op.operator_type == "conversation-classify":
                        # For sentiment analysis
                        result_data["predicted_label"] = getattr(op, 'predicted_label', None)
                        result_data["predicted_probability"] = getattr(op, 'predicted_probability', None)
                        result_data["label_probabilities"] = getattr(op, 'label_probabilities', {})
                        log_debug(f"[INTEL] Sentiment analysis: {result_data['predicted_label']} ({result_data['predicted_probability']})")
                    
                    elif op.operator_type == "extract":
                        # For entity extraction
                        result_data["extract_results"] = getattr(op, 'extract_results', {})
                        result_data["match_probability"] = getattr(op, 'match_probability', None)
                        result_data["extract_match"] = getattr(op, 'extract_match', None)
                        result_data["utterance_results"] = getattr(op, 'utterance_results', [])
                        log_debug(f"[INTEL] Entity extraction: {len(result_data['utterance_results'])} utterances")
                    
                    operator_results.append(result_data)
                    log_debug(f"[INTEL] ✅ Added operator result: {op.name}")
                
                log_debug(f"[INTEL] ✅ Successfully processed {len(operator_results)} operator results")
                
            except Exception as e:
                log_debug(f"[ERR] ❌ Failed to fetch operator results: {type(e).__name__}: {e}")
                logger.error(f"[ERR] Operator results API error: {type(e).__name__}: {e}")
        
        response_data = {
            "conversation_sid": conversation_sid,
            "call_sid": call_sid,
            "transcript": {
                "sid": conversation_transcript.sid if conversation_transcript else None,
                "status": getattr(conversation_transcript, 'status', None) if conversation_transcript else None,
                "language": getattr(conversation_transcript, 'language_code', None) if conversation_transcript else None,
                "duration": getattr(conversation_transcript, 'duration', None) if conversation_transcript else None,
                "sentences": transcript_sentences
            } if conversation_transcript else None,
            "operator_results": operator_results,
            "intelligence_service_sid": intelligence_service_sid
        }
        
        log_debug(f"[INTEL] Returning intelligence data for {conversation_sid}: transcript={bool(conversation_transcript)}, sentences={len(transcript_sentences)}, operators={len(operator_results)}")
        
        return web.json_response(sanitize_json(response_data))
        
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Failed to get conversation intelligence: {e}{Style.RESET_ALL}")
        return web.json_response(
            {"error": "Failed to fetch intelligence data", "message": str(e)}, 
            status=500
        )

async def test_transcripts(request):
    """Test function to debug transcript access"""
    try:
        intelligence_service_sid = os.getenv("TWILIO_INTELLIGENCE_SERVICE_SID", "GA283e1ef3f15a071f01a91a96a4c16621")
        
        # Test: List transcripts using correct Intelligence API access
        transcripts = twilio_client.intelligence.v2.transcripts.list(limit=10)
        
        result = {
            "service_sid": intelligence_service_sid,
            "transcript_count": len(transcripts),
            "transcripts": []
        }
        
        for transcript in transcripts:
            transcript_info = {
                "sid": transcript.sid,
                "status": transcript.status,
                "duration": getattr(transcript, 'duration', None),
                "language": getattr(transcript, 'language_code', None),
                "has_channel": hasattr(transcript, 'channel'),
                "raw_data": str(transcript.__dict__)[:500] + "..." if len(str(transcript.__dict__)) > 500 else str(transcript.__dict__)
            }
            
            # Check if our target call SID is in this transcript
            call_sid = "CAb0ac09fa0f4949d4888795448aa80ea8"
            if call_sid in str(transcript.__dict__):
                transcript_info["matches_call_sid"] = True
                transcript_info["match_details"] = f"Found {call_sid} in transcript data"
            else:
                transcript_info["matches_call_sid"] = False
            
            result["transcripts"].append(transcript_info)
        
        return web.json_response(sanitize_json(result))
        
    except Exception as e:
        logger.error(f"Test transcripts error: {e}")
        return web.json_response({"error": str(e)}, status=500)

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
    tools_paths=["./tools/route-to-specialist.json"],
    logger=logger
))

registry.register(Agent(
    name="Sunny",
    role="onboarding",
    knowledge_paths=["./knowledge/owlbank_onboarding.txt"],
    tools_paths=["./tools/route-to-generalist.json"],
    logger=logger
))

registry.register(Agent(
    name="Max",
    role="wealth",
    knowledge_paths=["./knowledge/high-value-customer.csv", "./knowledge/owlbank_wealth-management.txt"],
    tools_paths=["./tools/route-to-generalist.json"],
    logger=logger
))

registry.register(Agent(
    name="Io",
    role="investments",
    knowledge_paths=["./knowledge/owlbank_investment_products.txt", "./knowledge/owlbank_investors-and-assets.csv"],
    tools_paths=["./tools/route-to-generalist.json"],
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

    # Build agent-specific personality
    personality_map = {
        "Olli": "You are Olli, the friendly generalist at Owl Bank. You help with general questions and route customers to specialists when needed.",
        "Sunny": "You are Sunny, the welcoming onboarding specialist at Owl Bank. You help new customers get started and explain our services.",
        "Max": "You are Max, the wealth management specialist at Owl Bank. You serve high-net-worth clients with sophisticated financial needs.",
        "Io": "You are Io, the investment specialist at Owl Bank. You help customers with investment options, portfolio advice, and financial planning."
    }
    
    agent_personality = personality_map.get(agent.name, f"You are {agent.name}, a {agent.role} support agent at Owl Bank.")
    
    return (
        f"{agent_personality}\n"
        f"IMPORTANT: Always identify yourself correctly as {agent.name}. Never claim to be a different agent.\n"
        f"Behavioral rules (critical):\n"
        f"- Never read out long lists of products or recommendations. Ask discovery questions first to narrow options.\n"
        f"- Ask ONE question at a time and wait for the customer's reply.\n"
        f"- Before a multistep task, ask: do they prefer step-by-step with confirmation at each step, or a summary of all steps? Default to step-by-step.\n"
        f"- Confirm understanding and get consent before moving to the next step.\n"
        f"- Keep utterances concise and optimized for TTS; avoid emojis and special characters.\n"
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
    openai_model = os.getenv('OPENAI_MODEL')  # Must be set in environment variables
    
    def __post_init__(self):
        if not self.openai_model:
            raise ValueError("OPENAI_MODEL environment variable is required but not set")

import asyncio

class LLMClient:
    def __init__(self, config: ConversationConfig):
        self.config = config
        logger.info(f"{Fore.CYAN}[DEBUG] About to create OpenAI() client in LLMClient{Style.RESET_ALL}")
        
        try:
            # Create OpenAI client - httpx==0.27.2 fixes the proxies compatibility issue
            self.client = OpenAI()
            logger.info(f"{Fore.GREEN}[DEBUG] OpenAI client created successfully in LLMClient{Style.RESET_ALL}")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Failed to create OpenAI client in LLMClient: {e}{Style.RESET_ALL}")
            import traceback
            logger.error(f"{Fore.RED}[ERR] OpenAI client traceback:\n{traceback.format_exc()}{Style.RESET_ALL}")
            raise

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
                    f"IMPORTANT: If you need to route to a specialist agent (Sunny, Max, or Io), "
                    f"provide a helpful response first, then add #route_to:<AgentName> at the very end. "
                    f"The routing command #route_to:<AgentName> will NOT be spoken to the customer. "
                    f"For example: 'Let me connect you with our wealth management expert. #route_to:Max'"
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
                f"IMPORTANT: If you need to route to a specialist agent (Sunny, Max, or Io), "
                f"provide a helpful response first, then add #route_to:<AgentName> at the very end. "
                f"The routing command #route_to:<AgentName> will NOT be spoken to the customer. "
                f"For example: 'Let me connect you with our wealth management expert. #route_to:Max'"
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
        
        logger.info(f"{Fore.CYAN}[DEBUG] Initializing standard LLM client{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}[DEBUG] OpenAI model: {self.config.openai_model}{Style.RESET_ALL}")
        
        # Always use standard LLM client (OpenAI Functions disabled)
        logger.info(f"{Fore.CYAN}[DEBUG] Creating standard LLMClient instance{Style.RESET_ALL}")
        self.llm_client = LLMClient(self.config)
        logger.info(f"{Fore.BLUE}[SYS] Standard LLM Client initialized successfully{Style.RESET_ALL}")
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
        # Initialize banking tools and conversations logger (standard version only)
        self.banking_tools = get_banking_tools()
        self.conversations_logger = get_conversations_logger()
        self.customer_phone = None  # Store customer phone for banking operations
        self.live_transcription_active = False  # Track if live transcription is active
        self.current_partial_transcript = {}  # Store partial transcripts by speaker

    async def broadcast_to_dashboard(self, payload: dict):
        msg = json.dumps(payload)
        for ws in self.dashboard_clients:
            try:
                await ws.send_str(msg)
            except Exception as e:
                logger.error(f"{Fore.RED}[ERR] Dashboard WS send failed: {e}{Style.RESET_ALL}\n")

    def update_transcription_state(self, event_type: str, data: dict):
        """Update the live transcription state based on incoming events"""
        if event_type == "transcription-started":
            self.live_transcription_active = True
            self.current_partial_transcript = {}
            logger.info(f"{Fore.GREEN}[TRANSCRIPT] Live transcription activated{Style.RESET_ALL}")
            
        elif event_type == "transcription-stopped":
            self.live_transcription_active = False
            self.current_partial_transcript = {}
            logger.info(f"{Fore.YELLOW}[TRANSCRIPT] Live transcription deactivated{Style.RESET_ALL}")
            
        elif event_type in ["utterance-partial", "utterance-final"]:
            speaker = data.get("speaker", "unknown")
            text = data.get("text", "")
            
            if event_type == "utterance-partial":
                # Update partial transcript for this speaker
                self.current_partial_transcript[speaker] = text
            elif event_type == "utterance-final":
                # Clear partial transcript for this speaker as it's now final
                if speaker in self.current_partial_transcript:
                    del self.current_partial_transcript[speaker]

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
        await self.broadcast_to_dashboard({"type": "setup", "ts": datetime.now(timezone.utc)
.isoformat(), "data": data})

        # Proactively inform Conversation Relay of initial language for TTS/STT
        try:
            if self.websocket:
                language_message = {
                    "type": "language",
                    "ttsLanguage": self.language,
                    "transcriptionLanguage": self.language,
                }
                await self.websocket.send_str(json.dumps(language_message))
                logger.info(f"{Fore.YELLOW}[LANG] Sent initial language to Conversation Relay: {language_message}{Style.RESET_ALL}\n")
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Failed to send initial language: {e}{Style.RESET_ALL}\n")

        # Extract customer phone number
        from_number = data.get("from", "")
        if from_number.startswith("whatsapp:"):
            self.customer_phone = from_number.replace("whatsapp:", "")
        else:
            self.customer_phone = from_number

        # Check if this is a WhatsApp call and route accordingly
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

        # Initialize voice conversation in Conversations Manager
        if self.customer_phone and self.conversation_sid and self.conversations_logger:
            conversation_sid = self.conversations_logger.create_voice_conversation(
                self.customer_phone, self.conversation_sid, self.active_agent
            )
            if conversation_sid:
                logger.info(f"{Fore.GREEN}[CONV] Started voice conversation tracking for {self.customer_phone}{Style.RESET_ALL}\n")
            else:
                logger.warning(f"{Fore.YELLOW}[CONV] Failed to start voice conversation tracking{Style.RESET_ALL}\n")

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

            # Log user speech to voice conversation
            if self.customer_phone and self.conversations_logger:
                self.conversations_logger.log_user_speech(self.customer_phone, text)

            # Use standard banking tools approach (OpenAI Functions disabled)
            banking_response = None
            if self.banking_tools and self.customer_phone:
                banking_response = self.banking_tools.process_user_input(text, self.customer_phone, self.language)
                
                if banking_response:
                    logger.info(f"{Fore.GREEN}[BANK] Banking response generated{Style.RESET_ALL}")
                    
                    # Log banking action
                    if self.conversations_logger:
                        self.conversations_logger.log_banking_action(
                            self.customer_phone, 
                            "balance_check", 
                            {"success": True, "response_generated": True}
                        )
                    
                    # Broadcast banking action to dashboard
                    await self.broadcast_to_dashboard({
                        "type": "banking-action",
                        "data": {
                            "action": "balance_check",
                            "customer_phone": self.customer_phone,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    })

            # If we have a banking response, use it; otherwise get AI response
            if banking_response:
                # Send banking response directly
                response_text = banking_response
                
                # Send token by token for consistency with streaming
                words = response_text.split()
                for i, word in enumerate(words):
                    if i == 0:
                        await self.send_response(word, partial=True)
                    else:
                        await self.send_response(f" {word}", partial=True)
                    # Small delay to simulate natural speech
                    await asyncio.sleep(0.05)
                
                # Update chat history
                self.chat_history.append({"role": "user", "content": text})
                self.chat_history.append({"role": "assistant", "content": response_text})
                
            else:
                # Get AI response using standard approach
                log_debug(f"[AI] Generating AI response for: {text}")
                self.chat_history.append({"role": "user", "content": text})
                
                # First, collect the complete response
                response_buffer = []
                token_count = 0
                async for token in self.llm_client.get_completion_from_history(
                    history=self.chat_history,
                    language=self.language,
                    agent_name=self.active_agent,
                    customer_profile=self.personalization
                ):
                    response_buffer.append(token)
                    token_count += 1
                    if DEBUG_MODE and token_count % 10 == 0:  # Log every 10 tokens in debug mode
                        log_debug(f"[AI] Received {token_count} tokens so far")
            
                response_text = ''.join(response_buffer).strip()
                log_debug(f"[AI] Complete response generated ({len(response_buffer)} tokens): {response_text[:100]}...")
                
                # Check for #route_to:<Agent> and remove it from the response
                route_match = re.search(r"#route_to:(\w+)", response_text)
                if route_match:
                    requested_agent = route_match.group(1)
                    # Remove the routing command from the response text before storing in history
                    clean_response = re.sub(r"\s*#route_to:\w+\s*", "", response_text).strip()
                    self.chat_history.append({"role": "assistant", "content": clean_response})
                    
                    if registry.get_agent(requested_agent):
                        logger.info(f"{Fore.YELLOW}[ROUTE] Routing to agent: {requested_agent}{Style.RESET_ALL}")
                        old_agent = self.active_agent
                        self.active_agent = requested_agent
                        logger.info(f"{Fore.GREEN}[AGENT] Active agent updated: {old_agent} -> {self.active_agent}{Style.RESET_ALL}")
                        
                        # Add context transfer message for the new agent
                        transfer_context = f"[CONTEXT: Customer was transferred from {old_agent} to you ({requested_agent}). Previous conversation context is available.]"
                        self.chat_history.append({"role": "system", "content": transfer_context})
                        
                        await self.broadcast_to_dashboard({
                            "type": "agent-switch",
                            "data": {"from": old_agent, "to": requested_agent}
                        })
                        
                        # Set response_text to the clean version without routing command
                        response_text = clean_response
                    else:
                        logger.warning(f"{Fore.YELLOW}[WARN] Unknown agent requested: {requested_agent}{Style.RESET_ALL}")
                        # Still clean the response even if agent is unknown
                        response_text = re.sub(r"\s*#route_to:\w+\s*", "", response_text).strip()
                        self.chat_history.append({"role": "assistant", "content": response_text})
                else:
                    self.chat_history.append({"role": "assistant", "content": response_text})
                
                # Stream response as meaningful text chunks for optimal TTS
                if response_text.strip():
                    log_debug(f"[TTS] Streaming complete response as text token: {len(response_text)} characters")
                    
                    # Send the complete response as a single text token for immediate TTS conversion
                    # This follows Twilio's recommendation to stream tokens as they become available
                    await self.send_response(response_text, partial=True)
                    log_debug(f"[TTS] Complete text token sent to ConversationRelay for vocalization")
                else:
                    log_debug(f"[TTS] No response text to stream")
            
            
            # Log agent response to voice conversation
            if self.customer_phone and self.conversations_logger and response_text:
                self.conversations_logger.log_agent_response(self.customer_phone, response_text)

            # Send final marker
            await self.send_response("", partial=False)
            
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Error processing input: {e}{Style.RESET_ALL}\n")
            await self.send_response("Desculpe, não consegui processar sua solicitação.", partial=False)
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] Error processing input: {e}{Style.RESET_ALL}\n")
            await self.send_response("Desculpe, não consegui processar sua solicitação.", partial=False)

    async def send_response(self, text: str, partial: bool = True):
        if not self.websocket:
            return

        # Build text token message following Twilio ConversationRelay specification
        msg = {
            "type": "text",
            "token": text,
            "last": not partial,
            "interruptible": self.latest_prompt_flags["interruptible"],
            "preemptible": self.latest_prompt_flags["preemptible"]
        }

        # Add language code for TTS (as per Twilio docs)
        if hasattr(self, 'language') and self.language:
            msg["lang"] = self.language

        # Log in debug mode but ALWAYS send
        if DEBUG_MODE:
            log_debug(f"[TTS] Sending text token to ConversationRelay: {json.dumps(msg, ensure_ascii=False)}")

        try:
            message_json = json.dumps(msg, ensure_ascii=False)
            await self.websocket.send_str(message_json)

            if DEBUG_MODE:
                log_debug(f"[TTS] Text token sent successfully: {len(message_json)} bytes")

        except Exception as e:
            logger.error(f"[ERR] Failed to send text token: {e}")
            if DEBUG_MODE:
                log_debug(f"[TTS] WebSocket send error: {type(e).__name__}: {str(e)}")

# Global PWA WebSocket clients set for transcription streaming
pwa_clients = set()

async def broadcast_to_pwa_clients(payload: dict):
    """Broadcast transcription events to connected PWA clients"""
    global pwa_clients
    if not pwa_clients:
        return
        
    msg = json.dumps(payload)
    disconnected_clients = set()
    
    for ws in pwa_clients:
        try:
            await ws.send_str(msg)
        except Exception as e:
            logger.error(f"{Fore.RED}[ERR] PWA WebSocket send failed: {e}{Style.RESET_ALL}")
            disconnected_clients.add(ws)
    
    # Clean up disconnected clients
    pwa_clients -= disconnected_clients

async def handle_pwa_websocket(request):
    """Handle WebSocket connections from PWA for transcription streaming"""
    global pwa_clients
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    pwa_clients.add(ws)
    logger.info(f"{Fore.GREEN}[PWA] New PWA WebSocket connection - {len(pwa_clients)} clients connected{Style.RESET_ALL}")
    
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                # Handle any messages from PWA if needed
                pass
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"{Fore.RED}[ERR] PWA WebSocket error: {ws.exception()}{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] PWA WebSocket error: {e}{Style.RESET_ALL}")
    finally:
        pwa_clients.discard(ws)
        logger.info(f"{Fore.YELLOW}[PWA] PWA WebSocket disconnected - {len(pwa_clients)} clients remaining{Style.RESET_ALL}")
    
    return ws

def safe_json(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def sanitize_json(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
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

async def process_transcription_event(event_type: str, data: dict, call_sid: str, timestamp: str, ws_handler):
    """Process transcription events asynchronously without blocking main flow"""
    try:
        transcription_payload = {
            "type": "live-transcription",
            "ts": timestamp,
            "data": {
                "event": event_type,
                "call_sid": call_sid,
                "transcript_sid": data.get("TranscriptionSid"),
                "raw_data": data
            }
        }
        
        # Handle different transcription events
        if event_type == "transcription-started":
            logger.info(f"{Fore.GREEN}[TRANSCRIPT] Started for call {call_sid}{Style.RESET_ALL}")
            transcription_payload["data"]["status"] = "started"
            
        elif event_type == "transcription-stopped":
            logger.info(f"{Fore.YELLOW}[TRANSCRIPT] Stopped for call {call_sid}{Style.RESET_ALL}")
            transcription_payload["data"]["status"] = "stopped"
            
        elif event_type == "transcription-content":
            # Parse transcription data JSON
            transcription_data = data.get("TranscriptionData", "{}")
            try:
                import urllib.parse
                decoded_data = urllib.parse.unquote(transcription_data)
                transcript_info = json.loads(decoded_data)
                
                transcript_text = transcript_info.get("transcript", "")
                confidence = transcript_info.get("confidence", 0)
                
                # Determine speaker from track
                track = data.get("Track", "")
                speaker = "customer" if "inbound" in track else "agent" if "outbound" in track else "unknown"
                
                is_final = data.get("Final", "false").lower() == "true"
                
                logger.info(f"{Fore.CYAN}[TRANSCRIPT] {speaker}: {transcript_text[:80]}...{Style.RESET_ALL}")
                
                transcription_payload["data"].update({
                    "text": transcript_text,
                    "speaker": speaker,
                    "track": track,
                    "confidence": confidence,
                    "is_final": is_final,
                    "is_partial": not is_final
                })
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"{Fore.RED}[ERR] Failed to parse transcription data: {e}{Style.RESET_ALL}")
                return
        
        # Update handler state and broadcast to dashboard and PWA
        ws_handler.update_transcription_state(event_type, transcription_payload.get("data", {}))
        await ws_handler.broadcast_to_dashboard(transcription_payload)
        
        # Also broadcast to PWA clients
        try:
            await broadcast_to_pwa_clients(transcription_payload)
        except Exception as pwa_error:
            logger.error(f"{Fore.RED}[ERR] PWA broadcast failed: {pwa_error}{Style.RESET_ALL}")
        
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Error processing transcription event: {e}{Style.RESET_ALL}")

async def generate_voice_twiml(request):
    """Generate TwiML for incoming voice calls with real-time transcription"""
    try:
        # Get the host from the request to build the callback URL
        host = request.host
        scheme = request.scheme
        transcription_callback_url = f"{scheme}://{host}/transcripts"
        
        logger.info(f"{Fore.GREEN}[TWIML] Generating voice TwiML with transcription callback: {transcription_callback_url}{Style.RESET_ALL}")
        
        # Generate TwiML with transcription
        twiml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Transcription 
            statusCallbackUrl="{transcription_callback_url}" 
            name="Voice Call Transcription" 
            speechModel="telephony" 
            transcriptionEngine="google" 
            partialResults="true" 
            enableAutomaticPunctuation="true"
        />
    </Start>
    <Connect>
        <ConversationRelay url="wss://{host}/websocket"/>
    </Connect>
</Response>'''
        
        return web.Response(
            text=twiml_response,
            content_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Error generating voice TwiML: {e}{Style.RESET_ALL}")
        # Fallback TwiML without transcription
        fallback_twiml = '''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay/>
    </Connect>
</Response>'''
        return web.Response(
            text=fallback_twiml,
            content_type="application/xml"
        )

async def handle_transcription_webhook(request, ws_handler: TwilioWebSocketHandler):
    """Handle Real Time Transcription status callbacks from Twilio"""
    try:
        # Twilio sends form-encoded data, not JSON
        data = dict(await request.post())
        
        # Extract event type from TranscriptionEvent field
        event_type = data.get("TranscriptionEvent") or data.get("transcription_event")
        
        # Extract common fields from form data
        call_sid = data.get("CallSid")
        transcript_sid = data.get("TranscriptionSid")
        timestamp = data.get("Timestamp") or datetime.now(timezone.utc).isoformat()
        
        logger.info(f"{Fore.CYAN}[TRANSCRIPT] Event: {event_type}, Call: {call_sid}{Style.RESET_ALL}")
        
        # Process transcription asynchronously to avoid blocking main conversation flow
        asyncio.create_task(process_transcription_event(event_type, data, call_sid, timestamp, ws_handler))
        
        # Return immediately to avoid blocking
        return web.Response(text="OK", status=200)
        
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Error handling transcription webhook: {e}{Style.RESET_ALL}")
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

async def proxy_to_conversations(request):
    """Reverse proxy to forward requests to the Conversations API server on port 3002"""
    try:
        # Extract the path after /conversations
        path = request.match_info.get('path', '')
        target_url = f"http://127.0.0.1:3002/{path}"
        
        # Add query parameters if present
        if request.query_string:
            target_url += f"?{request.query_string}"
        
        # Prepare headers, exclude Host header
        headers = dict(request.headers)
        headers.pop('Host', None)
        
        # Get request body
        data = await request.read()
        
        # Forward the request to the Conversations server
        async with aiohttp.ClientSession() as session:
            async with session.request(
                request.method,
                target_url,
                headers=headers,
                data=data,
                allow_redirects=False
            ) as resp:
                # Read response body
                body = await resp.read()
                
                # Prepare response headers
                response_headers = dict(resp.headers)
                # Remove headers that shouldn't be forwarded
                for header in ['Transfer-Encoding', 'Connection', 'Content-Encoding']:
                    response_headers.pop(header, None)
                
                return web.Response(
                    status=resp.status,
                    body=body,
                    headers=response_headers
                )
                
    except aiohttp.ClientConnectorError:
        logger.error(f"{Fore.RED}[PROXY] Cannot connect to Conversations server on port 3002{Style.RESET_ALL}")
        return web.json_response(
            {"error": "Conversations service unavailable", "message": "Make sure the Conversations server is running on port 3002"},
            status=503
        )
    except Exception as e:
        logger.error(f"{Fore.RED}[PROXY] Error proxying to Conversations: {e}{Style.RESET_ALL}")
        return web.json_response(
            {"error": "Proxy error", "message": str(e)},
            status=502
        )

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
            limit=100
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

def setup_ngrok_tunnel(port: int):
    """Setup ngrok tunnel if environment variables are present"""
    # Check if pyngrok is available
    if not NGROK_AVAILABLE:
        logger.info(f"{Fore.YELLOW}[NGROK] pyngrok not available - skipping tunnel setup{Style.RESET_ALL}")
        return None
        
    ngrok_domain = os.getenv('NGROK_DOMAIN')
    ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
    
    # Only setup ngrok if environment variables are present
    if not (ngrok_domain or ngrok_auth_token):
        logger.info(f"{Fore.YELLOW}[NGROK] No ngrok configuration found in environment variables{Style.RESET_ALL}")
        return None
    
    try:
        logger.info(f"{Fore.BLUE}[NGROK] Setting up ngrok tunnel...{Style.RESET_ALL}")
        
        # Set auth token if provided
        if ngrok_auth_token:
            ngrok.set_auth_token(ngrok_auth_token)
            logger.info(f"{Fore.GREEN}[NGROK] Auth token configured{Style.RESET_ALL}")
        
        # Connect tunnel
        if ngrok_domain:
            logger.info(f"{Fore.BLUE}[NGROK] Using domain from .env: {ngrok_domain}{Style.RESET_ALL}")
            tunnel = ngrok.connect(port, domain=ngrok_domain)
        else:
            logger.info(f"{Fore.BLUE}[NGROK] Generating new tunnel...{Style.RESET_ALL}")
            tunnel = ngrok.connect(port)
        
        # Extract the URL string from the tunnel object
        public_url = str(tunnel.public_url)
        
        logger.info(f"{Fore.GREEN}[NGROK] Tunnel established!{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[NGROK] Public URL: {public_url}{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[NGROK] WebSocket URL: {public_url.replace('http', 'ws')}/websocket{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[NGROK] Dashboard: {public_url}/dashboard{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[NGROK] Voice TwiML: {public_url}/voice{Style.RESET_ALL}")
        logger.info(f"{Fore.GREEN}[NGROK] Webhooks: {public_url}/webhook{Style.RESET_ALL}")
        
        return public_url
        
    except Exception as e:
        logger.error(f"{Fore.RED}[NGROK] Failed to setup tunnel: {e}{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}[NGROK] Continuing without tunnel...{Style.RESET_ALL}")
        return None

async def main():
    ws_handler = TwilioWebSocketHandler()
    app = web.Application()
    
    # Setup Jinja2 templates
    BASE_DIR = pathlib.Path(__file__).parent
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(str(BASE_DIR / "templates")))

    app.router.add_get('/dashboard', handle_dashboard)
    app.router.add_get('/dashboard-ws', lambda req: handle_dashboard_ws(req, ws_handler))
    app.router.add_get('/pwa-transcripts', handle_pwa_websocket)

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
    app.router.add_post('/transcripts', lambda request: handle_transcription_webhook(request, ws_handler))
    app.router.add_post('/voice', generate_voice_twiml)
    app.router.add_get('/voice', generate_voice_twiml)
    app.router.add_get('/', lambda request: web.Response(text="Twilio WebSocket/HTTP Server Running"))
    app.router.add_get('/health', lambda request: web.json_response({
        "status": "healthy",
        "service": "signal-sp-session",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv('DEPLOYMENT_ENVIRONMENT', 'local')
    }))
    app.router.add_get('/intel-aggregates', lambda req: web.json_response(
        sanitize_json(load_aggregated_intel_results(req.rel_url.query.get("group", "day")))
    ))
    app.router.add_get('/intel-events', lambda req: web.json_response(load_recent_events()))
    app.router.add_get('/conversation/{conversation_sid}/intelligence', get_conversation_intelligence)
    app.router.add_get('/test-transcripts', test_transcripts)
    
    # Reverse proxy routes to Conversations API server
    try:
        # Register proxy routes for specific HTTP methods to avoid conflicts
        app.router.add_get('/conversations/{path:.*}', proxy_to_conversations)
        app.router.add_post('/conversations/{path:.*}', proxy_to_conversations)
        app.router.add_put('/conversations/{path:.*}', proxy_to_conversations)
        app.router.add_delete('/conversations/{path:.*}', proxy_to_conversations)
        app.router.add_patch('/conversations/{path:.*}', proxy_to_conversations)
        log_debug(f"[INIT] Conversations proxy routes registered successfully")
    except ValueError as e:
        # Route might already be registered, log and continue
        log_debug(f"[WARN] Conversations route registration skipped: {e}")



    for route in list(app.router.routes()):
        cors.add(route)
    
    # Environment-aware host and port configuration
    deployment_env = os.getenv('DEPLOYMENT_ENVIRONMENT', 'local')
    if deployment_env in ['render', 'heroku', 'aws', 'gcp']:
        host = "0.0.0.0"  # Bind to all interfaces for cloud deployment
        port = int(os.getenv('PORT', 8080))
        # Skip ngrok setup in production environments
        public_url = None
        logger.info(f"{Fore.BLUE}[SYS] Production environment detected: {deployment_env}{Style.RESET_ALL}")
    else:
        host = "localhost"
        port = int(os.getenv('PORT', 8080))
        # Setup ngrok tunnel if configured for local development
        public_url = setup_ngrok_tunnel(port)
    
    logger.info(f"{Fore.BLUE}[SYS] Starting Twilio WebSocket/HTTP server on {host}:{port}{Style.RESET_ALL}\n")
    
    if public_url:
        # Display ngrok URLs
        logger.info(f"{Fore.GREEN}[SYS] Server accessible via ngrok: {public_url}{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] WebSocket endpoint: {public_url.replace('http', 'ws')}/websocket{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] HTTP webhook endpoint: {public_url}/webhook{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] Voice TwiML endpoint: {public_url}/voice{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] Transcription webhook endpoint: {public_url}/transcripts{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] PWA transcription WebSocket: {public_url.replace('http', 'ws')}/pwa-transcripts{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] Dashboard: {public_url}/dashboard{Style.RESET_ALL}\n")
    else:
        # Display local URLs
        logger.info(f"{Fore.BLUE}[SYS] WebSocket endpoint: ws://{host}:{port}/websocket{Style.RESET_ALL}\n")
        logger.info(f"{Fore.BLUE}[SYS] HTTP webhook endpoint: http://{host}:{port}/webhook{Style.RESET_ALL}\n")
        logger.info(f"{Fore.CYAN}[SYS] Voice TwiML endpoint: http://{host}:{port}/voice{Style.RESET_ALL}\n")
        logger.info(f"{Fore.CYAN}[SYS] Transcription webhook endpoint: http://{host}:{port}/transcripts{Style.RESET_ALL}\n")
        logger.info(f"{Fore.GREEN}[SYS] PWA transcription WebSocket: ws://{host}:{port}/pwa-transcripts{Style.RESET_ALL}\n")
        logger.info(f"{Fore.CYAN}[SYS] Dashboard: http://{host}:{port}/dashboard{Style.RESET_ALL}\n")
    
    # Get the intelligence service SID from environment variables
    intelligence_service_sid = os.getenv("TWILIO_INTELLIGENCE_SERVICE_SID")
    if intelligence_service_sid:
        await preload_transcripts_for_service(intelligence_service_sid, ws_handler)
    else:
        logger.warning(f"{Fore.YELLOW}[WARN] TWILIO_INTELLIGENCE_SERVICE_SID not found in environment variables{Style.RESET_ALL}")
    
    # Configure access logging - disable in production, enable in debug mode
    access_log = logger if DEBUG_MODE else None
    runner = web.AppRunner(app, access_log=access_log)
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
        # Clean up ngrok tunnels if available
        if NGROK_AVAILABLE:
            try:
                ngrok.disconnect_all()
                ngrok.kill()
                logger.info(f"{Fore.YELLOW}[NGROK] Tunnels disconnected{Style.RESET_ALL}\n")
            except Exception as ngrok_error:
                logger.error(f"{Fore.RED}[NGROK] Error cleaning up tunnels: {ngrok_error}{Style.RESET_ALL}\n")
    except Exception as e:
        logger.error(f"{Fore.RED}[ERR] Server error: {e}{Style.RESET_ALL}\n")
        # Clean up ngrok tunnels on error too if available
        if NGROK_AVAILABLE:
            try:
                ngrok.disconnect_all()
                ngrok.kill()
            except:
                pass
