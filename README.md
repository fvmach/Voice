
# Cross-Channel AI Agents Platform

A comprehensive platform for managing AI-powered voice conversations and analytics, built with Twilio's APIs and OpenAI integration. Features real-time voice processing, conversation management, and advanced analytics capabilities.

## Platform Overview

This platform consists of multiple integrated components:

### 1. Conversations Manager (Full-Stack Web Application)
- **Frontend**: React application with Twilio Paste design system
- **Backend**: Express.js API server with comprehensive CRUD operations
- **Purpose**: Complete management interface for Twilio Conversations API

### 2. Main Voice Assistant Server (Conversation Relay)
- **Technology**: Python WebSocket server with OpenAI integration
- **Purpose**: Real-time voice conversations with multi-language support

### 3. Signal Processing & Analytics (Voice Intelligence)
- **Technology**: Python server with Twilio Intelligence integration
- **Purpose**: Advanced conversation analytics and AI-powered insights

### 4. Conversational Intelligence Webhook Server
- **Technology**: Flask-based webhook receiver
- **Purpose**: Real-time processing of Twilio Intelligence events

## Key Features

### Conversations Manager (API Management)
- **Multi-Service Support**: Manage multiple Twilio Conversation Services
- **Complete CRUD Operations**: Full lifecycle management for:
  - **Conversations**: Create, read, update, delete with status management
  - **Participants**: Add/remove users with messaging bindings
  - **Messages**: Send, view, delete messages with media attachments
  - **Webhooks**: Configure and manage webhook endpoints
  - **Services**: Manage Conversation Services and configurations
- **Professional UI**: Built with Twilio Paste design system
- **Responsive Design**: Works across desktop and mobile devices
- **Advanced Filtering**: Search and filter across all resources
- **Real-time Data**: Live updates with React Query integration
- **Performance Optimized**: Efficient data fetching and caching

### Voice Assistant (Conversation Relay)
- **Real-time Voice Processing**: WebSocket-based communication
- **Multi-language Support**: Auto-detection (Portuguese, English, Spanish)
- **OpenAI Integration**: GPT-powered conversational AI with streaming
- **Live Dashboard**: Real-time conversation monitoring
- **DTMF Support**: Touch-tone input handling
- **Language Switching**: Dynamic language change during conversations

### Analytics & Intelligence
- **Advanced Analytics**: CSAT, CES, sentiment analysis, legal risk
- **Customer Personalization**: Twilio Segment integration
- **Data Persistence**: NDJSON format with time-based aggregation
- **Webhook Processing**: Real-time intelligence event handling
- **Dashboard Visualization**: Live analytics and insights

## Technology Stack

### Frontend
- React 18+ with Hooks
- Twilio Paste Design System
- React Router for navigation
- React Query for state management
- Date-fns for date formatting

### Backend
- Express.js with CORS support
- Twilio SDK for API integration
- RESTful API design
- Environment-based configuration

### Voice Processing
- Python asyncio for WebSocket handling
- OpenAI API with streaming responses
- Twilio Conversation Relay integration
- Real-time language detection

### Analytics & Intelligence
- Twilio Intelligence API
- Pandas for data processing
- Flask for webhook handling
- NDJSON for data persistence

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- Twilio Account with:
  - Conversations API access
  - Conversation Relay access
  - Intelligence API access (optional)
- OpenAI API key
- ngrok (for webhook development)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Cross-Channel AI Agents"
   ```

2. **Install Dependencies**
   ```bash
   # Conversations Manager
   cd Conversations
   npm install
   cd client
   npm install
   cd ../..
   
   # Python components
   pip install aiohttp aiohttp-cors aiohttp-jinja2 openai python-dotenv twilio colorama jinja2 pandas flask
   ```

3. **Environment Configuration**
   Create `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   SEGMENT_SPACE_ID=your_segment_space_id  # Optional
   SEGMENT_ACCESS_SECRET=your_segment_token  # Optional
   NGROK_DOMAIN=your_ngrok_domain  # Optional
   DEBUG_MODE=false
   ```

### Running the Platform

**Development Mode (4 Terminal Setup):**

```bash
# Terminal 1: Conversations Manager (Full-stack)
cd Conversations && npm run dev
# Frontend: http://localhost:3000, Backend: http://localhost:3001

# Terminal 2: Main Voice Assistant
python server-backup.py
# WebSocket server: localhost:8080, Dashboard: /dashboard

# Terminal 3: Analytics Server (Optional)
cd "Signal SP Session" && python server.py

# Terminal 4: Webhook Server (Optional)
cd "Conversational Intelligence" && python server.py
# Webhook receiver: localhost:4000
```

## User Guides

### Conversations Manager Usage

1. **Access the Interface**: Navigate to `http://localhost:3000`
2. **Service Management**: 
   - Switch between Conversation Services using the dropdown
   - Create new services or manage existing ones
