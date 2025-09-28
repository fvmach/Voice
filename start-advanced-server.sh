#!/bin/bash

# Start the advanced server with specialist agents and banking integration
echo "Starting advanced Twilio Conversation Relay server with specialist agents..."
echo "This server includes:"
echo "  - Specialist agent routing (Olli, Sunny, Max, Io)"
echo "  - Banking API integration"
echo "  - Customer personalization via Twilio Segment"
echo "  - Intelligence analytics"
echo ""

echo "Note: Make sure the following Python packages are installed:"
echo "  pip install aiohttp-cors aiohttp aiohttp-jinja2 openai python-dotenv twilio colorama jinja2 pandas requests"
echo ""
echo "Starting server..."
echo ""

cd "Signal SP Session"
python3 server.py
