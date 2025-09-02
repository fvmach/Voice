# Twilio Conversations Manager

A full-stack web application for managing Twilio Conversations API resources with complete CRUD operations. Built with Express.js backend and React frontend using Twilio Paste design system.

## Features

### Backend API (Express.js)
- **Services Management**: Create, list, and delete Conversation Services
- **Conversations Management**: Full CRUD operations for conversations with multi-service support
- **Participants Management**: Add, remove, list, and update conversation participants
- **Messages Management**: Send, list, update, and delete messages in conversations
- **Media Management**: Upload, list, and manage media attachments
- **Webhooks Management**: Create and manage conversation-scoped webhooks
- **Multi-Service Architecture**: Support for multiple Twilio Conversation Services
- **Error Handling**: Comprehensive error handling and validation
- **Security**: Rate limiting, CORS, and security headers
- **File Upload**: Media file upload with validation

### Frontend UI (React + Twilio Paste)
- **Modern Design**: Built with Twilio Paste design system
- **Responsive Layout**: Works on desktop and mobile devices
- **Real-time Updates**: React Query for data fetching and caching
- **Service Management**: Create and manage multiple Conversation Services
- **Comprehensive CRUD**: Full interface for all Conversations API resources
- **Error Handling**: User-friendly error messages and validation
- **Loading States**: Proper loading indicators and states

## Architecture

### Multi-Service Support
The application supports Twilio's multi-service architecture, allowing you to:
- Create multiple Conversation Services (dev, staging, prod)
- Scope all operations to specific services
- Switch between services in the UI
- Isolate resources by environment

### API Endpoints

```
Services:
GET    /api/services                    - List all services
POST   /api/services                    - Create a new service
GET    /api/services/:sid               - Get specific service
DELETE /api/services/:sid               - Delete a service

Conversations:
GET    /api/conversations?serviceSid=xxx - List conversations
POST   /api/conversations               - Create conversation
GET    /api/conversations/:sid          - Get conversation
PATCH  /api/conversations/:sid          - Update conversation
DELETE /api/conversations/:sid          - Delete conversation

Participants:
GET    /api/participants/:conversationSid    - List participants
POST   /api/participants/:conversationSid    - Add participant
GET    /api/participants/:conversationSid/:participantSid - Get participant
PATCH  /api/participants/:conversationSid/:participantSid - Update participant
DELETE /api/participants/:conversationSid/:participantSid - Remove participant

Messages:
GET    /api/messages/:conversationSid        - List messages
POST   /api/messages/:conversationSid        - Send message
GET    /api/messages/:conversationSid/:messageSid - Get message
PATCH  /api/messages/:conversationSid/:messageSid - Update message
DELETE /api/messages/:conversationSid/:messageSid - Delete message

Media:
GET    /api/media/:conversationSid/:messageSid - List media
POST   /api/media/upload                     - Upload media file
GET    /api/media/:conversationSid/:messageSid/:mediaSid - Get media
DELETE /api/media/:conversationSid/:messageSid/:mediaSid - Delete media

Webhooks:
GET    /api/webhooks/:conversationSid        - List webhooks
POST   /api/webhooks/:conversationSid        - Create webhook
GET    /api/webhooks/:conversationSid/:webhookSid - Get webhook
PATCH  /api/webhooks/:conversationSid/:webhookSid - Update webhook
DELETE /api/webhooks/:conversationSid/:webhookSid - Delete webhook
```

All endpoints support the `serviceSid` query parameter for multi-service operations.

## Setup and Installation

### Prerequisites
- Node.js 18+ and npm
- Twilio Account with Conversations API access
- Twilio Account SID and Auth Token

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd twilio-conversations-manager
   ```

2. **Install dependencies**
   ```bash
   # Install backend dependencies
   npm install
   
   # Install frontend dependencies
   cd client
   npm install
   cd ..
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your Twilio credentials:
   ```env
   TWILIO_ACCOUNT_SID=your_account_sid_here
   TWILIO_AUTH_TOKEN=your_auth_token_here
   PORT=3001
   NODE_ENV=development
   CLIENT_URL=http://localhost:3000
   ```

