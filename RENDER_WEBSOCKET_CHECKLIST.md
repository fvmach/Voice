# Render WebSocket Deployment Checklist

## TwiML Configuration
- [x] Use `wss://` protocol (not `ws://`)
- [x] Use domain without port: `wss://twilio-cross-channel-cx-mas-demo.onrender.com/websocket`
- [x] No port specification in TwiML Bin

## Server Configuration  
- [x] WebSocket heartbeat enabled (30s)
- [x] Compression enabled
- [x] Proper timeout handling
- [x] Connection state validation
- [x] Error handling for ConnectionResetError/TimeoutError

## Expected Behavior After Deploy
- [ ] WebSocket connection established in logs
- [ ] Text tokens sent successfully 
- [ ] tokensPlayed events received
- [ ] TTS audio working on calls

## Debug Commands
```bash
# Test WebSocket connection
python -m websockets wss://twilio-cross-channel-cx-mas-demo.onrender.com/websocket

# Check Render logs
# Look for:
# - [WS] WebSocket connection request
# - [SYS] New WebSocket connection established  
# - [TTS] Sending WebSocket message
# - [SPI] Event received
```

## Common Issues
- Free tier: 5-minute connection timeout (upgrade to Pro fixed)
- Port specification: Remove ports from client URLs
- Protocol: Must use wss:// not ws://
- Compression: Enable for better performance