const express = require('express');
const { client } = require('../config/twilio');
const router = express.Router();

// Helper function to get the appropriate webhooks resource
const getWebhooksResource = (conversationSid, serviceSid) => {
  if (serviceSid && serviceSid !== 'default') {
    return client.conversations.v1.services(serviceSid).conversations(conversationSid).webhooks;
  }
  return client.conversations.v1.conversations(conversationSid).webhooks;
};

// GET /api/webhooks/:conversationSid?serviceSid=xxx - List webhooks for a conversation
router.get('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { serviceSid } = req.query;
    
    const webhooksResource = getWebhooksResource(conversationSid, serviceSid);
    const webhooks = await webhooksResource.list();
    
    const response = {
      webhooks: webhooks.map(webhook => ({
        sid: webhook.sid,
        conversationSid: webhook.conversationSid,
        target: webhook.target,
        url: webhook.url,
        configuration: webhook.configuration,
        dateCreated: webhook.dateCreated,
        dateUpdated: webhook.dateUpdated,
        serviceSid: serviceSid || 'default'
      })),
      meta: {
        conversationSid,
        serviceSid: serviceSid || 'default'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing webhooks:', error);
    res.status(500).json({
      error: 'Failed to list webhooks',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/webhooks/:conversationSid/:webhookSid?serviceSid=xxx - Get a specific webhook
router.get('/:conversationSid/:webhookSid', async (req, res) => {
  try {
    const { conversationSid, webhookSid } = req.params;
    const { serviceSid } = req.query;
    
    const webhooksResource = getWebhooksResource(conversationSid, serviceSid);
    const webhook = await webhooksResource(webhookSid).fetch();
    
    res.json({
      sid: webhook.sid,
      conversationSid: webhook.conversationSid,
      target: webhook.target,
      url: webhook.url,
      configuration: webhook.configuration,
      dateCreated: webhook.dateCreated,
      dateUpdated: webhook.dateUpdated,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error fetching webhook:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Webhook not found',
        message: `Webhook with SID ${req.params.webhookSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch webhook',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/webhooks/:conversationSid - Create a conversation-scoped webhook
router.post('/:conversationSid', async (req, res) => {
  try {
    const { conversationSid } = req.params;
    const { 
      target,
      webhookUrl,
      configuration = {},
      serviceSid
    } = req.body;
    
    if (!target || !webhookUrl) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'Both target and webhookUrl are required'
      });
    }
    
    // Validate target values
    const validTargets = ['webhook', 'studio', 'trigger'];
    if (!validTargets.includes(target)) {
      return res.status(400).json({
        error: 'Bad Request',
        message: `Target must be one of: ${validTargets.join(', ')}`
      });
    }
    
    const webhookData = {
      target: target,
      'configuration.url': webhookUrl
    };
    
    // Add optional configuration parameters
    if (configuration.method) {
      webhookData['configuration.method'] = configuration.method;
    }
    if (configuration.filters && configuration.filters.length > 0) {
      configuration.filters.forEach((filter, index) => {
        webhookData[`configuration.filters[${index}]`] = filter;
      });
    }
    if (configuration.triggers && Object.keys(configuration.triggers).length > 0) {
      Object.entries(configuration.triggers).forEach(([key, value]) => {
        webhookData[`configuration.triggers.${key}`] = value;
      });
    }
    if (configuration.flowSid) {
      webhookData['configuration.flowSid'] = configuration.flowSid;
    }
    
    const webhooksResource = getWebhooksResource(conversationSid, serviceSid);
    const webhook = await webhooksResource.create(webhookData);
    
    res.status(201).json({
      sid: webhook.sid,
      conversationSid: webhook.conversationSid,
      target: webhook.target,
      url: webhook.url,
      configuration: webhook.configuration,
      dateCreated: webhook.dateCreated,
      dateUpdated: webhook.dateUpdated,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error creating webhook:', error);
    if (error.status === 400) {
      return res.status(400).json({
        error: 'Bad Request',
        message: error.message,
        code: error.code
      });
    }
    res.status(500).json({
      error: 'Failed to create webhook',
      message: error.message,
      code: error.code
    });
  }
});

// PATCH /api/webhooks/:conversationSid/:webhookSid - Update a webhook
router.patch('/:conversationSid/:webhookSid', async (req, res) => {
  try {
    const { conversationSid, webhookSid } = req.params;
    const { 
      target,
      webhookUrl,
      configuration = {},
      serviceSid
    } = req.body;
    
    const updateData = {};
    
    if (target !== undefined) {
      const validTargets = ['webhook', 'studio', 'trigger'];
      if (!validTargets.includes(target)) {
        return res.status(400).json({
          error: 'Bad Request',
          message: `Target must be one of: ${validTargets.join(', ')}`
        });
      }
      updateData.target = target;
    }
    
    if (webhookUrl !== undefined) {
      updateData['configuration.url'] = webhookUrl;
    }
    
    // Add optional configuration parameters
    if (configuration.method) {
      updateData['configuration.method'] = configuration.method;
    }
    if (configuration.filters && configuration.filters.length > 0) {
      configuration.filters.forEach((filter, index) => {
        updateData[`configuration.filters[${index}]`] = filter;
      });
    }
    if (configuration.triggers && Object.keys(configuration.triggers).length > 0) {
      Object.entries(configuration.triggers).forEach(([key, value]) => {
        updateData[`configuration.triggers.${key}`] = value;
      });
    }
    if (configuration.flowSid) {
      updateData['configuration.flowSid'] = configuration.flowSid;
    }
    
    const webhooksResource = getWebhooksResource(conversationSid, serviceSid);
    const webhook = await webhooksResource(webhookSid).update(updateData);
    
    res.json({
      sid: webhook.sid,
      conversationSid: webhook.conversationSid,
      target: webhook.target,
      url: webhook.url,
      configuration: webhook.configuration,
      dateCreated: webhook.dateCreated,
      dateUpdated: webhook.dateUpdated,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error updating webhook:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Webhook not found',
        message: `Webhook with SID ${req.params.webhookSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to update webhook',
      message: error.message,
      code: error.code
    });
  }
});

// DELETE /api/webhooks/:conversationSid/:webhookSid?serviceSid=xxx - Delete a webhook
router.delete('/:conversationSid/:webhookSid', async (req, res) => {
  try {
    const { conversationSid, webhookSid } = req.params;
    const { serviceSid } = req.query;
    
    const webhooksResource = getWebhooksResource(conversationSid, serviceSid);
    await webhooksResource(webhookSid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting webhook:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Webhook not found',
        message: `Webhook with SID ${req.params.webhookSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete webhook',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
