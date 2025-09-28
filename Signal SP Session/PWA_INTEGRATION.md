# PWA Integration for Real-Time Transcription

This guide explains how to integrate live transcription streaming into your PWA located at `/Users/fvieiramachado/Twilio/Owl Bank PWA App v2/src/index.html`.

## Overview

The transcription system now works asynchronously:
1. **Voice calls** continue through Conversation Relay (no blocking)
2. **Transcription webhook** processes events asynchronously 
3. **PWA WebSocket** receives live transcripts for display
4. **No latency impact** on conversation flow

## Integration Steps

### 1. Add Transcription Client to PWA

Copy the `pwa_transcription.js` file to your PWA directory and include it:

```html
<!-- Add to index.html head section -->
<script src="pwa_transcription.js"></script>
```

### 2. Add Transcription UI Elements

Add these elements to your `index.html` where you want transcriptions to appear:

```html
<!-- Add inside your chat container or create a new section -->
<div id="transcription-container" class="transcription-panel" style="display: none;">
    <div class="transcription-header">
        <h3>Live Transcription</h3>
        <span id="transcription-status" class="status disconnected">Connecting...</span>
    </div>
    <div id="live-transcript" class="transcript-content"></div>
</div>
```

### 3. Add Transcription CSS

Add these styles to your `styles.css`:

```css
/* Transcription Panel Styles */
.transcription-panel {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    margin: 10px 0;
    max-height: 300px;
    overflow-y: auto;
}

.transcription-header {
    padding: 10px;
    background: #e9ecef;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.transcription-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
}

.status {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
}

.status.connected {
    background: #d4edda;
    color: #155724;
}

.status.disconnected {
    background: #f8d7da;
    color: #721c24;
}

.status.error {
    background: #fcf8e3;
    color: #856404;
}

.transcript-content {
    padding: 10px;
    font-family: monospace;
    font-size: 13px;
    line-height: 1.4;
    max-height: 200px;
    overflow-y: auto;
}

.transcript-line {
    margin-bottom: 5px;
    padding: 4px 0;
}

.transcript-line.customer {
    color: #0056b3;
}

.transcript-line.agent {
    color: #28a745;
}

.transcript-line.partial {
    opacity: 0.7;
    font-style: italic;
}

.transcript-line .speaker {
    font-weight: bold;
    margin-right: 8px;
}

.transcript-line .confidence {
    font-size: 11px;
    color: #6c757d;
    margin-left: 8px;
}
```

### 4. Initialize Transcription Client

Add this JavaScript code to your `app.js` or create a new script section:

```javascript
// Initialize transcription client when PWA loads
let transcriptionClient;

function initTranscriptionClient() {
    // Update URL if your server runs on different host/port
    transcriptionClient = new TranscriptionClient('ws://localhost:8080/pwa-transcripts');
    
    // Handle transcription started
    transcriptionClient.onTranscriptionStarted = (data) => {
        console.log('Call transcription started:', data.call_sid);
        document.getElementById('transcription-container').style.display = 'block';
        document.getElementById('live-transcript').innerHTML = '';
    };
    
    // Handle transcription stopped  
    transcriptionClient.onTranscriptionStopped = (data) => {
        console.log('Call transcription stopped:', data.call_sid);
        // Keep transcription visible but stop updates
        const status = document.getElementById('transcription-status');
        status.textContent = 'Transcription: ended';
        status.className = 'status disconnected';
    };
    
    // Handle live transcript updates
    transcriptionClient.onTranscriptReceived = (data) => {
        displayTranscript(data);
    };
    
    // Handle connection status
    transcriptionClient.onConnectionStatus = (status) => {
        const statusElement = document.getElementById('transcription-status');
        statusElement.textContent = `Transcription: ${status}`;
        statusElement.className = `status ${status}`;
    };
}

function displayTranscript(data) {
    const transcriptElement = document.getElementById('live-transcript');
    
    const speaker = data.speaker === 'customer' ? 'You' : 'Agent';
    const confidence = Math.round(data.confidence * 100);
    
    const transcriptHtml = `
        <div class="transcript-line ${data.speaker}">
            <span class="speaker">${speaker}:</span>
            <span class="text">${data.text}</span>
            <span class="confidence">(${confidence}%)</span>
        </div>
    `;
    
    if (data.is_final) {
        // Final transcript - add permanently
        transcriptElement.innerHTML += transcriptHtml;
        
        // Remove any partial lines for this speaker
        const partialLines = transcriptElement.querySelectorAll('.partial');
        partialLines.forEach(line => line.remove());
    } else {
        // Partial transcript - replace previous partial for this speaker
        const existingPartial = transcriptElement.querySelector(`.partial.${data.speaker}`);
        if (existingPartial) {
            existingPartial.remove();
        }
        
        const partialElement = document.createElement('div');
        partialElement.className = `transcript-line partial ${data.speaker}`;
        partialElement.innerHTML = `
            <span class="speaker">${speaker}:</span>
            <span class="text">${data.text}</span>
            <span class="confidence">(${confidence}%)</span>
        `;
        transcriptElement.appendChild(partialElement);
    }
    
    // Auto-scroll to bottom
    transcriptElement.scrollTop = transcriptElement.scrollHeight;
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initTranscriptionClient);
```

### 5. Integrate with Voice Call Button

Modify your existing voice call functionality to show transcription when calls start:

```javascript
// In your existing toggleCall() function or voice call handler
function toggleCall() {
    // Your existing voice call logic...
    
    // Show transcription panel when call starts
    if (isCallActive) {
        document.getElementById('transcription-container').style.display = 'block';
    } else {
        // Optionally hide when call ends
        // document.getElementById('transcription-container').style.display = 'none';
    }
}
```

## Server Configuration

Make sure your transcription server is running:

```bash
cd "/Users/fvieiramachado/Twilio/CX MAS/Cross-Channel AI Agents/Signal SP Session"
python3 server.py
```

The server will show:
```
[SYS] PWA transcription WebSocket: ws://localhost:8080/pwa-transcripts
```

## Testing

1. **Start the server** - You should see the PWA WebSocket endpoint in logs
2. **Open your PWA** - Check browser console for transcription connection
3. **Make a voice call** - Transcription should appear in real-time
4. **Monitor logs** - Server shows PWA connections and transcript events

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Verify server is running on correct port
   - Check for CORS issues in browser console
   - Ensure WebSocket URL matches server host/port

2. **No transcripts appearing**
   - Verify Twilio phone number webhook points to `/voice` endpoint
   - Check server logs for transcription webhook events
   - Ensure TwiML includes transcription configuration

3. **Transcripts delayed**
   - This is now fixed - transcription processing is async
   - No impact on conversation relay latency

### Debug Mode

Enable detailed logging:
```bash
export DEBUG_MODE=true
python3 server.py
```

This will show detailed transcription processing logs.

## Architecture

```
Voice Call → Twilio → TwiML (/voice) → Conversation Relay (no blocking)
                                   ↓
Real-Time Transcription → Webhook (/transcripts) → Async Processing
                                                        ↓
                                                PWA WebSocket Stream
```

The key improvement is that transcription processing happens asynchronously and doesn't block the main conversation flow, eliminating the latency issues you experienced.