3. **Conversation Management**:
   - View all conversations with filtering and search
   - Create new conversations with custom attributes
   - Click any conversation to access detailed management
4. **Detailed Resource Management**:
   - **Participants**: Add users, configure messaging bindings
   - **Messages**: Send messages, view conversation history
   - **Webhooks**: Configure endpoints for real-time events
   - **Settings**: Edit conversation status and metadata

### Voice Assistant Usage

1. **Start the Server**: `python server-backup.py`
2. **Configure Twilio**: Set up Conversation Relay with WebSocket endpoint
3. **Monitor Dashboard**: Visit `/dashboard` for live conversation monitoring
4. **Language Support**: System automatically detects and switches languages

### Analytics Dashboard

1. **Start Analytics Server**: `python server.py` in Signal SP Session directory
2. **View Intelligence Data**: Check `data/intel_results.ndjson` for processed insights
3. **Monitor Webhooks**: Intelligence events are processed in real-time

## API Documentation

### Conversations Manager API Endpoints

```
# Services
GET    /api/services              # List all services
POST   /api/services              # Create service
GET    /api/services/:sid         # Get service details
PUT    /api/services/:sid         # Update service
DELETE /api/services/:sid         # Delete service

# Conversations
GET    /api/conversations         # List conversations
POST   /api/conversations         # Create conversation
GET    /api/conversations/:sid    # Get conversation
PUT    /api/conversations/:sid    # Update conversation
DELETE /api/conversations/:sid    # Delete conversation

# Participants
GET    /api/conversations/:sid/participants    # List participants
POST   /api/conversations/:sid/participants    # Add participant
DELETE /api/conversations/:sid/participants/:participantSid  # Remove participant

# Messages
GET    /api/conversations/:sid/messages        # List messages
POST   /api/conversations/:sid/messages        # Send message
DELETE /api/conversations/:sid/messages/:messageSid  # Delete message

# Webhooks
GET    /api/conversations/:sid/webhooks        # List webhooks
POST   /api/conversations/:sid/webhooks        # Add webhook
DELETE /api/conversations/:sid/webhooks/:webhookSid  # Delete webhook
```

## Data Management

### Analytics Data
```bash
# View intelligence results
cd "Signal SP Session"
cat data/intel_results.ndjson | jq .  # Pretty print JSON

# Clear webhook data
curl -X POST http://localhost:4000/data/clear
```

### Configuration Classes

**ConversationConfig** (server-backup.py):
- `sentence_end_patterns`: Text completion detection
- `partial_timeout`: Streaming response timing
- `max_buffer_size`: Input buffer limits
- `openai_model`: LLM model selection

## Architecture Details

### Data Flow Architecture
```
Phone Call → Twilio Conversation Relay → WebSocket Handler → OpenAI LLM
                                      ↓
Twilio Intelligence → Webhook Server → Analytics Processing → Dashboard
                                    ↓
                            Data Persistence (NDJSON)
```

### Component Integration
- **Multi-service Support**: All components respect serviceSid parameters
- **Real-time Updates**: WebSocket connections for live data
- **Error Handling**: Comprehensive error states and recovery
- **Data Persistence**: Multiple storage formats for different use cases
- **Customer Context**: Segment integration for personalized experiences

## Development

### Code Patterns
- **Async/Await**: All WebSocket handling is async
- **React Hooks**: Modern React patterns with custom hooks
- **Error Boundaries**: Graceful error handling throughout
- **Type Safety**: PropTypes and careful data validation
- **Performance**: Optimized rendering and API calls

### Testing
- Use ngrok for webhook testing
- Debug mode for verbose logging
- Dashboard monitoring for real-time feedback
- JSON schema validation for webhook payloads

## Supported Events & Operations

### Voice Assistant Events
- `setup`: Initialize conversation
- `prompt`: Process voice input from user
- `interrupt`: Handle conversation interruptions
- `dtmf`: Process touch-tone inputs
- `info`/`debug`: System information events

### Conversation Management Operations
- **Create**: All resources support creation with validation
- **Read**: Comprehensive listing with filtering and pagination
- **Update**: In-place editing with optimistic updates
- **Delete**: Safe deletion with confirmation dialogs

## Security & Best Practices

- **Environment Variables**: All secrets stored in `.env`
- **CORS Configuration**: Proper cross-origin request handling
- **Input Validation**: Server-side validation for all inputs
- **Error Sanitization**: Safe error messages for users
- **Rate Limiting**: Built-in protection against abuse

## Future Enhancements

- **File Upload**: Media attachment management
- **Advanced Analytics**: Custom dashboard views
- **User Management**: Role-based access control
- **API Rate Limiting**: Enhanced performance controls
- **Real-time Collaboration**: Multi-user conversation management
