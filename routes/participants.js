const express = require('express');
const { client } = require('../config/twilio');
const router = express.Router();

// Helper function to get the appropriate participants resource
const getParticipantsResource = (conversationSid, serviceSid) => {
  if (serviceSid && serviceSid !== 'default') {
    return client.conversations.v1.services(serviceSid).conversations(conversationSid).participants;
  }
  return client.conversations.v1.conversations(conversationSid).participants;
};

// GET /api/participants/:conversationSid?serviceSid=xxx - List participants in a conversation
router.get('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { limit = 50, pageToken, serviceSid } = req.query;
    
    const options = {
      limit: parseInt(limit)
    };
    
    if (pageToken) {
      options.pageToken = pageToken;
    }
    
    const participantsResource = getParticipantsResource(conversationSid, serviceSid);
    const participants = await participantsResource.list(options);
    
    const response = {
      participants: participants.map(participant => ({
        sid: participant.sid,
        conversationSid: participant.conversationSid,
        identity: participant.identity,
        attributes: participant.attributes ? JSON.parse(participant.attributes) : {},
        messagingBinding: participant.messagingBinding,
        roleSid: participant.roleSid,
        dateCreated: participant.dateCreated,
        dateUpdated: participant.dateUpdated,
        url: participant.url,
        serviceSid: serviceSid || 'default'
      })),
      meta: {
        page: req.query.page || 0,
        pageSize: parseInt(limit),
        nextPageToken: participants.length === parseInt(limit) ? participants[participants.length - 1].sid : null,
        conversationSid,
        serviceSid: serviceSid || 'default'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing participants:', error);
    res.status(500).json({
      error: 'Failed to list participants',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/participants/:conversationSid/:participantSid?serviceSid=xxx - Get a specific participant
router.get('/:conversationSid/:participantSid', async (req, res) => {
  try {
    const { conversationSid, participantSid } = req.params;
    const { serviceSid } = req.query;
    
    const participantsResource = getParticipantsResource(conversationSid, serviceSid);
    const participant = await participantsResource(participantSid).fetch();
    
    res.json({
      sid: participant.sid,
      conversationSid: participant.conversationSid,
      identity: participant.identity,
      attributes: participant.attributes ? JSON.parse(participant.attributes) : {},
      messagingBinding: participant.messagingBinding,
      roleSid: participant.roleSid,
      dateCreated: participant.dateCreated,
      dateUpdated: participant.dateUpdated,
      url: participant.url,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error fetching participant:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Participant not found',
        message: `Participant with SID ${req.params.participantSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch participant',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/participants/:conversationSid - Add a participant to a conversation
router.post('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { 
      identity,
      messagingBindingAddress,
      messagingBindingProxyAddress,
      attributes = {},
      roleSid,
      serviceSid
    } = req.body;
    
    if (!identity && !messagingBindingAddress) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Either identity or messagingBindingAddress is required'
      });
    }
    
    const participantData = {};
    
    if (identity) participantData.identity = identity;
    if (messagingBindingAddress) participantData['messagingBinding.address'] = messagingBindingAddress;
    if (messagingBindingProxyAddress) participantData['messagingBinding.proxyAddress'] = messagingBindingProxyAddress;
    if (roleSid) participantData.roleSid = roleSid;
    if (Object.keys(attributes).length > 0) {
      participantData.attributes = JSON.stringify(attributes);
    }
    
    const participantsResource = getParticipantsResource(conversationSid, serviceSid);
    const participant = await participantsResource.create(participantData);
    
    res.status(201).json({
      sid: participant.sid,
      conversationSid: participant.conversationSid,
      identity: participant.identity,
      attributes: participant.attributes ? JSON.parse(participant.attributes) : {},
      messagingBinding: participant.messagingBinding,
      roleSid: participant.roleSid,
      dateCreated: participant.dateCreated,
      dateUpdated: participant.dateUpdated,
      url: participant.url,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error creating participant:', error);
    if (error.status === 400) {
      return res.status(400).json({
        error: 'Bad Request',
        message: error.message,
        code: error.code
      });
    }
    res.status(500).json({
      error: 'Failed to create participant',
      message: error.message,
      code: error.code
    });
  }
});

// PATCH /api/participants/:conversationSid/:participantSid - Update a participant
router.patch('/:conversationSid/:participantSid', async (req, res) => {
  try {
    const { conversationSid, participantSid } = req.params;
    const { 
      identity,
      attributes,
      roleSid,
      messagingBindingAddress,
      messagingBindingProxyAddress,
      serviceSid
    } = req.body;
    
    const updateData = {};
    
    if (identity !== undefined) updateData.identity = identity;
    if (roleSid !== undefined) updateData.roleSid = roleSid;
    if (messagingBindingAddress !== undefined) updateData['messagingBinding.address'] = messagingBindingAddress;
    if (messagingBindingProxyAddress !== undefined) updateData['messagingBinding.proxyAddress'] = messagingBindingProxyAddress;
    if (attributes !== undefined) {
      updateData.attributes = JSON.stringify(attributes);
    }
    
    const participantsResource = getParticipantsResource(conversationSid, serviceSid);
    const participant = await participantsResource(participantSid).update(updateData);
    
    res.json({
      sid: participant.sid,
      conversationSid: participant.conversationSid,
      identity: participant.identity,
      attributes: participant.attributes ? JSON.parse(participant.attributes) : {},
      messagingBinding: participant.messagingBinding,
      roleSid: participant.roleSid,
      dateCreated: participant.dateCreated,
      dateUpdated: participant.dateUpdated,
      url: participant.url,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error updating participant:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Participant not found',
        message: `Participant with SID ${req.params.participantSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to update participant',
      message: error.message,
      code: error.code
    });
  }
});

// DELETE /api/participants/:conversationSid/:participantSid?serviceSid=xxx - Remove a participant
router.delete('/:conversationSid/:participantSid', async (req, res) => {
  try {
    const { conversationSid, participantSid } = req.params;
    const { serviceSid } = req.query;
    
    const participantsResource = getParticipantsResource(conversationSid, serviceSid);
    await participantsResource(participantSid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting participant:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Participant not found',
        message: `Participant with SID ${req.params.participantSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete participant',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
