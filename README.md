
# Twilio Conversation Relay Voice Assistant

A real-time voice conversation assistant built with Twilio's Conversation Relay API, featuring multi-language support and OpenAI integration.

## Features

- **Real-time Voice Conversations**: WebSocket-based communication with Twilio's Conversation Relay
- **Multi-language Support**: Automatic language detection and switching (Portuguese, English, Spanish)
- **OpenAI Integration**: GPT-powered conversational AI with streaming responses
- **Live Dashboard**: Real-time monitoring of conversation events
- **DTMF Support**: Handle touch-tone inputs during calls

## Architecture

The application consists of:
- **WebSocket Handler**: Manages Twilio Conversation Relay events
- **LLM Client**: Handles OpenAI API interactions with streaming
- **Language Detection**: Automatic language switching based on user input
- **Dashboard Broadcasting**: Real-time event monitoring

## Prerequisites

- Python 3.8+
- Twilio Account with Conversation Relay access
- OpenAI API key
- Required dependencies (see `requirements.txt`)

## Installation

1. Clone the repository
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Create a `.env` file with your credentials:
    ```
    OPENAI_API_KEY=your_openai_key
    TWILIO_ACCOUNT_SID=your_twilio_sid
    TWILIO_AUTH_TOKEN=your_twilio_token
    ```

## Usage

Run the server:
```bash
python server-backup.py
```

The application will handle incoming Twilio Conversation Relay events and provide AI-powered responses through voice synthesis.

## Supported Events

- `setup`: Initialize conversation
- `prompt`: Process voice input from user
- `interrupt`: Handle conversation interruptions
- `dtmf`: Process touch-tone inputs
- `info`/`debug`: System information events

## Configuration

Modify `ConversationConfig` to adjust:
- Response timeouts
- Buffer sizes
- OpenAI model selection
- Language detection patterns