4. **Start Development Servers**
   
   **Terminal 1 - Backend:**
   ```bash
   npm run dev
   ```
   
   **Terminal 2 - Frontend:**
   ```bash
   cd client
   npm start
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:3001/api
   - Health Check: http://localhost:3001/api/health

### Production Deployment (Render)

1. **Prepare for Render**
   - Ensure `package.json` has the correct build scripts
   - The app is configured to serve the React build in production

2. **Deploy to Render**
   - Create a new Web Service on Render
   - Connect your GitHub repository
   - Set the build command: `npm install && npm run build`
   - Set the start command: `npm start`

3. **Environment Variables on Render**
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   NODE_ENV=production
   CLIENT_URL=https://your-app-name.onrender.com
   ```

## Usage

### Services Management
1. Navigate to the Services page
2. Create a new Conversation Service or use the default
3. Each service provides isolated environments for your conversations

### Conversations Management
1. Select a service (or use default)
2. Create conversations with friendly names and attributes
3. Manage conversation state and settings
4. View conversation details and associated resources

### Participants Management
- Add participants by identity or phone number
- Manage participant roles and attributes
- Remove participants from conversations

### Messages Management
- Send text messages to conversations
- Upload and attach media files
- View message history and delivery status
- Update message attributes

### Webhooks Management
- Configure conversation-scoped webhooks
- Set webhook URLs and event filters
- Manage webhook targets (webhook, studio, trigger)

## API Usage Examples

### Create a Service
```bash
curl -X POST http://localhost:3001/api/services \\
  -H "Content-Type: application/json" \\
  -d '{"friendlyName": "My Development Service"}'
```

### Create a Conversation
```bash
curl -X POST http://localhost:3001/api/conversations \\
  -H "Content-Type: application/json" \\
  -d '{
    "friendlyName": "Customer Support Chat",
    "serviceSid": "ISXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "attributes": {"department": "support"}
  }'
```

### Add a Participant
```bash
curl -X POST http://localhost:3001/api/participants/CHXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \\
  -H "Content-Type: application/json" \\
  -d '{
    "identity": "customer123",
    "serviceSid": "ISXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  }'
```

### Send a Message
```bash
curl -X POST http://localhost:3001/api/messages/CHXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX \\
  -H "Content-Type: application/json" \\
  -d '{
    "body": "Hello! How can I help you today?",
    "author": "agent",
    "serviceSid": "ISXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
  }'
```

## Development

### Project Structure
```
├── server.js              # Express server
├── config/
│   └── twilio.js          # Twilio client configuration
├── routes/                # API route handlers
│   ├── services.js
│   ├── conversations.js
│   ├── participants.js
│   ├── messages.js
│   ├── media.js
│   └── webhooks.js
├── client/                # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API service functions
│   │   └── utils/         # Utility functions
│   └── public/
└── package.json
```

### Technologies Used

**Backend:**
- Express.js - Web framework
- Twilio SDK - Twilio API integration
- Multer - File upload handling
- Helmet - Security headers
- CORS - Cross-origin resource sharing
- Morgan - HTTP request logging

**Frontend:**
- React - UI framework
- Twilio Paste - Design system
- React Router - Client-side routing
- React Query - Data fetching and caching
- Axios - HTTP client
- React Hook Form - Form handling

## Error Handling

The application includes comprehensive error handling:

- **API Validation**: Input validation on all endpoints
- **Twilio Errors**: Proper handling of Twilio API errors
- **User Feedback**: Clear error messages in the UI
- **Network Errors**: Graceful handling of network issues
- **Rate Limiting**: Protection against abuse

## Security Features

- **Rate Limiting**: 1000 requests per 15 minutes per IP
- **CORS**: Configurable cross-origin settings
- **Helmet**: Security headers including CSP
- **Input Validation**: Server-side validation on all inputs
- **File Upload Security**: File type and size restrictions

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the Twilio Conversations API documentation
- Create an issue in this repository
- Contact Twilio support for API-related questions
