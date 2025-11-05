# Railway Deployment - Quick Reference

## Your App
**URL**: https://ai-agents-production-cf4f.up.railway.app

## Quick Commands

### Deploy to Railway
```bash
railway up
```

### View Logs
```bash
railway logs
```

### Set Environment Variables
```bash
railway variables set DEPLOYMENT_ENVIRONMENT=railway
railway variables set OPENAI_API_KEY=your_key
railway variables set TWILIO_ACCOUNT_SID=your_sid
railway variables set TWILIO_AUTH_TOKEN=your_token
railway variables set TWILIO_INTELLIGENCE_SERVICE_SID=your_intel_sid
railway variables set SEGMENT_SPACE_ID=your_segment_space
railway variables set SEGMENT_ACCESS_SECRET=your_segment_secret
railway variables set OPENAI_MODEL=gpt-4o-mini
railway variables set DEBUG_MODE=false
```

### Link to Project
```bash
railway link
```

### Open in Browser
```bash
railway open
```

## Endpoints

- **Health Check**: https://ai-agents-production-cf4f.up.railway.app/health
- **Root**: https://ai-agents-production-cf4f.up.railway.app/
- **WebSocket**: wss://ai-agents-production-cf4f.up.railway.app/websocket
- **Dashboard**: https://ai-agents-production-cf4f.up.railway.app/dashboard
- **Conversations Manager**: https://ai-agents-production-cf4f.up.railway.app/conversations/

## WebSocket Configuration (Railway)

Railway automatically uses these settings when `DEPLOYMENT_ENVIRONMENT=railway`:
- **Heartbeat**: 30 seconds
- **Timeout**: 90 seconds
- **Keep-alive interval**: 30 seconds
- **Compression**: Enabled

## Testing Your Deployment

### 1. Test Health Endpoint
```bash
curl https://ai-agents-production-cf4f.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "conversation-relay",
  "timestamp": "2025-11-05T15:35:00Z",
  "environment": "railway"
}
```

### 2. Test Root Endpoint
```bash
curl https://ai-agents-production-cf4f.up.railway.app/
```

Expected: `Twilio WebSocket/HTTP Server Running`

### 3. Configure Twilio Conversation Relay

Point your Twilio Conversation Relay to:
```
wss://ai-agents-production-cf4f.up.railway.app/websocket
```

## Monitoring

### View Real-time Logs
```bash
railway logs -f
```

### Check WebSocket Health
Look for these log messages:
- `[KEEPALIVE] Started keep-alive task (interval=30s, env=railway)`
- `[WS] Connection details: env=railway, heartbeat=30s, compress=True, timeout=90s`
- `[SYS] WebSocket connection closed after XXs` (should be > 60s during active calls)

## Troubleshooting

### TTS Not Working
1. Check logs: `railway logs -f`
2. Look for: `[BUFF] WebSocket closed - buffering response`
3. Verify `DEPLOYMENT_ENVIRONMENT=railway` is set correctly
4. Check that WebSocket connection stays alive > 30 seconds

### Environment Variable Not Set
```bash
# List all variables
railway variables

# Set missing variable
railway variables set VARIABLE_NAME=value
```

### Redeploy After Changes
```bash
# Push code changes
git push

# Or force redeploy
railway up --detach
```

## Cost Estimate

Railway pricing:
- **Free tier**: $5 credit/month
- **Hobby plan**: $5-20/month for moderate usage
- **Pro plan**: Pay-as-you-go

Your app will likely cost $5-15/month depending on usage.

## Comparison: Local vs Railway

| Feature | Local | Railway |
|---------|-------|---------|
| WebSocket Support | Excellent | Excellent |
| Setup Time | 5 minutes | 10 minutes |
| Cost | Free | $5-20/month |
| Accessibility | ngrok required | Public URL |
| Uptime | Manual | 99.9% SLA |
| Best For | Development, Demos | Production |

## Next Steps

1. ✅ Verify health endpoint works
2. ✅ Check logs for successful startup
3. ✅ Configure Twilio Conversation Relay with Railway WebSocket URL
4. ✅ Test voice call with TTS
5. ⬜ Add custom domain (optional)
6. ⬜ Enable metrics/monitoring

## Support

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Check Railway dashboard for deployment logs
