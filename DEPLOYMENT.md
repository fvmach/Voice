# Deployment Guide

This application supports three deployment environments: **Local**, **Render**, and **Railway**. Each environment has optimized WebSocket configurations.

## Quick Start

### Local Development

```bash
# Set environment
export DEPLOYMENT_ENVIRONMENT=local

# Terminal 1: Conversations Manager (Port 3002)
cd Conversations && node server.js

# Terminal 2: Signal SP Session (Port 3001)
cd "Signal SP Session" && python server.py
```

### Render Deployment

**Note**: Render has WebSocket limitations that may cause TTS issues during long AI processing times. Consider Railway for production.

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure:
   - **Build Command**: `pip install -r requirements.txt && cd Conversations && npm ci && cd client && npm ci && npm run build`
   - **Start Command**: `cd "Signal SP Session" && python server.py`
   - **Environment Variables**:
     - `DEPLOYMENT_ENVIRONMENT=render`
     - `PORT` (auto-generated)
     - `OPENAI_API_KEY`
     - `TWILIO_ACCOUNT_SID`
     - `TWILIO_AUTH_TOKEN`
     - (Add all other required variables from `.env`)

**Render WebSocket Settings**:
- Heartbeat: 20s
- Timeout: 45s
- Keep-alive interval: 15s

### Railway Deployment (Recommended for Production)

Railway offers better WebSocket support and is recommended for production use.

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login and initialize:
   ```bash
   railway login
   railway init
   ```

3. Link to your project:
   ```bash
   railway link
   ```

4. Set environment variables:
   ```bash
   railway variables set DEPLOYMENT_ENVIRONMENT=railway
   railway variables set OPENAI_API_KEY=your_key
   railway variables set TWILIO_ACCOUNT_SID=your_sid
   railway variables set TWILIO_AUTH_TOKEN=your_token
   # Add all other required variables
   ```

5. Deploy:
   ```bash
   railway up
   ```

**Railway WebSocket Settings**:
- Heartbeat: 30s
- Timeout: 90s
- Keep-alive interval: 30s

## Environment Variables

Required for all environments:

```
DEPLOYMENT_ENVIRONMENT=local|render|railway
PORT=3001
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_INTELLIGENCE_SERVICE_SID=your_intelligence_sid
SEGMENT_SPACE_ID=your_segment_space_id
SEGMENT_ACCESS_SECRET=your_segment_token
DEBUG_MODE=false
```

Optional:
```
USE_NGROK=false
NGROK_AUTHTOKEN=your_ngrok_token
CONVERSATIONS_PORT=3002
```

## WebSocket Configuration Details

The application automatically adapts WebSocket settings based on `DEPLOYMENT_ENVIRONMENT`:

| Setting | Local | Railway | Render |
|---------|-------|---------|--------|
| Heartbeat | 60s | 30s | 20s |
| Timeout | 120s | 90s | 45s |
| Keep-alive | 60s | 30s | 15s |
| Compression | No | Yes | Yes |

## Testing Your Deployment

After deployment, test the WebSocket connection:

```bash
# Health check
curl https://your-app-url/health

# Check if server is running
curl https://your-app-url/
```

Expected response:
```json
{
  "status": "healthy",
  "service": "conversation-relay",
  "timestamp": "2025-11-05T15:30:00Z",
  "environment": "railway"
}
```

## Troubleshooting

### TTS Not Working on Render

**Symptom**: Logs show `[BUFF] WebSocket closed - buffering response`

**Cause**: Render's infrastructure closes WebSocket connections during idle periods (e.g., AI processing)

**Solutions**:
1. **Switch to Railway** (recommended) - Better WebSocket support
2. **Use ngrok tunnel** for local development demos
3. **Contact Render support** to increase WebSocket idle timeout

### Connection Dropping

Check logs for:
```
[WARN] Short-lived WebSocket connection (33.3s)
[KEEPALIVE] Ping failed
```

This indicates infrastructure-level timeout. Verify:
- `DEPLOYMENT_ENVIRONMENT` is set correctly
- Your platform supports long-lived WebSocket connections

### Local Works, Production Doesn't

This is typically a WebSocket timeout issue. Railway handles this better than Render.

## Monitoring

Monitor WebSocket health in logs:

```bash
# Railway
railway logs

# Render
# View logs in Render dashboard
```

Look for:
- `[KEEPALIVE] Started keep-alive task`
- `[WS] Connection details: env=railway`
- `[SYS] WebSocket connection closed after XXs` (should be > 60s during active calls)

## Performance Optimization

### Railway (Recommended)
- Enable horizontal scaling for high traffic
- Use Railway's built-in metrics for monitoring
- Estimated cost: $5-20/month for moderate usage

### Render
- Free tier available but has WebSocket limitations
- Paid tier ($7/month) may still have timeout issues
- Better for non-WebSocket workloads

### Local
- Best for development and demos
- No infrastructure costs
- Full control over WebSocket behavior
- Use ngrok for external access

## Next Steps

1. **Development**: Use local environment
2. **Staging/Testing**: Deploy to Railway
3. **Production**: Use Railway with custom domain
4. **Demos**: Use local with ngrok or Railway

## Support

If you encounter deployment issues:
1. Check `DEPLOYMENT_ENVIRONMENT` is set correctly
2. Verify all environment variables are configured
3. Review logs for specific error messages
4. Consider switching from Render to Railway if experiencing WebSocket issues
