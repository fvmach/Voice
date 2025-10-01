# Render Deployment Guide

## 🚀 Deployment Options

### Option 1: Lightweight Core Deployment (Recommended)
**File:** `render-lightweight.yaml`
**Startup:** `python start_unified_server.py`

**What it includes:**
- ✅ Main Conversation Relay Server (Python)
- ✅ Conversations API Manager (Node.js)
- ❌ Signal Analytics (requires pandas)
- ❌ Intelligence Webhook Server (optional)

**Benefits:**
- Fast build times (~3-5 minutes)
- Reliable deployment
- Lower resource usage
- Core functionality works perfectly

### Option 2: Complete Deployment
**File:** `render-complete.yaml`
**Startup:** `python start_complete_server.py`

**What it includes:**
- ✅ All servers
- ✅ Full analytics with pandas
- ✅ Intelligence webhooks
- ✅ Smart dependency detection

**Considerations:**
- Longer build times (~10-15 minutes)
- Requires pandas compatibility with Python version
- Higher resource usage

## 🔧 Quick Fix Applied

### Problem Solved:
The original deployment was failing because:
1. **pandas 2.1.4** is incompatible with **Python 3.13.4**
2. Build was taking too long and failing on pandas compilation

### Solutions Implemented:

1. **Added `.python-version`** to force Python 3.11.9 (compatible with all dependencies)

2. **Updated `requirements.txt`** with compatible versions:
   - pandas: 2.1.4 → 2.2.0
   - openai: 1.3.0 → 1.12.0
   - twilio: 8.10.0 → 9.0.4
   - flask: 3.0.0 → 3.0.2

3. **Created `requirements-render.txt`** (lightweight version without pandas)

4. **Smart server detection** - automatically skips analytics if pandas not available

## 🎯 Recommended Deployment Steps

### For Render:

1. **Use the lightweight config** (fastest, most reliable):
   ```yaml
   # Use deployment/render/render-lightweight.yaml
   startCommand: python start_unified_server.py
   ```

2. **Or use complete config** (if you need analytics):
   ```yaml
   # Use deployment/render/render-complete.yaml  
   startCommand: python start_complete_server.py
   ```

### Environment Variables Required:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
OPENAI_API_KEY=your_openai_key
```

### Optional Environment Variables:
```
TWILIO_INTELLIGENCE_SERVICE_SID=your_intelligence_sid
SEGMENT_SPACE_ID=your_segment_space
SEGMENT_ACCESS_SECRET=your_segment_secret
DEBUG_MODE=false
```

## 🔍 Local Testing

Test the startup scripts locally:

```bash
# Test lightweight version (core servers only)
python start_unified_server.py

# Test complete version (all servers)
python start_complete_server.py

# Test bash version (simple alternative)
./start_render_unified.sh
```

## 📊 Server Architecture

### Core Servers (Always Running):
- **Conversation Relay** (Python, port: Render PORT)
  - Main WebSocket server for voice conversations
  - AI-powered conversation handling
  - Dashboard at `/dashboard`

- **Conversations API** (Node.js, port: Render PORT + 1)
  - Twilio Conversations API management
  - React frontend for conversation management
  - CRUD operations for conversations

### Optional Servers:
- **Signal Analytics** (Python, port: Render PORT + 3)
  - Voice analytics with AI insights
  - Requires pandas for data processing
  - Intelligence dashboard

- **Intelligence Webhook** (Python, port: Render PORT + 2)
  - Webhook receiver for Twilio Intelligence
  - Event processing and storage

## 🎉 Expected Results

After successful deployment:
- ✅ Main endpoint responds at your Render URL
- ✅ Dashboard available at `/dashboard`
- ✅ WebSocket connections working
- ✅ Conversations API accessible
- ✅ All environment variables configured
- ✅ Build completes in under 10 minutes

The lightweight deployment should work reliably and give you the core functionality needed for your Cross-Channel AI Agents platform!