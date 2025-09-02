const express = require('express');
const { client } = require('../config/twilio');
const router = express.Router();

// Helper function to get the appropriate messages resource
const getMessagesResource = (conversationSid, serviceSid) => {
  if (serviceSid && serviceSid !== 'default') {
    return client.conversations.v1.services(serviceSid).conversations(conversationSid).messages;
  }
  return client.conversations.v1.conversations(conversationSid).messages;
};

// GET /api/messages/:conversationSid?serviceSid=xxx - List messages in a conversation
router.get('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { limit = 50, pageToken, order = 'desc', serviceSid } = req.query;
    
    const options = {
      limit: parseInt(limit),
      order: order
    };
    
    if (pageToken) {
      options.pageToken = pageToken;
    }
    
    const messagesResource = getMessagesResource(conversationSid, serviceSid);
    const messages = await messagesResource.list(options);
    
    const response = {
      messages: messages.map(message => ({
        sid: message.sid,
        conversationSid: message.conversationSid,
        participantSid: message.participantSid,
        author: message.author,
        body: message.body,
        media: message.media,
        attributes: message.attributes ? JSON.parse(message.attributes) : {},
        index: message.index,
        dateCreated: message.dateCreated,
        dateUpdated: message.dateUpdated,
        delivery: message.delivery,
        url: message.url,
        links: message.links,
        serviceSid: serviceSid || 'default'
      })),
      meta: {
        page: req.query.page || 0,
        pageSize: parseInt(limit),
        nextPageToken: messages.length === parseInt(limit) ? messages[messages.length - 1].sid : null,
        conversationSid,
        serviceSid: serviceSid || 'default'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing messages:', error);
    res.status(500).json({
      error: 'Failed to list messages',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/messages/:conversationSid/:messageSid?serviceSid=xxx - Get a specific message
router.get('/:conversationSid/:messageSid', async (req, res) => {
  try {
    const { conversationSid, messageSid } = req.params;
    const { serviceSid } = req.query;
    
    const messagesResource = getMessagesResource(conversationSid, serviceSid);
    const message = await messagesResource(messageSid).fetch();
    
    res.json({
      sid: message.sid,
      conversationSid: message.conversationSid,
      participantSid: message.participantSid,
      author: message.author,
      body: message.body,
      media: message.media,
      attributes: message.attributes ? JSON.parse(message.attributes) : {},
      index: message.index,
      dateCreated: message.dateCreated,
      dateUpdated: message.dateUpdated,
      delivery: message.delivery,
      url: message.url,
      links: message.links,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error fetching message:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Message not found',
        message: `Message with SID ${req.params.messageSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch message',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/messages/:conversationSid - Send a message to a conversation
router.post('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { 
      body,
      author,
      mediaSid,
      attributes = {},
      serviceSid
    } = req.body;
    
    if (!body && !mediaSid) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Either body or mediaSid is required'
      });
    }
    
    const messageData = {};
    
    if (body) messageData.body = body;
    if (author) messageData.author = author;
    if (mediaSid) messageData.mediaSid = mediaSid;
    if (Object.keys(attributes).length > 0) {
      messageData.attributes = JSON.stringify(attributes);
    }
    
    const messagesResource = getMessagesResource(conversationSid, serviceSid);
    const message = await messagesResource.create(messageData);
    
    res.status(201).json({
      sid: message.sid,
      conversationSid: message.conversationSid,
      participantSid: message.participantSid,
      author: message.author,
      body: message.body,
      media: message.media,
      attributes: message.attributes ? JSON.parse(message.attributes) : {},
      index: message.index,
      dateCreated: message.dateCreated,
      dateUpdated: message.dateUpdated,
      delivery: message.delivery,
      url: message.url,
      links: message.links,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error creating message:', error);
    if (error.status === 400) {
      return res.status(400).json({
        error: 'Bad Request',
        message: error.message,
        code: error.code
      });
    }
    res.status(500).json({
      error: 'Failed to create message',
      message: error.message,
      code: error.code
    });
  }
});

// PATCH /api/messages/:conversationSid/:messageSid - Update a message
router.patch('/:conversationSid/:messageSid', async (req, res) => {
  try {
    const { conversationSid, messageSid } = req.params;
    const { 
      body,
      author,
      attributes,
      serviceSid
    } = req.body;
    
    const updateData = {};
    
    if (body !== undefined) updateData.body = body;
    if (author !== undefined) updateData.author = author;
    if (attributes !== undefined) {
      updateData.attributes = JSON.stringify(attributes);
    }
    
    const messagesResource = getMessagesResource(conversationSid, serviceSid);
    const message = await messagesResource(messageSid).update(updateData);
    
    res.json({
      sid: message.sid,
      conversationSid: message.conversationSid,
      participantSid: message.participantSid,
      author: message.author,
      body: message.body,
      media: message.media,
      attributes: message.attributes ? JSON.parse(message.attributes) : {},
      index: message.index,
      dateCreated: message.dateCreated,
      dateUpdated: message.dateUpdated,
      delivery: message.delivery,
      url: message.url,
      links: message.links,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error updating message:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Message not found',
        message: `Message with SID ${req.params.messageSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to update message',
      message: error.message,
      code: error.code
    });
  }
});

// DELETE /api/messages/:conversationSid/:messageSid?serviceSid=xxx - Delete a message
router.delete('/:conversationSid/:messageSid', async (req, res) => {
  try {
    const { conversationSid, messageSid } = req.params;
    const { serviceSid } = req.query;
    
    const messagesResource = getMessagesResource(conversationSid, serviceSid);
    await messagesResource(messageSid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting message:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Message not found',
        message: `Message with SID ${req.params.messageSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete message',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
