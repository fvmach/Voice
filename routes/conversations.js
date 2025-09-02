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

module.exports = router;
