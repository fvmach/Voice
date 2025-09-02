# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Common Development Commands

### Running Servers

**Main Voice Assistant Server (Conversation Relay):**
```bash
python server-backup.py
```
- Runs the main WebSocket server for Twilio Conversation Relay on `localhost:8080`
- Handles real-time voice conversations with multi-language support
- Provides live dashboard at `/dashboard` and WebSocket at `/websocket`

**Signal SP Session Server (Voice Analytics):**
```bash
cd "Signal SP Session"
python server.py
```
- Advanced voice analytics server with AI-powered insights
- Integrates with Twilio Intelligence for conversation analysis
- Includes real-time dashboard and data persistence

**Conversational Intelligence Webhook Server:**
```bash
cd "Conversational Intelligence"
python server.py
```
- Flask-based webhook receiver for Twilio Intelligence events
- Runs on port 4000 with ngrok tunnel for external webhooks
- Detailed payload logging and analysis

### Environment Setup

**Install dependencies for each component:**
```bash
# Main server
pip install -r requirements.txt  # If available, or install manually

# Signal SP Session
cd "Signal SP Session"
pip install -r requirements.txt

# Common packages across all components
pip install aiohttp aiohttp-cors aiohttp-jinja2 openai python-dotenv twilio colorama jinja2 pandas
```

**Environment variables required (create `.env` file):**
```
OPENAI_API_KEY=your_openai_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
SEGMENT_SPACE_ID=your_segment_space_id  # For personalization
SEGMENT_ACCESS_SECRET=your_segment_token
NGROK_DOMAIN=your_ngrok_domain  # Optional
DEBUG_MODE=false  # Set to true for verbose logging
```

### Data Management

**View intelligence results:**
```bash
cd "Signal SP Session"
# Results are stored in data/intel_results.ndjson (flat format)
# Raw results in data/intel_raw_results.ndjson
cat data/intel_results.ndjson | jq .  # Pretty print JSON
```

**Clear webhook data:**
```bash
curl -X POST http://localhost:4000/data/clear
```

### Development Workflow

**Start development environment:**
```bash
# Terminal 1: Main conversation relay server
python server-backup.py

# Terminal 2: Analytics server (if needed)
cd "Signal SP Session" && python server.py

# Terminal 3: Webhook server (if testing intelligence features)
cd "Conversational Intelligence" && python server.py
```

## Architecture Overview

### Core Components

**1. Conversation Relay Handler (`server-backup.py`)**
- `TwilioWebSocketHandler`: Main WebSocket connection manager for Twilio Conversation Relay
- `LLMClient`: OpenAI integration with streaming responses
- Real-time language detection and switching (Portuguese, English, Spanish)
- Dashboard broadcasting for live monitoring
- Event types: `setup`, `prompt`, `interrupt`, `dtmf`, `info/debug`

**2. Signal Processing & Analytics (`Signal SP Session/`)**
- Advanced voice analytics with Twilio Intelligence integration
- `flatten_intel_result()`: Extracts CSAT, CES, sentiment, and legal risk scores
- Persistent data storage in NDJSON format
- Aggregation functions for time-based analysis (day/week/month/year)
- Customer personalization via Twilio Segment integration

**3. Intelligence Webhook Receiver (`Conversational Intelligence/`)**
- Flask-based webhook endpoint for Twilio Intelligence events
- Detailed payload analysis and logging
- Real-time transcription handling
- Operator results processing (CSAT, sentiment, etc.)

### Data Flow Architecture

```
Phone Call → Twilio Conversation Relay → WebSocket Handler → OpenAI LLM
                                      ↓
Twilio Intelligence → Webhook Server → Analytics Processing → Dashboard
                                    ↓
                            Data Persistence (NDJSON)
```

### Key Integrations

**External Services:**
- **OpenAI GPT**: Conversational AI with streaming responses
- **Twilio Conversation Relay**: Real-time voice processing
- **Twilio Intelligence**: Advanced conversation analytics
- **Twilio Segment**: Customer personalization context
- **ngrok**: Webhook tunneling for local development

**Personalization System (`tools/personalization.py`):**
- Segment profile fetching by phone number
- Customer context injection into conversations
- Supports both inbound and outbound call directions

### Configuration Classes

**`ConversationConfig`** (in `server-backup.py`):
- `sentence_end_patterns`: Text completion detection
- `partial_timeout`: Streaming response timing
- `max_buffer_size`: Input buffer limits
- `openai_model`: LLM model selection

### Data Persistence

**Intelligence Results Structure:**
- Flat format in `data/intel_results.ndjson`
- Raw format in `data/intel_raw_results.ndjson`
- Fields: CSAT scores, CES scores, sentiment analysis, legal risk, hallucination detection
- Aggregation support for time-based analytics

### Language Support

**Multi-language Detection:**
- Automatic switching between Portuguese (pt-BR), English (en-US), Spanish (es-US)
- Pattern-based detection using regex
- Real-time language change notifications to Conversation Relay
- Localized system prompts and responses

### Dashboard & Monitoring

**Live Dashboard Features:**
- Real-time conversation events
- Language switching notifications  
- Analytics visualization
- WebSocket-based updates
- Intelligence results aggregation

### Error Handling & Logging

**Logging System:**
- Color-coded console output using colorama
- Event-specific prefixes: `[SYS]`, `[STT]`, `[SPI]`, `[ERR]`
- Debug mode toggle via environment variables
- Comprehensive error logging for all components

## Development Notes

### Code Patterns

**Async/Await Usage:**
- All WebSocket handling is async
- OpenAI streaming implemented with `asyncio.to_thread()`
- Broadcast functions for real-time dashboard updates

**Data Processing:**
- JSON-safe serialization with custom handlers
- Pandas integration for analytics aggregation
- NDJSON format for append-only data persistence

**WebSocket Event Routing:**
- Pattern matching for event type handling
- Graceful error recovery and connection management
- Real-time bidirectional communication

### Testing Approach

**Local Development:**
- Use ngrok for webhook testing
- Debug mode for verbose logging
- Dashboard monitoring for real-time feedback

**Data Validation:**
- JSON schema validation for webhook payloads
- Safe data extraction with fallback values
- Graceful handling of missing or malformed data
