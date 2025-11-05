const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const serviceRoutes = require('./routes/services');
const conversationRoutes = require('./routes/conversations');
const participantRoutes = require('./routes/participants');
const messageRoutes = require('./routes/messages');
const mediaRoutes = require('./routes/media');
const webhookRoutes = require('./routes/webhooks');

const app = express();
const PORT = process.env.CONVERSATIONS_PORT || 3002;

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // Limit each IP to 1000 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

// Middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://paste.twilio.design"],
      scriptSrc: ["'self'", "'unsafe-eval'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.twilio.com"],
      fontSrc: ["'self'", "https://paste.twilio.design"],
    },
  },
}));
app.use(limiter);
app.use(morgan('combined'));
// CORS configuration
const ALLOWED_ORIGINS = [
  'http://localhost:3000',
  'http://localhost:3001',
  'http://localhost:3002',
  'http://localhost:4000',
  'http://localhost:4001',
  'https://twilio-cross-channel-cx-mas-demo.onrender.com',
  process.env.CLIENT_URL, // Additional client URL from environment
].filter(Boolean);

app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (e.g., mobile apps, curl, Postman)
    if (!origin) return callback(null, true);
    
    // Check if the origin is in our allowed list
    if (ALLOWED_ORIGINS.includes(origin)) {
      return callback(null, true);
    }
    
    // Log and reject unauthorized origins
    console.warn(`CORS blocked origin: ${origin}`);
    return callback(new Error(`Not allowed by CORS: ${origin}`));
  },
  credentials: true
}));
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// API Routes
app.use('/api/services', serviceRoutes);
app.use('/api/conversations', conversationRoutes);
app.use('/api/participants', participantRoutes);
app.use('/api/messages', messageRoutes);
app.use('/api/media', mediaRoutes);
app.use('/api/webhooks', webhookRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Serve static files from React app in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, 'client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'client/build', 'index.html'));
  });
}

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Server Error:', error);
  
  // Twilio API errors
  if (error.status && error.message) {
    return res.status(error.status).json({
      error: 'Twilio API Error',
      message: error.message,
      code: error.code || 'TWILIO_ERROR'
    });
  }
  
  // Generic server errors
  res.status(500).json({
    error: 'Internal Server Error',
    message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Not Found',
    message: `Route ${req.originalUrl} not found`
  });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Twilio Conversations Manager`);
  console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  console.log(`API Base URL: http://localhost:${PORT}/api`);
  console.log(`\nMake sure React client uses: REACT_APP_API_URL=http://localhost:${PORT}/api`);
  
  // Validate Twilio credentials
  if (!process.env.TWILIO_ACCOUNT_SID || !process.env.TWILIO_AUTH_TOKEN) {
    console.warn('Warning: Twilio credentials not found. Please set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN environment variables.');
  }
});
