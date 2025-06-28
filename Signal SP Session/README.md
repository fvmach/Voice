
# Signal SP Session

A real-time voice analysis system using Twilio Voice and AI for customer experience insights.

## Overview

This project demonstrates real-time voice signal processing and analysis during phone calls, combining Twilio's Voice API with AI capabilities for customer experience monitoring.

## Files

### `server.py`
The main application server that handles:
- Twilio Voice webhooks for incoming calls
- Real-time audio streaming and processing
- WebSocket connections for live updates
- AI-powered sentiment analysis and insights

### `signal-sp-notebook.ipynb`
Jupyter notebook containing:
- Data analysis and visualization examples
- Signal processing demonstrations
- AI model testing and validation
- Performance metrics and insights

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Key dependencies include:
- `twilio` - Twilio API integration
- `aiohttp` - Async web server
- `openai` - AI processing capabilities
- `asyncio-mqtt` - Real-time messaging
- `pandas` - Data analysis

## Setup

1. Clone the repository
2. Install requirements: `pip install -r requirements.txt`
3. Configure environment variables for Twilio and OpenAI
4. Run the server: `python server.py`

## Usage

1. Start the server
2. Configure Twilio webhook URLs
3. Make test calls to see real-time analysis
4. Review insights in the notebook
