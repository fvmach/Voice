# Twilio Function Deployment Instructions

## Function: export-conversation.js

This Twilio Function securely handles conversation exports to Intelligence Service without exposing credentials in your application code.

### 1. Deploy the Function

#### Option A: Using Twilio CLI (Recommended)

1. Install Twilio CLI if you haven't already:
   ```bash
   npm install twilio-cli -g
   ```

2. Login to Twilio CLI:
   ```bash
   twilio login
   ```

3. Deploy the function:
   ```bash
   cd twilio-functions
   twilio serverless:deploy
   ```

#### Option B: Using Twilio Console

1. Go to [Twilio Console > Functions & Assets > Services](https://console.twilio.com/us1/develop/functions/services)
2. Create a new Service (or use existing one)
3. Add a new Function with path `/export-conversation`
4. Copy and paste the contents of `export-conversation.js`
5. Save and Deploy

### 2. Configure Environment Variables

In your Twilio Function Service, add these environment variables:

```
TWILIO_INTELLIGENCE_SERVICE_SID_PT_BR=GA283e1ef3f15a071f01a91a96a4c16621
TWILIO_INTELLIGENCE_SERVICE_SID_EN_US=GA039a07e690ab766f3bce66d52fafa7c9
TWILIO_INTELLIGENCE_SERVICE_SID_ES_US=GAa674e245abdfb597308c4a0d85c6f29f
```

### 3. Update Your Application Environment

Add the function URL to your `.env` file:

```env
# Replace with your actual function domain
TWILIO_FUNCTION_DOMAIN=your-runtime-domain.twil.io

# Or full URL if needed
TWILIO_FUNCTION_URL=https://your-runtime-domain.twil.io/export-conversation
```

### 4. Function Usage

The function accepts these parameters:

- `conversationSid` (required): The conversation SID to export
- `serviceSid` (optional): Service SID, omit for default service  
- `language` (optional): Language code (pt-BR, en-US, es-US), defaults to pt-BR

### 5. Testing

You can test the function using curl:

```bash
curl -X POST https://your-runtime-domain.twil.io/export-conversation \
  -d "conversationSid=CH1234567890abcdef1234567890abcdef" \
  -d "language=pt-BR"
```

### 6. Security Benefits

- ✅ Credentials stay within Twilio infrastructure
- ✅ No need to store Twilio credentials in your application
- ✅ Automatic authentication with Twilio APIs
- ✅ CORS headers included for browser requests
- ✅ Proper error handling and status codes

### 7. Monitoring

Monitor your function execution in:
- Twilio Console > Functions & Assets > Services > [Your Service] > Logs
- Twilio Console > Monitor > Logs > Functions

### Function Response Format

**Success Response:**
```json
{
  "success": true,
  "exportSid": "EX1234567890abcdef1234567890abcdef",
  "conversationSid": "CH1234567890abcdef1234567890abcdef",
  "intelligenceServiceSid": "GA283e1ef3f15a071f01a91a96a4c16621",
  "status": "queued",
  "dateCreated": "2025-01-10T10:00:00.000Z",
  "url": "https://conversations.twilio.com/v1/Conversations/.../Export/..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Export Failed",
  "message": "Conversation not found",
  "code": "20404"
}
```
