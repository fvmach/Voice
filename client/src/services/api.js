import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'development' ? 'http://localhost:3001/api' : '/api');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.params || config.data);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Services API
export const servicesApi = {
  list: (params = {}) => api.get('/services', { params }),
  get: (serviceSid) => api.get(`/services/${serviceSid}`),
  create: (data) => api.post('/services', data),
  delete: (serviceSid) => api.delete(`/services/${serviceSid}`),
};

// Conversations API
export const conversationsApi = {
  list: (params = {}) => api.get('/conversations', { params }),
  get: (conversationSid, params = {}) => api.get(`/conversations/${conversationSid}`, { params }),
  create: (data) => api.post('/conversations', data),
  update: (conversationSid, data) => api.patch(`/conversations/${conversationSid}`, data),
  delete: (conversationSid, params = {}) => api.delete(`/conversations/${conversationSid}`, { params }),
};

// Participants API
export const participantsApi = {
  list: (conversationSid, params = {}) => api.get(`/participants/${conversationSid}`, { params }),
  get: (conversationSid, participantSid, params = {}) => api.get(`/participants/${conversationSid}/${participantSid}`, { params }),
  create: (conversationSid, data) => api.post(`/participants/${conversationSid}`, data),
  update: (conversationSid, participantSid, data) => api.patch(`/participants/${conversationSid}/${participantSid}`, data),
  delete: (conversationSid, participantSid, params = {}) => api.delete(`/participants/${conversationSid}/${participantSid}`, { params }),
};

// Messages API
export const messagesApi = {
  list: (conversationSid, params = {}) => api.get(`/messages/${conversationSid}`, { params }),
  get: (conversationSid, messageSid, params = {}) => api.get(`/messages/${conversationSid}/${messageSid}`, { params }),
  create: (conversationSid, data) => api.post(`/messages/${conversationSid}`, data),
  update: (conversationSid, messageSid, data) => api.patch(`/messages/${conversationSid}/${messageSid}`, data),
  delete: (conversationSid, messageSid, params = {}) => api.delete(`/messages/${conversationSid}/${messageSid}`, { params }),
};

// Media API
export const mediaApi = {
  list: (conversationSid, messageSid, params = {}) => api.get(`/media/${conversationSid}/${messageSid}`, { params }),
  get: (conversationSid, messageSid, mediaSid, params = {}) => api.get(`/media/${conversationSid}/${messageSid}/${mediaSid}`, { params }),
  upload: (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/media/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
  },
  delete: (conversationSid, messageSid, mediaSid, params = {}) => api.delete(`/media/${conversationSid}/${messageSid}/${mediaSid}`, { params }),
};

// Webhooks API
export const webhooksApi = {
  list: (conversationSid, params = {}) => api.get(`/webhooks/${conversationSid}`, { params }),
  get: (conversationSid, webhookSid, params = {}) => api.get(`/webhooks/${conversationSid}/${webhookSid}`, { params }),
  create: (conversationSid, data) => api.post(`/webhooks/${conversationSid}`, data),
  update: (conversationSid, webhookSid, data) => api.patch(`/webhooks/${conversationSid}/${webhookSid}`, data),
  delete: (conversationSid, webhookSid, params = {}) => api.delete(`/webhooks/${conversationSid}/${webhookSid}`, { params }),
};

// Health check
export const healthApi = {
  check: () => api.get('/health'),
};

export default api;
