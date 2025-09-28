# Real-Time Transcription Streaming

This document explains the new Real-Time Transcription streaming feature that allows you to receive live transcription events from Twilio's Voice API during phone calls.

## Overview

The transcription streaming feature enables real-time processing of voice conversations by:

1. **Setting up Real-Time Transcription** via TwiML when a call starts
2. **Receiving live transcription events** through webhooks as the conversation progresses
3. **Broadcasting events** to connected dashboard clients via WebSocket
4. **Managing transcription state** throughout the call lifecycle

## Architecture

```
Phone Call → Twilio Voice API → TwiML (/voice) → Conversation Relay
                                     ↓
Real-Time Transcription → Webhook (/transcripts) → Dashboard WebSocket
```

## Endpoints

### 1. Voice TwiML Endpoint
- **URL**: `GET/POST /voice`
- **Purpose**: Returns TwiML with Real-Time Transcription configuration
- **Response**: XML with `<Start><Transcription>` elements

**Example TwiML Response:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Start>
        <Transcription 
            statusCallbackUrl="https://your-domain.com/transcripts" 
            name="Voice Call Transcription" 
            speechModel="telephony" 
            transcriptionEngine="google" 
            partialResults="true" 
            enableAutomaticPunctuation="true"
        />
    </Start>
    <Connect>
        <ConversationRelay url="wss://your-domain.com/websocket"/>
    </Connect>
</Response>
```

### 2. Transcription Webhook Endpoint
- **URL**: `POST /transcripts`
- **Purpose**: Receives Real-Time Transcription status callbacks from Twilio
- **Content-Type**: `application/json`

**Supported Events:**
- `transcription-started`: When transcription begins
- `utterance-partial`: Partial transcript text (real-time)
- `utterance-final`: Final transcript text for an utterance
- `transcription-stopped`: When transcription ends

## Event Types

### Transcription Started
```json
{
    "event": "transcription-started",
    "CallSid": "CA1234567890abcdef",
    "Name": "Voice Call Transcription",
    "Timestamp": "2025-01-08T13:00:00Z"
}
```

### Utterance Events
```json
{
    "event": "utterance-partial",  // or "utterance-final"
    "CallSid": "CA1234567890abcdef",
    "TranscriptText": "Hello, how can I help you today?",
    "Channel": "1",  // 1 = customer, 2 = agent
    "Confidence": "0.95",
    "Timestamp": "2025-01-08T13:00:15Z"
}
```

### Transcription Stopped
```json
{
    "event": "transcription-stopped",
    "CallSid": "CA1234567890abcdef", 
    "Name": "Voice Call Transcription",
    "Timestamp": "2025-01-08T13:10:00Z"
}
```

## Dashboard Integration

Transcription events are automatically broadcasted to connected dashboard clients via WebSocket:

```json
{
    "type": "live-transcription",
    "ts": "2025-01-08T13:00:15Z",
    "data": {
        "event": "utterance-final",
        "call_sid": "CA1234567890abcdef",
        "text": "Hello, how can I help you today?",
        "speaker": "customer",
        "channel": "1",
        "confidence": "0.95",
        "is_partial": false,
        "is_final": true
    }
}
```

## Configuration

### Twilio Phone Number Setup

Configure your Twilio phone number webhook URL to point to the `/voice` endpoint:

1. Go to Twilio Console → Phone Numbers → Manage → Active Numbers
2. Select your phone number
3. Set **Voice Webhook URL** to: `https://your-domain.com/voice`
4. Set **HTTP Method** to `POST`
5. Save the configuration

### Environment Variables

Ensure these environment variables are set in your `.env` file:

```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
DEBUG_MODE=false  # Set to true for verbose logging
```

## Usage

### 1. Start the Server

```bash
cd "Signal SP Session"
python server.py
```

The server will start on `localhost:8080` with the following endpoints:
- Voice TwiML: `http://localhost:8080/voice`
- Transcription webhook: `http://localhost:8080/transcripts`
- Dashboard: `http://localhost:8080/dashboard`
- Dashboard WebSocket: `ws://localhost:8080/dashboard-ws`

### 2. Make a Voice Call

When someone calls your Twilio phone number:

1. Twilio requests TwiML from `/voice`
2. TwiML includes transcription configuration
3. Call connects with real-time transcription enabled
4. Transcription events stream to `/transcripts` webhook
5. Events are processed and broadcasted to dashboard

### 3. Monitor Live Transcription

Open the dashboard at `http://localhost:8080/dashboard` to see:
- Live transcription events
- Speaker identification (customer vs. agent)
- Partial and final transcript text
- Transcription confidence scores

## Testing

Use the included test script to verify functionality:

```bash
# Test all endpoints
python test_transcription.py

# Test specific functionality
python -c "from test_transcription import test_voice_twiml; test_voice_twiml()"
python -c "from test_transcription import test_transcription_webhook; test_transcription_webhook()"
```

### Manual Testing with curl

**Test Voice TwiML:**
```bash
curl http://localhost:8080/voice
```

**Test Transcription Webhook:**
```bash
curl -X POST http://localhost:8080/transcripts \
  -H "Content-Type: application/json" \
  -d '{
    "event": "utterance-final",
    "CallSid": "CA1234567890",
    "TranscriptText": "Hello world",
    "Channel": "1",
    "Confidence": "0.95"
  }'
```

## Troubleshooting

### Common Issues

1. **Webhook not receiving events**
   - Verify your domain is publicly accessible
   - Check Twilio phone number webhook configuration
   - Ensure `/transcripts` endpoint is reachable

2. **TwiML not working**
   - Verify `/voice` endpoint returns valid XML
   - Check Twilio phone number Voice webhook URL
   - Test with curl to ensure endpoint responds

3. **Dashboard not showing events**
   - Verify WebSocket connection to `/dashboard-ws`
   - Check browser console for connection errors
   - Ensure server is broadcasting events

### Debug Mode

The server has two logging modes:

**Clean Mode (Default)**: `DEBUG_MODE=false`
- Only shows colorama-formatted application logs
- No HTTP request/response details
- No access logs or SDK noise
- Perfect for demos and production

**Verbose Mode**: `DEBUG_MODE=true` 
- Shows all HTTP requests and responses
- Displays detailed headers and payloads
- Shows aiohttp access logs
- Includes Twilio SDK debug information

Enable verbose logging by setting `DEBUG_MODE=true` in your `.env` file:

```bash
DEBUG_MODE=true
```

Verbose mode provides detailed logging of:
- Transcription webhook payloads
- HTTP request/response cycles
- Event processing details
- WebSocket broadcasting
- Error diagnostics

### Logs

Key log prefixes to look for:

- `[TRANSCRIPT]` - Transcription-related events
- `[TWIML]` - TwiML generation
- `[SYS]` - System messages
- `[ERR]` - Error messages

## Security Considerations

1. **Webhook Validation**: Consider implementing Twilio webhook signature validation
2. **HTTPS**: Use HTTPS in production for webhook endpoints
3. **Access Control**: Restrict access to dashboard and sensitive endpoints
4. **Data Privacy**: Handle transcript data according to privacy regulations

## Next Steps

- Integrate with Twilio Intelligence for advanced analytics
- Add transcript persistence to database
- Implement speaker diarization
- Add real-time sentiment analysis
- Create transcript export functionality

## API Reference

For more details on Twilio Real-Time Transcription, see:
- [Twilio Voice TwiML Transcription](https://www.twilio.com/docs/voice/twiml/transcription)
- [Real-Time Transcription Guide](https://www.twilio.com/docs/voice/tutorials/transcription)
