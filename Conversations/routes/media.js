const express = require('express');
const multer = require('multer');
const { client } = require('../config/twilio');
const { v4: uuidv4 } = require('uuid');
const router = express.Router();

// Configure multer for file uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024, // 50MB limit
  },
  fileFilter: (req, file, cb) => {
    // Allow common media types
    const allowedTypes = [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp',
      'video/mp4', 'video/quicktime', 'video/x-msvideo',
      'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4',
      'application/pdf', 'text/plain'
    ];
    
    if (allowedTypes.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error(`File type ${file.mimetype} not supported`), false);
    }
  }
});

// Helper function to get the appropriate media resource
const getMediaResource = (conversationSid, serviceSid) => {
  if (serviceSid && serviceSid !== 'default') {
    return client.conversations.v1.services(serviceSid).conversations(conversationSid).messages;
  }
  return client.conversations.v1.conversations(conversationSid).messages;
};

// GET /api/media/:conversationSid/:messageSid/:mediaSid?serviceSid=xxx - Get media details
router.get('/:conversationSid/:messageSid/:mediaSid', async (req, res) => {
  try {
    const { conversationSid, messageSid, mediaSid } = req.params;
    const { serviceSid } = req.query;
    
    const messagesResource = getMediaResource(conversationSid, serviceSid);
    const media = await messagesResource(messageSid).media(mediaSid).fetch();
    
    res.json({
      sid: media.sid,
      messageSid: media.messageSid,
      conversationSid: media.conversationSid,
      contentType: media.contentType,
      filename: media.filename,
      size: media.size,
      dateCreated: media.dateCreated,
      dateUpdated: media.dateUpdated,
      url: media.url,
      serviceSid: serviceSid || 'default'
    });
  } catch (error) {
    console.error('Error fetching media:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Media not found',
        message: `Media with SID ${req.params.mediaSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to fetch media',
      message: error.message,
      code: error.code
    });
  }
});

// GET /api/media/:conversationSid/:messageSid?serviceSid=xxx - List media for a message
router.get('/:conversationSid/:messageSid', async (req, res) => {
  try {
    const { conversationSid, messageSid } = req.params;
    const { serviceSid } = req.query;
    
    const messagesResource = getMediaResource(conversationSid, serviceSid);
    const mediaList = await messagesResource(messageSid).media.list();
    
    const response = {
      media: mediaList.map(media => ({
        sid: media.sid,
        messageSid: media.messageSid,
        conversationSid: media.conversationSid,
        contentType: media.contentType,
        filename: media.filename,
        size: media.size,
        dateCreated: media.dateCreated,
        dateUpdated: media.dateUpdated,
        url: media.url,
        serviceSid: serviceSid || 'default'
      })),
      meta: {
        conversationSid,
        messageSid,
        serviceSid: serviceSid || 'default'
      }
    };
    
    res.json(response);
  } catch (error) {
    console.error('Error listing media:', error);
    res.status(500).json({
      error: 'Failed to list media',
      message: error.message,
      code: error.code
    });
  }
});

// POST /api/media/upload - Upload media file and get media SID
router.post('/upload', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        error: 'Bad Request',
        message: 'No file uploaded'
      });
    }
    
    // For now, we'll return a placeholder response since Twilio media upload
    // requires the media to be uploaded to a publicly accessible URL first
    // In a real implementation, you'd upload to S3, Google Cloud, etc.
    
    const mediaInfo = {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
      size: req.file.size,
      buffer: req.file.buffer.toString('base64'), // Base64 for demo purposes
      uploadId: uuidv4() // Temporary ID for tracking
    };
    
    // Store temporarily (in production, upload to cloud storage)
    // This is just for demo purposes
    res.status(201).json({
      uploadId: mediaInfo.uploadId,
      filename: mediaInfo.filename,
      contentType: mediaInfo.contentType,
      size: mediaInfo.size,
      message: 'File uploaded successfully. Use this uploadId when sending a message with media.',
      note: 'In production, this would upload to cloud storage and return a public URL.'
    });
    
  } catch (error) {
    console.error('Error uploading media:', error);
    if (error.code === 'LIMIT_FILE_SIZE') {
      return res.status(400).json({
        error: 'File too large',
        message: 'File size exceeds 50MB limit'
      });
    }
    res.status(500).json({
      error: 'Failed to upload media',
      message: error.message
    });
  }
});

// DELETE /api/media/:conversationSid/:messageSid/:mediaSid?serviceSid=xxx - Delete media
router.delete('/:conversationSid/:messageSid/:mediaSid', async (req, res) => {
  try {
    const { conversationSid, messageSid, mediaSid } = req.params;
    const { serviceSid } = req.query;
    
    const messagesResource = getMediaResource(conversationSid, serviceSid);
    await messagesResource(messageSid).media(mediaSid).remove();
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting media:', error);
    if (error.status === 404) {
      return res.status(404).json({
        error: 'Media not found',
        message: `Media with SID ${req.params.mediaSid} was not found`
      });
    }
    res.status(500).json({
      error: 'Failed to delete media',
      message: error.message,
      code: error.code
    });
  }
});

module.exports = router;
