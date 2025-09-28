const express = require('express');
const { client } = require('../config/twilio');
const router = express.Router();

// Helper function to get the appropriate conversations resource
const getConversationsResource = (serviceSid) => {
  if (serviceSid && serviceSid !== 'default') {
    return client.conversations.v1.services(serviceSid).conversations;
  }
  return client.conversations.v1.conversations;
};

// GET /api/conversations?serviceSid=xxx - List all conversations (with optional service scope)
router.get('/', async (req, res) => {
  try {
    const { limit = 50, pageToken, serviceSid } = req.query;
    
    const options = {
      limit: parseInt(limit)
    };
    
    if (pageToken) {
      options.pageToken = pageToken;
    }
    
    const conversationsResource = getConversationsResource(serviceSid);
    const conversations = await conversationsResource.list(options);
    
    const response = {
      conversations: conversations.map(conv => ({
        sid: conv.sid,
        uniqueName: conv.uniqueName,
        friendlyName: conv.friendlyName,
        state: conv.state,
        dateCreated: conv.dateCreated,
        dateUpdated: conv.dateUpdated,
        url: conv.url,
        links: conv.links,
        attributes: conv.attributes ? JSON.parse(conv.attributes) : {},
        serviceSid: serviceSid || 'default',
        messagingServiceSid: conv.messagingServiceSid,
        chatServiceSid: conv.chatServiceSid
      })),
      meta: {
        page: req.query.page || 0,
        pageSize: parseInt(limit),
        nextPageToken: conversations.length === parseInt(limit) ? conversations[conversations.length - 1].sid : null,
        serviceSid: serviceSid || 'default'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing conversations:', error);
    res.status(500).json({
      error: 'Failed to list conversations',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/conversations/:sid?serviceSid=xxx - Get a specific conversation
router.get('/:sid', async (req, res) => {
  try {
    const { sid } = req.params;
    const { serviceSid } = req.query;
    
    const conversationsResource = getConversationsResource(serviceSid);
    const conversation = await conversationsResource(sid).fetch();
    
    res.json({
      sid: conversation.sid,
      uniqueName: conversation.uniqueName,
      friendlyName: conversation.friendlyName,
      state: conversation.state,
      dateCreated: conversation.dateCreated,
      dateUpdated: conversation.dateUpdated,
      url: conversation.url,
      links: conversation.links,
      attributes: conversation.attributes ? JSON.parse(conversation.attributes) : {},
      serviceSid: serviceSid || 'default',
      messagingServiceSid: conversation.messagingServiceSid,
      chatServiceSid: conversation.chatServiceSid
    });
  } catch (error) {
    console.error('Error fetching conversation:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Conversation not found',
        message: `Conversation with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch conversation',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/conversations - Create a new conversation
router.post('/', async (req, res) => {
  try {
    const { 
      uniqueName, 
      friendlyName, 
      attributes = {},
      messagingServiceSid,
      state = 'active',
      serviceSid
    } = req.body;
    
    if (!friendlyName && !uniqueName) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Either friendlyName or uniqueName is required'
      });
    }
    
    const conversationData = {
      state
    };
    
    if (uniqueName) conversationData.uniqueName = uniqueName;
    if (friendlyName) conversationData.friendlyName = friendlyName;
    if (messagingServiceSid) conversationData.messagingServiceSid = messagingServiceSid;
    if (Object.keys(attributes).length > 0) {
      conversationData.attributes = JSON.stringify(attributes);
    }
    
    const conversationsResource = getConversationsResource(serviceSid);
    const conversation = await conversationsResource.create(conversationData);
    
    res.status(201).json({
      sid: conversation.sid,
      uniqueName: conversation.uniqueName,
      friendlyName: conversation.friendlyName,
      state: conversation.state,
      dateCreated: conversation.dateCreated,
      dateUpdated: conversation.dateUpdated,
      url: conversation.url,
      links: conversation.links,
      attributes: conversation.attributes ? JSON.parse(conversation.attributes) : {},
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error creating conversation:', error);
    if (error.status === 400) {
      return res.status(400).json({
        error: 'Bad Request',
        message: error.message,
        code: error.code
      });
    }
    res.status(500).json({
      error: 'Failed to create conversation',
      message: error.message,
      code: error.code
    });
  }
});

// PATCH /api/conversations/:sid - Update a conversation
router.patch('/:sid', async (req, res) => {
  try {
    const { sid } = req.params;
    const { 
      uniqueName, 
      friendlyName, 
      attributes,
      state,
      messagingServiceSid,
      serviceSid
    } = req.body;
    
    const updateData = {};
    
    if (uniqueName !== undefined) updateData.uniqueName = uniqueName;
    if (friendlyName !== undefined) updateData.friendlyName = friendlyName;
    if (state !== undefined) updateData.state = state;
    if (messagingServiceSid !== undefined) updateData.messagingServiceSid = messagingServiceSid;
    if (attributes !== undefined) {
      updateData.attributes = JSON.stringify(attributes);
    }
    
    const conversationsResource = getConversationsResource(serviceSid);
    const conversation = await conversationsResource(sid).update(updateData);
    
    res.json({
      sid: conversation.sid,
      uniqueName: conversation.uniqueName,
      friendlyName: conversation.friendlyName,
      state: conversation.state,
      dateCreated: conversation.dateCreated,
      dateUpdated: conversation.dateUpdated,
      url: conversation.url,
      links: conversation.links,
      attributes: conversation.attributes ? JSON.parse(conversation.attributes) : {},
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error updating conversation:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Conversation not found',
        message: `Conversation with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to update conversation',
      message: error.message,
      code: error.code
    });
  }
});

// DELETE /api/conversations/:sid?serviceSid=xxx - Delete a conversation
router.delete('/:sid', async (req, res) => {
  try {
    const { sid } = req.params;
    const { serviceSid } = req.query;
    
    const conversationsResource = getConversationsResource(serviceSid);
    await conversationsResource(sid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting conversation:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Conversation not found',
        message: `Conversation with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete conversation',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/conversations/:sid/export - Export conversation for intelligence processing
router.post('/:sid/export', async (req, res) => {
  try {
    const { sid } = req.params;
    const { serviceSid, language } = req.query;
    
    // Map languages to intelligence service SIDs
    const intelligenceServices = {
      'pt-BR': 'GA283e1ef3f15a071f01a91a96a4c16621',
      'en-US': 'GA039a07e690ab766f3bce66d52fafa7c9',
      'es-US': 'GAa674e245abdfb597308c4a0d85c6f29f'
    };
    
    // Default to pt-BR if no language specified (matches current TwiML configuration)
    const intelligenceServiceSid = intelligenceServices[language] || intelligenceServices['pt-BR'];
    
    console.log(`Exporting conversation for ${language || 'pt-BR'} intelligence service: ${intelligenceServiceSid}`);
    
    if (!intelligenceServiceSid) {
      return res.status(400).json({
        error: 'Configuration Error',
        message: 'Intelligence Service SID not found for the specified language'
      });
    }
    
    const conversationsResource = getConversationsResource(serviceSid);
    
    // Use the export endpoint for text conversations
    const exportData = {
      IntelligenceServiceSid: intelligenceServiceSid
    };
    
    // Call Twilio Function for secure export
    const functionUrl = process.env.TWILIO_FUNCTION_URL || `https://${process.env.TWILIO_FUNCTION_DOMAIN || 'conversations-intelligence-functions-6235-dev.twil.io'}/export-conversation`;
    
    const https = require('https');
    const querystring = require('querystring');
    
    // Prepare the function parameters
    const functionData = querystring.stringify({
      conversationSid: sid,
      serviceSid: serviceSid || '',
      language: language || 'pt-BR'
    });
    
    // Call the Twilio Function
    const exportResult = await new Promise((resolve, reject) => {
      const url = require('url');
      const parsedUrl = url.parse(functionUrl);
      
      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || 443,
        path: parsedUrl.path,
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(functionData)
        }
      };
      
      const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const result = JSON.parse(data);
            if (res.statusCode >= 200 && res.statusCode < 300 && result.success) {
              resolve(result);
            } else {
              console.error(`Function error ${res.statusCode}:`, result);
              reject(new Error(result.message || `Function error: ${res.statusCode}`));
            }
          } catch (parseError) {
            console.error('Failed to parse function response:', parseError);
            reject(parseError);
          }
        });
      });
      
      req.on('error', (error) => {
        console.error('Request to Twilio Function failed:', error);
        reject(error);
      });
      
      req.setTimeout(30000, () => {
        req.destroy();
        reject(new Error('Request to Twilio Function timed out'));
      });
      
      req.write(functionData);
      req.end();
    });
    
    res.json({
      exportSid: exportResult.exportSid || exportResult.sid,
      conversationSid: sid,
      intelligenceServiceSid: intelligenceServiceSid,
      status: exportResult.status || 'completed',
      dateCreated: exportResult.dateCreated,
      url: exportResult.url,
      messageCount: exportResult.messageCount
    });
  } catch (error) {
    console.error('Error exporting conversation for intelligence:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Conversation not found',
        message: `Conversation with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to export conversation',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/conversations/:sid/intelligence - Get intelligence data for conversation
router.get('/:sid/intelligence', async (req, res) => {
  try {
    const { sid } = req.params;
    const { serviceSid, language } = req.query;
    
    console.log(`Fetching intelligence data for conversation ${sid}, language: ${language || 'pt-BR'}`);
    
    // Get the Signal SP Session server URL from environment
    const signalSpUrl = process.env.NGROK_DOMAIN 
      ? `https://${process.env.NGROK_DOMAIN}` 
      : 'http://localhost:8080';
    
    // Proxy request to Signal SP Session server
    const https = require('https');
    const http = require('http');
    const url = require('url');
    
    const signalSpEndpoint = `${signalSpUrl}/conversation/${sid}/intelligence`;
    console.log(`Proxying request to Signal SP Session server: ${signalSpEndpoint}`);
    
    const requestPromise = new Promise((resolve, reject) => {
      const parsedUrl = url.parse(signalSpEndpoint);
      const requestModule = parsedUrl.protocol === 'https:' ? https : http;
      
      const options = {
        hostname: parsedUrl.hostname,
        port: parsedUrl.port || (parsedUrl.protocol === 'https:' ? 443 : 80),
        path: parsedUrl.path,
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'Twilio-Conversations-Manager/1.0'
        }
      };
      
      const req = requestModule.request(options, (response) => {
        let data = '';
        
        response.on('data', (chunk) => {
          data += chunk;
        });
        
        response.on('end', () => {
          try {
            if (response.statusCode === 200) {
              const jsonData = JSON.parse(data);
              resolve(jsonData);
            } else {
              console.error(`Signal SP Session server returned status ${response.statusCode}: ${data}`);
              reject(new Error(`Signal SP server error: ${response.statusCode} - ${data}`));
            }
          } catch (parseError) {
            console.error('Failed to parse response from Signal SP Session server:', parseError);
            reject(parseError);
          }
        });
      });
      
      req.on('error', (error) => {
        console.error('Request to Signal SP Session server failed:', error);
        reject(error);
      });
      
      req.setTimeout(10000, () => {
        req.destroy();
        reject(new Error('Request to Signal SP Session server timed out'));
      });
      
      req.end();
    });
    
    const intelligenceData = await requestPromise;
    
    // Return the data from Signal SP Session server
    res.json(intelligenceData);
    
  } catch (error) {
    console.error('Error fetching intelligence data:', error);
    
    // Check if it's a connection error to Signal SP server
    if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
      return res.status(503).json({
        error: 'Signal Processing Server Unavailable',
        message: 'Could not connect to the Signal SP Session server. Please ensure the server is running.',
        details: error.message
      });
    }
    
    res.status(500).json({
      error: 'Failed to fetch intelligence data',
      message: error.message,
      details: 'Error occurred while proxying request to Signal SP Session server'
    });
  }
});

// GET /api/conversations/:sid/transcription - Get live transcription data for voice conversations
router.get('/:sid/transcription', async (req, res) => {
  try {
    const { sid } = req.params;
    const { serviceSid } = req.query;
    
    // For live transcription, connect to Signal SP Session server for real data
    const transcriptionData = {
      conversationSid: sid,
      isLive: true,
      transcriptions: [],
      websocketUrl: 'wss://owlbank.ngrok.io/websocket', // Signal SP Session server WebSocket
      signalSpUrl: 'https://owlbank.ngrok.io', // Signal SP Session server HTTP API
      status: 'available'
    };
    
    res.json(transcriptionData);
  } catch (error) {
    console.error('Error fetching transcription data:', error);
    res.status(500).json({
      error: 'Failed to fetch transcription data',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
