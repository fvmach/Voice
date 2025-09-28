/**
 * PWA Transcription WebSocket Client
 * Add this to your PWA to receive live transcription events
 */

class TranscriptionClient {
    constructor(serverUrl = 'ws://localhost:8080/pwa-transcripts') {
        this.serverUrl = serverUrl;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnecting = false;
        
        // Event listeners
        this.onTranscriptionStarted = null;
        this.onTranscriptionStopped = null;
        this.onTranscriptReceived = null;
        this.onConnectionStatus = null;
        
        this.connect();
    }
    
    connect() {
        if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
            return;
        }
        
        this.isConnecting = true;
        console.log('[TRANSCRIPT] Connecting to transcription WebSocket...');
        
        try {
            this.ws = new WebSocket(this.serverUrl);
            
            this.ws.onopen = (event) => {
                console.log('[TRANSCRIPT] Connected to transcription stream');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                
                if (this.onConnectionStatus) {
                    this.onConnectionStatus('connected');
                }
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleTranscriptionEvent(data);
                } catch (error) {
                    console.error('[TRANSCRIPT] Error parsing message:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('[TRANSCRIPT] WebSocket disconnected');
                this.isConnecting = false;
                
                if (this.onConnectionStatus) {
                    this.onConnectionStatus('disconnected');
                }
                
                // Attempt reconnection
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`[TRANSCRIPT] Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.connect();
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('[TRANSCRIPT] WebSocket error:', error);
                this.isConnecting = false;
                
                if (this.onConnectionStatus) {
                    this.onConnectionStatus('error');
                }
            };
            
        } catch (error) {
            console.error('[TRANSCRIPT] Failed to create WebSocket:', error);
            this.isConnecting = false;
        }
    }
    
    handleTranscriptionEvent(data) {
        if (data.type !== 'live-transcription') {
            return;
        }
        
        const event = data.data.event;
        
        switch (event) {
            case 'transcription-started':
                console.log('[TRANSCRIPT] Transcription started for call:', data.data.call_sid);
                if (this.onTranscriptionStarted) {
                    this.onTranscriptionStarted(data.data);
                }
                break;
                
            case 'transcription-stopped':
                console.log('[TRANSCRIPT] Transcription stopped for call:', data.data.call_sid);
                if (this.onTranscriptionStopped) {
                    this.onTranscriptionStopped(data.data);
                }
                break;
                
            case 'transcription-content':
                console.log(`[TRANSCRIPT] ${data.data.speaker}: ${data.data.text}`);
                if (this.onTranscriptReceived) {
                    this.onTranscriptReceived(data.data);
                }
                break;
                
            default:
                console.log('[TRANSCRIPT] Unknown event:', event, data.data);
        }
    }
    
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
    
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Usage example for PWA integration:
/*

// Initialize transcription client
const transcriptionClient = new TranscriptionClient();

// Set up event handlers
transcriptionClient.onTranscriptionStarted = (data) => {
    console.log('Call transcription started:', data.call_sid);
    // Show transcription UI
    document.getElementById('transcription-container').style.display = 'block';
};

transcriptionClient.onTranscriptionStopped = (data) => {
    console.log('Call transcription stopped:', data.call_sid);
    // Hide transcription UI
    document.getElementById('transcription-container').style.display = 'none';
};

transcriptionClient.onTranscriptReceived = (data) => {
    // Display transcript in real-time
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
    } else {
        // Partial transcript - replace last partial
        const partialLine = transcriptElement.querySelector('.partial');
        if (partialLine) {
            partialLine.remove();
        }
        transcriptElement.innerHTML += `<div class="transcript-line partial ${data.speaker}">${transcriptHtml}</div>`;
    }
    
    // Auto-scroll to bottom
    transcriptElement.scrollTop = transcriptElement.scrollHeight;
};

transcriptionClient.onConnectionStatus = (status) => {
    const statusIndicator = document.getElementById('transcription-status');
    statusIndicator.textContent = `Transcription: ${status}`;
    statusIndicator.className = `status ${status}`;
};

*/

// Export for use in PWA
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TranscriptionClient;
} else if (typeof window !== 'undefined') {
    window.TranscriptionClient = TranscriptionClient;
}
