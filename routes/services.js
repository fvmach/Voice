const express = require('express');
const { client } = require('../config/twilio');
const router = express.Router();

// GET /api/services - List all conversation services
router.get('/', async (req, res) => {
  try {
    const { limit = 50, pageToken } = req.query;
    
    const options = {
      limit: parseInt(limit)
    };
    
    if (pageToken) {
      options.pageToken = pageToken;
    }
    
    const services = await client.conversations.v1.services.list(options);
    
    const response = {
      services: services.map(service => ({
        sid: service.sid,
        accountSid: service.accountSid,
        friendlyName: service.friendlyName,
        dateCreated: service.dateCreated,
        dateUpdated: service.dateUpdated,
        url: service.url,
        links: service.links
      })),
      meta: {
        page: req.query.page || 0,
        pageSize: parseInt(limit),
        nextPageToken: services.length === parseInt(limit) ? services[services.length - 1].sid : null
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing services:', error);
    res.status(500).json({
      error: 'Failed to list services',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/services/:sid - Get a specific service
router.get('/:sid', async (req, res) => {
  try {
    const { sid } = req.params;
    
    const service = await client.conversations.v1.services(sid).fetch();
    
    res.json({
      sid: service.sid,
      accountSid: service.accountSid,
      friendlyName: service.friendlyName,
      dateCreated: service.dateCreated,
      dateUpdated: service.dateUpdated,
      url: service.url,
      links: service.links
    });
  } catch (error) {
    console.error('Error fetching service:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Service not found',
        message: `Service with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch service',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/services - Create a new service
router.post('/', async (req, res) => {
  try {
    const { friendlyName } = req.body;
    
    if (!friendlyName) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'friendlyName is required'
      });
    }
    
    const service = await client.conversations.v1.services.create({
      friendlyName: friendlyName
    });
    
    res.status(201).json({
      sid: service.sid,
      accountSid: service.accountSid,
      friendlyName: service.friendlyName,
      dateCreated: service.dateCreated,
      dateUpdated: service.dateUpdated,
      url: service.url,
      links: service.links
    });
  } catch (error) {
    console.error('Error creating service:', error);
    if (error.status === 400) {
      return res.status(400).json({
        error: 'Bad Request',
        message: error.message,
        code: error.code
      });
    }
    res.status(500).json({
      error: 'Failed to create service',
      message: error.message,
      code: error.code
    });
  }
});

// DELETE /api/services/:sid - Delete a service
router.delete('/:sid', async (req, res) => {
  try {
    const { sid } = req.params;
    
    await client.conversations.v1.services(sid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting service:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Service not found',
        message: `Service with SID ${req.params.sid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete service',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
