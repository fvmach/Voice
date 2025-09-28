import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Box } from '@twilio-paste/core/box';
import { Flex } from '@twilio-paste/core/flex';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';
import { Button } from '@twilio-paste/core/button';
import { Card } from '@twilio-paste/core/card';
import { Badge } from '@twilio-paste/core/badge';
import { Alert } from '@twilio-paste/core/alert';
import { Spinner } from '@twilio-paste/core/spinner';
import { Tabs, TabList, Tab, TabPanels, TabPanel } from '@twilio-paste/core/tabs';
import { Table, THead, TBody, Tr, Th, Td } from '@twilio-paste/core/table';
import { Modal, ModalHeader, ModalHeading, ModalBody, ModalFooter, ModalFooterActions } from '@twilio-paste/core/modal';
import { Input } from '@twilio-paste/core/input';
import { Label } from '@twilio-paste/core/label';
import { Select, Option } from '@twilio-paste/core/select';
import { FormControl } from '@twilio-paste/core/form';
import { HelpText } from '@twilio-paste/core/help-text';
import { TextArea } from '@twilio-paste/core/textarea';
import { ArrowBackIcon } from '@twilio-paste/icons/esm/ArrowBackIcon';
import { ProductConversationsIcon } from '@twilio-paste/icons/esm/ProductConversationsIcon';
import { UserIcon } from '@twilio-paste/icons/esm/UserIcon';
import { ChatIcon } from '@twilio-paste/icons/esm/ChatIcon';
import { AttachIcon } from '@twilio-paste/icons/esm/AttachIcon';
import { LinkIcon } from '@twilio-paste/icons/esm/LinkIcon';
import { PlusIcon } from '@twilio-paste/icons/esm/PlusIcon';
import { EditIcon } from '@twilio-paste/icons/esm/EditIcon';
import { DeleteIcon } from '@twilio-paste/icons/esm/DeleteIcon';
import { SendIcon } from '@twilio-paste/icons/esm/SendIcon';
import { DownloadIcon } from '@twilio-paste/icons/esm/DownloadIcon';
import { FileIcon } from '@twilio-paste/icons/esm/FileIcon';
import { UploadToCloudIcon } from '@twilio-paste/icons/esm/UploadToCloudIcon';
import { ProductVoiceIcon } from '@twilio-paste/icons/esm/ProductVoiceIcon';
import { DataLineChartIcon } from '@twilio-paste/icons/esm/DataLineChartIcon';
import { ConnectivityAvailableIcon } from '@twilio-paste/icons/esm/ConnectivityAvailableIcon';
import { format } from 'date-fns';
import { conversationsApi, participantsApi, messagesApi, webhooksApi, mediaApi, signalSpApi } from '../services/api';

// Content rendering utilities
const detectContentType = (content) => {
  if (typeof content !== 'string') return 'text';
  
  const trimmedContent = content.trim();
  
  // JSON detection
  if ((trimmedContent.startsWith('{') && trimmedContent.endsWith('}')) ||
      (trimmedContent.startsWith('[') && trimmedContent.endsWith(']'))) {
    try {
      JSON.parse(trimmedContent);
      return 'json';
    } catch {
      // Fall through to other checks
    }
  }
  
  // Markdown detection (basic patterns)
  if (trimmedContent.includes('**') || 
      trimmedContent.includes('##') ||
      trimmedContent.includes('- ') ||
      trimmedContent.includes('1. ') ||
      trimmedContent.includes('```')) {
    return 'markdown';
  }
  
  // Code detection (basic patterns)
  if (trimmedContent.includes('function ') ||
      trimmedContent.includes('const ') ||
      trimmedContent.includes('import ') ||
      trimmedContent.includes('class ') ||
      trimmedContent.includes('def ') ||
      trimmedContent.includes('SELECT ') ||
      trimmedContent.includes('FROM ')) {
    return 'code';
  }
  
  return 'text';
};

const renderMarkdownContent = (content) => {
  if (!content) return content;
  
  return content
    // Bold text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Headers
    .replace(/^### (.*$)/gm, '<h3 style="font-size: 1.1em; font-weight: bold; margin: 16px 0 8px 0; color: #0f172a;">$1</h3>')
    .replace(/^## (.*$)/gm, '<h2 style="font-size: 1.2em; font-weight: bold; margin: 20px 0 10px 0; color: #0f172a;">$1</h2>')
    .replace(/^# (.*$)/gm, '<h1 style="font-size: 1.3em; font-weight: bold; margin: 24px 0 12px 0; color: #0f172a;">$1</h1>')
    // List items
    .replace(/^- (.*$)/gm, '<div style="margin: 4px 0; padding-left: 16px;">• $1</div>')
    .replace(/^(\d+)\. (.*$)/gm, '<div style="margin: 4px 0; padding-left: 16px;">$1. $2</div>')
    // Line breaks
    .replace(/\n/g, '<br/>');
};

const ContentRenderer = ({ content, type = null, showTypeIndicator = false }) => {
  if (!content) return null;
  
  const contentType = type || detectContentType(content);
  const contentStr = typeof content === 'string' ? content : JSON.stringify(content, null, 2);
  
  const TypeIndicator = () => {
    if (!showTypeIndicator) return null;
    
    const typeColors = {
      json: 'neutral',
      markdown: 'success', 
      code: 'warning',
      text: 'neutral'
    };
    
    const typeLabels = {
      json: 'JSON',
      markdown: 'Markdown',
      code: 'Code',
      text: 'Text'
    };
    
    return (
      <Badge 
        variant={typeColors[contentType]} 
        size="small" 
        marginBottom="space20"
      >
        {typeLabels[contentType]}
      </Badge>
    );
  };
  
  switch (contentType) {
    case 'json':
      return (
        <Box>
          <TypeIndicator />
          <Box 
            backgroundColor="colorBackgroundBodyInverse" 
            padding="space30" 
            borderRadius="borderRadius20"
            border="borderStyleSolid"
            borderWidth="borderWidth10"
            borderColor="colorBorderNeutralWeak"
          >
            <Text 
              fontFamily="fontFamilyCode" 
              fontSize="fontSize30" 
              color="colorTextInverse"
              lineHeight="lineHeight30"
            >
              {typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
            </Text>
          </Box>
        </Box>
      );
      
    case 'markdown':
      return (
        <Box>
          <TypeIndicator />
          <Box 
            backgroundColor="colorBackgroundNeutralWeakest" 
            padding="space30" 
            borderRadius="borderRadius20"
            borderLeftWidth="borderWidth30"
            borderLeftStyle="solid"
            borderLeftColor="colorBorderPrimary"
          >
            <Text 
              fontSize="fontSize30" 
              lineHeight="lineHeight40"
              color="colorText"
            >
              <span dangerouslySetInnerHTML={{ __html: renderMarkdownContent(contentStr) }} />
            </Text>
          </Box>
        </Box>
      );
      
    case 'code':
      return (
        <Box>
          <TypeIndicator />
          <Box 
            backgroundColor="colorBackgroundBodyInverse" 
            padding="space30" 
            borderRadius="borderRadius20"
            border="borderStyleSolid"
            borderWidth="borderWidth10"
            borderColor="colorBorderSuccess"
          >
            <Text 
              fontFamily="fontFamilyCode" 
              fontSize="fontSize30" 
              color="colorTextInverse"
              lineHeight="lineHeight30"
              style={{ whiteSpace: 'pre-wrap' }}
            >
              {contentStr}
            </Text>
          </Box>
        </Box>
      );
      
    default:
      return (
        <Box>
          <TypeIndicator />
          <Box 
            backgroundColor="colorBackgroundNeutralWeakest" 
            padding="space30" 
            borderRadius="borderRadius20"
            borderLeftWidth="borderWidth20"
            borderLeftStyle="solid"
            borderLeftColor="colorBorderNeutral"
          >
            <Text 
              fontSize="fontSize30" 
              lineHeight="lineHeight40"
              color="colorText"
              style={{ whiteSpace: 'pre-wrap' }}
            >
              {contentStr}
            </Text>
          </Box>
        </Box>
      );
  }
};

// Helper functions for form placeholders and help text
const getAddressPlaceholder = (bindingType) => {
  switch (bindingType) {
    case 'whatsapp': return '+1234567890';
    case 'sms': return '+1234567890';
    case 'messenger': return 'Facebook User ID';
    case 'gbm': return 'Google User ID';
    case 'instagram': return 'Instagram User ID';
    default: return '+1234567890';
  }
};

const getAddressHelpText = (bindingType) => {
  switch (bindingType) {
    case 'whatsapp': return 'Customer WhatsApp number (without whatsapp: prefix)';
    case 'sms': return 'Customer phone number';
    case 'messenger': return 'Customer Facebook Messenger ID';
    case 'gbm': return 'Customer Google Business Messages ID';
    case 'instagram': return 'Customer Instagram ID';
    default: return 'Customer contact address';
  }
};

const getProxyPlaceholder = (bindingType) => {
  switch (bindingType) {
    case 'whatsapp': return '+19111111111';
    case 'sms': return '+19111111111';
    case 'messenger': return 'Your Facebook Page ID';
    case 'gbm': return 'Your GBM Agent ID';
    case 'instagram': return 'Your Instagram Business ID';
    default: return '+19111111111';
  }
};

const getProxyHelpText = (bindingType) => {
  switch (bindingType) {
    case 'whatsapp': return 'Your Twilio WhatsApp sender number (without whatsapp: prefix)';
    case 'sms': return 'Your Twilio phone number for sending SMS';
    case 'messenger': return 'Your Facebook Page ID for Messenger';
    case 'gbm': return 'Your Google Business Messages agent ID';
    case 'instagram': return 'Your Instagram Business account ID';
    default: return 'Your Twilio sender number';
  }
};

const ConversationDetailPage = () => {
  const { conversationSid } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedTab, setSelectedTab] = useState('overview');
  
  // For now, we'll use default service. In a full implementation,
  // you'd get the serviceSid from URL params or context
  const serviceSid = undefined; // This means default service
  
  // Modal states
  const [editConversationModal, setEditConversationModal] = useState(false);
  const [addParticipantModal, setAddParticipantModal] = useState(false);
  const [sendMessageModal, setSendMessageModal] = useState(false);
  const [addWebhookModal, setAddWebhookModal] = useState(false);
  const [deleteItemModal, setDeleteItemModal] = useState({ open: false, item: null, type: null });
  const [uploadMediaModal, setUploadMediaModal] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  
  // Form states
  const [conversationForm, setConversationForm] = useState({
    friendlyName: '',
    uniqueName: '',
    state: 'active',
    attributes: '{}'
  });
  const [participantForm, setParticipantForm] = useState({ 
    identity: '', 
    address: '', 
    proxyAddress: '',
    bindingType: 'sms' // sms, whatsapp, etc.
  });
  const [messageForm, setMessageForm] = useState({ body: '', author: '' });
  const [webhookForm, setWebhookForm] = useState({ target: 'webhook', url: '', method: 'POST' });
  
  const [error, setError] = useState(null);
  
  // Intelligence and transcription states
  const [conversationLanguage, setConversationLanguage] = useState('pt-BR'); // Default language
  const [transcriptionMessages, setTranscriptionMessages] = useState([]);
  const [isConnectedToWebSocket, setIsConnectedToWebSocket] = useState(false);
  const [webSocket, setWebSocket] = useState(null);
  
  // Export intelligence states
  const [exportStatus, setExportStatus] = useState({ loading: false, error: null, success: null });
  const [autoExported, setAutoExported] = useState(false);
  
  // Live Monitor states
  const [liveMonitorMessages, setLiveMonitorMessages] = useState([]);
  const [liveMonitorWebSocket, setLiveMonitorWebSocket] = useState(null);
  const [isConnectedToLiveMonitor, setIsConnectedToLiveMonitor] = useState(false);
  const liveMonitorScrollRef = React.useRef(null);

  // Fetch conversation details
  const { data: conversationData, isLoading, error: fetchError } = useQuery(
    ['conversation', conversationSid],
    () => conversationsApi.get(conversationSid, serviceSid),
    {
      enabled: !!conversationSid,
    }
  );
  
  // Fetch participants
  const { data: participantsData, isLoading: participantsLoading } = useQuery(
    ['participants', conversationSid],
    () => participantsApi.list(conversationSid, serviceSid ? { serviceSid } : {}),
    {
      enabled: !!conversationSid && selectedTab === 'participants',
    }
  );
  
  // Fetch messages
  const { data: messagesData, isLoading: messagesLoading } = useQuery(
    ['messages', conversationSid],
    () => messagesApi.list(conversationSid, serviceSid ? { serviceSid } : {}),
    {
      enabled: !!conversationSid && (selectedTab === 'messages' || selectedTab === 'media'),
    }
  );
  
  // Fetch webhooks
  const { data: webhooksData, isLoading: webhooksLoading } = useQuery(
    ['webhooks', conversationSid],
    () => webhooksApi.list(conversationSid, serviceSid ? { serviceSid } : {}),
    {
      enabled: !!conversationSid && selectedTab === 'webhooks',
    }
  );
  
  // Extract all media files directly from messages data
  const { data: allMediaData, isLoading: mediaLoading } = useQuery(
    ['media', conversationSid],
    async () => {
      const messagesFromData = messagesData?.data?.messages || messagesData?.messages || [];
      
      if (messagesFromData.length === 0) return { media: [] };
      
      const messagesWithMedia = messagesFromData.filter(message => message.media && message.media.length > 0);
      
      // Extract media directly from message objects (no API calls needed)
      const allMedia = messagesWithMedia.flatMap(message => 
        message.media.map(media => ({
          // Map Twilio API field names to our expected structure
          sid: media.sid,
          messageSid: message.sid,
          conversationSid: conversationSid,
          contentType: media.content_type,
          filename: media.filename,
          size: media.size,
          category: media.category,
          dateCreated: message.dateCreated, // Use message date since media doesn't have separate date
          dateUpdated: message.dateUpdated,
          url: `https://media.twiliocdn.com/${media.sid}`, // Construct URL based on Twilio pattern
          // Additional context from message
          messageAuthor: message.author,
          messageBody: message.body,
          messageIndex: message.index,
          messageDate: message.dateCreated
        }))
      );
      
      
      return { media: allMedia };
    },
    {
      enabled: !!conversationSid && selectedTab === 'media' && !!(messagesData?.data?.messages || messagesData?.messages),
    }
  );
  
  // Extract conversation data early so it can be used in subsequent queries
  const conversation = conversationData?.data || conversationData;
  
  // Fetch intelligence data from Twilio Intelligence API
  const { data: intelligenceData, isLoading: intelligenceLoading } = useQuery(
    ['intelligence', conversationSid, conversationLanguage],
    () => conversationsApi.getIntelligence(conversationSid, serviceSid, conversationLanguage),
    {
      // Fetch when viewing Intelligence tab for any conversation
      enabled: !!conversationSid && selectedTab === 'intelligence',
      retry: 1, // Only retry once since this might not be available for all conversations
      staleTime: 30000, // Cache for 30 seconds
    }
  );
  
  // Fetch conversation-specific intelligence data from Signal SP Session server
  const { data: conversationIntelligenceData, isLoading: conversationIntelligenceLoading, error: conversationIntelligenceError } = useQuery(
    ['conversationIntelligence', conversationSid],
    () => signalSpApi.getConversationIntelligence(conversationSid),
    {
      // Fetch intelligence data when viewing Intelligence tab
      enabled: selectedTab === 'intelligence' && !!conversationSid,
      retry: 1,
      staleTime: 60000, // Cache for 60 seconds
      onError: (error) => {
        console.error('Failed to fetch conversation intelligence:', error);
      }
    }
  );
  
  // Helper function to determine if conversation is voice-based
  const isVoiceConversation = () => {
    // Check if conversation attributes indicate voice based on your rule patterns
    const conversationInfo = conversationData?.data || conversationData;
    const attributes = conversationInfo?.attributes || {};
    
    // Check for multiple voice indicators based on your conversation data structure
    return attributes.channel === 'voice' || 
           attributes.call_sid || 
           attributes.type === 'voice' || 
           attributes.conversationType === 'voice' ||
           conversationInfo?.friendlyName?.includes('Voice Call');
  };
  
  const hasIntelligenceData = () => {
    // Only consider data that actually belongs to THIS conversation
    const conversationInfo = conversationData?.data || conversationData;
    const currentCallSid = conversationInfo?.attributes?.call_sid;
    
    // Check if the intelligence data is specifically for this call
    const hasCurrentCallData = conversationIntelligenceData?.data && 
                               conversationIntelligenceData.data.call_sid === currentCallSid &&
                               (conversationIntelligenceData.data.transcript?.sentences?.length > 0 ||
                                conversationIntelligenceData.data.operator_results?.length > 0);
                                
    // For Twilio Intelligence API fallback (less reliable for call matching)
    const hasTwilioIntelligence = intelligenceData?.data && 
                                  (intelligenceData.data.transcript?.sentences?.length > 0 ||
                                   intelligenceData.data.operatorResults?.length > 0);
                                   
    return hasCurrentCallData || hasTwilioIntelligence;
  };
  
  const shouldShowLiveMonitor = () => {
    // Show Live Monitor for all active voice conversations
    const conversationInfo = conversationData?.data || conversationData;
    const isActive = conversationInfo?.state === 'active';
    const isVoice = isVoiceConversation();
    
    console.log('Live Monitor Check:', {
      isVoiceConversation: isVoice,
      isActive,
      conversationState: conversationInfo?.state,
      attributes: conversationInfo?.attributes,
      callSid: conversationInfo?.attributes?.call_sid
    });
    
    // For debugging: Show Live Monitor if URL contains ?monitor=true
    const forceMonitor = new URLSearchParams(window.location.search).get('monitor') === 'true';
    if (forceMonitor && isVoice) {
      console.log('Live Monitor forced via ?monitor=true');
      return true;
    }
    
    return isVoice && isActive;
  };
  
  // Live Monitor log parsing functions
  const parseLogMessage = (message) => {
    const timestamp = new Date().toISOString();
    
    // Parse different log types from server.py
    if (typeof message === 'object') {
      // WebSocket events (transcription data)
      if (message.type === 'prompt' || message.event === 'prompt') {
        return {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'transcription',
          category: 'customer',
          content: message.voicePrompt || message.text,
          icon: 'user',
          color: 'primary'
        };
      }
      
      if (message.type === 'tts' || message.event === 'tts') {
        return {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'transcription',
          category: 'agent',
          content: message.text || message.content,
          icon: 'bot',
          color: 'success'
        };
      }
      
      if (message.type === 'intelligence') {
        return {
          id: Date.now() + Math.random(),
          timestamp,
          type: 'intelligence',
          category: 'analysis',
          content: `Intelligence analysis completed for transcript ${message.data?.transcript?.sid}`,
          icon: 'brain',
          color: 'warning'
        };
      }
    }
    
    // Parse string log messages
    const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
    
    // System messages [SYS]
    if (messageStr.includes('[SYS]')) {
      return {
        id: Date.now() + Math.random(),
        timestamp,
        type: 'system',
        category: 'info',
        content: messageStr.replace(/\[SYS\]\s*/, '').replace(/\x1b\[[0-9;]*m/g, ''), // Remove color codes
        icon: 'system',
        color: 'neutral'
      };
    }
    
    // Speech-to-text messages [STT]
    if (messageStr.includes('[STT]')) {
      return {
        id: Date.now() + Math.random(),
        timestamp,
        type: 'transcription',
        category: 'processing',
        content: messageStr.replace(/\[STT\]\s*/, '').replace(/\x1b\[[0-9;]*m/g, ''),
        icon: 'microphone',
        color: 'primary'
      };
    }
    
    // Intelligence messages [SPI]
    if (messageStr.includes('[SPI]')) {
      return {
        id: Date.now() + Math.random(),
        timestamp,
        type: 'intelligence',
        category: 'analysis',
        content: messageStr.replace(/\[SPI\]\s*/, '').replace(/\x1b\[[0-9;]*m/g, ''),
        icon: 'brain',
        color: 'warning'
      };
    }
    
    // Error messages [ERR]
    if (messageStr.includes('[ERR]')) {
      return {
        id: Date.now() + Math.random(),
        timestamp,
        type: 'error',
        category: 'error',
        content: messageStr.replace(/\[ERR\]\s*/, '').replace(/\x1b\[[0-9;]*m/g, ''),
        icon: 'error',
        color: 'error'
      };
    }
    
    // Tool usage (banking tools, personalization)
    if (messageStr.includes('tool') || messageStr.includes('banking') || messageStr.includes('personalization')) {
      return {
        id: Date.now() + Math.random(),
        timestamp,
        type: 'tools',
        category: 'tools',
        content: messageStr.replace(/\x1b\[[0-9;]*m/g, ''),
        icon: 'tool',
        color: 'success'
      };
    }
    
    // Default message
    return {
      id: Date.now() + Math.random(),
      timestamp,
      type: 'general',
      category: 'info',
      content: messageStr.replace(/\x1b\[[0-9;]*m/g, ''),
      icon: 'info',
      color: 'neutral'
    };
  };
  
  // Auto-scroll Live Monitor to bottom when new messages arrive
  useEffect(() => {
    if (liveMonitorScrollRef.current && liveMonitorMessages.length > 0) {
      liveMonitorScrollRef.current.scrollTop = liveMonitorScrollRef.current.scrollHeight;
    }
  }, [liveMonitorMessages]);
  
  // Auto-connect Live Monitor for active voice conversations
  useEffect(() => {
    if (shouldShowLiveMonitor() && selectedTab === 'livemonitor' && !isConnectedToLiveMonitor) {
      console.log('Auto-connecting Live Monitor for active voice conversation');
      // Auto-connect to Dashboard WebSocket
      const ws = new WebSocket(signalSpApi.getDashboardWebSocketUrl());
      ws.onopen = () => {
        setIsConnectedToLiveMonitor(true);
        setLiveMonitorWebSocket(ws);
        console.log('Live Monitor auto-connected');
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const parsedMessage = parseLogMessage(data);
          setLiveMonitorMessages(prev => [...prev, parsedMessage].slice(-100));
        } catch (e) {
          const parsedMessage = parseLogMessage(event.data);
          setLiveMonitorMessages(prev => [...prev, parsedMessage].slice(-100));
        }
      };
      ws.onclose = () => {
        setIsConnectedToLiveMonitor(false);
        setLiveMonitorWebSocket(null);
      };
      ws.onerror = (error) => {
        console.error('Live Monitor WebSocket error:', error);
        setIsConnectedToLiveMonitor(false);
      };
    }
  }, [shouldShowLiveMonitor(), selectedTab, isConnectedToLiveMonitor]);
  
  // Auto-connect Live Transcription for voice conversations
  useEffect(() => {
    if (isVoiceConversation() && selectedTab === 'transcription' && !isConnectedToWebSocket) {
      console.log('Auto-connecting Live Transcription for voice conversation');
      const ws = new WebSocket(signalSpApi.getTranscriptionWebSocketUrl());
      ws.onopen = () => {
        setIsConnectedToWebSocket(true);
        setWebSocket(ws);
        console.log('Live Transcription auto-connected');
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.event === 'prompt' || data.type === 'prompt') {
            setTranscriptionMessages(prev => [...prev, {
              id: Date.now() + Math.random(),
              type: 'customer',
              text: data.voicePrompt || data.text,
              timestamp: new Date().toISOString()
            }]);
          } else if (data.event === 'tts' || data.type === 'tts') {
            setTranscriptionMessages(prev => [...prev, {
              id: Date.now() + Math.random(),
              type: 'agent', 
              text: data.text || data.content,
              timestamp: new Date().toISOString()
            }]);
          }
        } catch (e) {
          console.warn('Failed to parse WebSocket message:', e);
        }
      };
      ws.onclose = () => {
        setIsConnectedToWebSocket(false);
        setWebSocket(null);
      };
      ws.onerror = (error) => {
        console.error('Live Transcription WebSocket error:', error);
        setIsConnectedToWebSocket(false);
      };
    }
  }, [isVoiceConversation(), selectedTab, isConnectedToWebSocket]);
  
  // Cleanup WebSocket connections on unmount
  useEffect(() => {
    return () => {
      if (liveMonitorWebSocket) {
        liveMonitorWebSocket.close();
      }
      if (webSocket) {
        webSocket.close();
      }
    };
  }, [liveMonitorWebSocket, webSocket]);
  
  
  // Mutations
  const updateConversationMutation = useMutation(
    (data) => conversationsApi.update(conversationSid, data, serviceSid),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['conversation', conversationSid]);
        setEditConversationModal(false);
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to update conversation')
    }
  );
  
  const addParticipantMutation = useMutation(
    (data) => participantsApi.create(conversationSid, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['participants', conversationSid]);
        setAddParticipantModal(false);
        setParticipantForm({ identity: '', address: '', proxyAddress: '', bindingType: 'sms' });
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to add participant')
    }
  );
  
  const sendMessageMutation = useMutation(
    (data) => messagesApi.create(conversationSid, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['messages', conversationSid]);
        setSendMessageModal(false);
        setMessageForm({ body: '', author: '' });
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to send message')
    }
  );
  
  const addWebhookMutation = useMutation(
    (data) => webhooksApi.create(conversationSid, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['webhooks', conversationSid]);
        setAddWebhookModal(false);
        setWebhookForm({ target: 'webhook', url: '', method: 'POST' });
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to add webhook')
    }
  );
  
  const deleteItemMutation = useMutation(
    ({ itemId, type, messageSid }) => {
      switch (type) {
        case 'participant':
          return participantsApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        case 'message':
          return messagesApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        case 'webhook':
          return webhooksApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        case 'media':
          return mediaApi.delete(conversationSid, messageSid, itemId, serviceSid ? { serviceSid } : {});
        default:
          throw new Error('Unknown delete type');
      }
    },
    {
      onSuccess: (_, variables) => {
        if (variables.type === 'media') {
          queryClient.invalidateQueries(['media', conversationSid]);
          queryClient.invalidateQueries(['messages', conversationSid]);
        } else {
          queryClient.invalidateQueries([variables.type + 's', conversationSid]);
        }
        setDeleteItemModal({ open: false, item: null, type: null });
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to delete item')
    }
  );
  
  const uploadMediaMutation = useMutation(
    (files) => {
      const uploadPromises = files.map(file => 
        mediaApi.upload(file, (progressEvent) => {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100);
          setUploadProgress(prev => ({ ...prev, [file.name]: progress }));
        })
      );
      return Promise.all(uploadPromises);
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['media', conversationSid]);
        setUploadMediaModal(false);
        setSelectedFiles([]);
        setUploadProgress({});
        setError(null);
      },
      onError: (error) => {
        setError(error.response?.data?.message || 'Failed to upload media');
        setUploadProgress({});
      }
    }
  );
  
  // Export conversation for intelligence processing
  const exportConversationMutation = useMutation(
    ({ language }) => conversationsApi.export(conversationSid, serviceSid, language),
    {
      onMutate: () => {
        setExportStatus({ loading: true, error: null, success: null });
      },
      onSuccess: (response) => {
        setExportStatus({ 
          loading: false, 
          error: null, 
          success: `Export initiated successfully. Export SID: ${response.data?.exportSid}` 
        });
        // Refresh intelligence data after export
        setTimeout(() => {
          queryClient.invalidateQueries(['intelligence', conversationSid]);
          queryClient.invalidateQueries(['conversationIntelligence', conversationSid]);
        }, 2000);
      },
      onError: (error) => {
        setExportStatus({ 
          loading: false, 
          error: error.response?.data?.message || 'Failed to export conversation', 
          success: null 
        });
      }
    }
  );

  // Data extraction - Handle both wrapped and unwrapped responses  
  const participants = participantsData?.data?.participants || participantsData?.participants || [];
  const messages = messagesData?.data?.messages || messagesData?.messages || [];
  const webhooks = webhooksData?.data?.webhooks || webhooksData?.webhooks || [];
  const allMedia = allMediaData?.media || [];
  
  // Auto-export conversation when it's a closed messaging conversation
  useEffect(() => {
    if (!conversation || autoExported) return;
    
    const isMessaging = !isVoiceConversation();
    const isClosed = conversation.state === 'closed' || conversation.state === 'inactive';
    const hasMessages = messages.length > 0;
    
    if (isMessaging && isClosed && hasMessages) {
      console.log('Auto-exporting messaging conversation for intelligence processing');
      setAutoExported(true);
      exportConversationMutation.mutate({ language: conversationLanguage });
    }
  }, [conversation, messages.length, autoExported, conversationLanguage, exportConversationMutation, isVoiceConversation]);
  
  if (isLoading) {
    return (
      <Flex vAlignContent="center" hAlignContent="center" height="400px">
        <Spinner decorative size="sizeIcon110" />
        <Text marginLeft="space40">Loading conversation details...</Text>
      </Flex>
    );
  }

  if (fetchError) {
    return (
      <Box>
        <Alert variant="error" marginBottom="space40">
          <Text as="span">
            <strong>Error:</strong> {fetchError.response?.data?.message || fetchError.message}
          </Text>
        </Alert>
      </Box>
    );
  }

  // Handler functions
  const openEditConversation = () => {
    if (conversation) {
      setConversationForm({
        friendlyName: conversation.friendlyName || '',
        uniqueName: conversation.uniqueName || '',
        state: conversation.state || 'active',
        attributes: JSON.stringify(conversation.attributes || {}, null, 2)
      });
      setEditConversationModal(true);
    }
  };
  
  const handleUpdateConversation = () => {
    let attributes = {};
    try {
      attributes = JSON.parse(conversationForm.attributes);
    } catch (e) {
      setError('Invalid JSON in attributes field');
      return;
    }
    
    updateConversationMutation.mutate({
      friendlyName: conversationForm.friendlyName.trim() || undefined,
      uniqueName: conversationForm.uniqueName.trim() || undefined,
      state: conversationForm.state,
      attributes
    });
  };
  
  const handleAddParticipant = () => {
    const data = {};
    
    // For chat-only participants, identity is required and no messaging binding
    if (participantForm.bindingType === 'chat') {
      if (!participantForm.identity.trim()) {
        setError('Identity is required for chat-only participants');
        return;
      }
      data.identity = participantForm.identity.trim();
    } else {
      // For messaging participants, address and proxy address are required, no identity
      if (!participantForm.address.trim()) {
        setError('Customer address is required for messaging participants');
        return;
      }
      
      // Add appropriate prefix based on channel type
      let prefix = '';
      switch (participantForm.bindingType) {
        case 'whatsapp':
          prefix = 'whatsapp:';
          break;
        case 'messenger':
          prefix = 'messenger:';
          break;
        case 'gbm':
          prefix = 'gbm:';
          break;
        case 'instagram':
          prefix = 'instagram:';
          break;
        // SMS doesn't need a prefix
        default:
          prefix = '';
      }
      
      data.messagingBindingAddress = prefix + participantForm.address.trim();
      
      // Add proxy address if provided (required for WhatsApp and most OTT channels)
      if (participantForm.proxyAddress.trim()) {
        data.messagingBindingProxyAddress = prefix + participantForm.proxyAddress.trim();
      } else if (['whatsapp', 'messenger', 'gbm', 'instagram'].includes(participantForm.bindingType)) {
        // For OTT channels, proxy address is typically required
        setError(`Twilio Sender Number is required for ${participantForm.bindingType.toUpperCase()} participants`);
        return;
      }
      
      // Optional: Add identity only if provided (some use cases might want both)
      if (participantForm.identity.trim()) {
        data.identity = participantForm.identity.trim();
      }
    }
    
    addParticipantMutation.mutate(data);
  };
  
  const handleSendMessage = () => {
    const data = {
      body: messageForm.body.trim()
    };
    if (messageForm.author.trim()) {
      data.author = messageForm.author.trim();
    }
    sendMessageMutation.mutate(data);
  };
  
  const handleAddWebhook = () => {
    const data = {
      target: webhookForm.target,
      'configuration.url': webhookForm.url.trim(),
      'configuration.method': webhookForm.method
    };
    addWebhookMutation.mutate(data);
  };
  
  const openDeleteModal = (item, type) => {
    setDeleteItemModal({ open: true, item, type });
  };
  
  const handleDelete = () => {
    if (deleteItemModal.item) {
      deleteItemMutation.mutate({ 
        itemId: deleteItemModal.item.sid, 
        type: deleteItemModal.type,
        messageSid: deleteItemModal.item.messageSid // For media deletion
      });
    }
  };
  
  const handleFileSelect = (event) => {
    const files = Array.from(event.target.files);
    setSelectedFiles(files);
  };
  
  const handleUploadMedia = () => {
    if (selectedFiles.length > 0) {
      uploadMediaMutation.mutate(selectedFiles);
    }
  };
  
  const handleExportConversation = () => {
    exportConversationMutation.mutate({ language: conversationLanguage });
  };
  
  
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  const getMediaTypeIcon = (contentType) => {
    if (contentType?.startsWith('image/')) return '🖼️';
    if (contentType?.startsWith('video/')) return '🎥';
    if (contentType?.startsWith('audio/')) return '🎵';
    if (contentType?.includes('pdf')) return '📄';
    return '📎';
  };
  
  const openDeleteMediaModal = (media) => {
    setDeleteItemModal({ 
      open: true, 
      item: media, 
      type: 'media' 
    });
  };
  
  // Debug logging
  if (messagesData) {
    console.log('messagesData structure:', messagesData);
    console.log('messagesData.data:', messagesData.data);
    console.log('messagesData.data?.messages:', messagesData.data?.messages);
  }
  if (participantsData) {
    console.log('participantsData structure:', participantsData);
  }
  if (webhooksData) {
    console.log('webhooksData structure:', webhooksData);
  }
  
  // Debug intelligence data
  if (conversationIntelligenceData) {
    console.log('conversationIntelligenceData:', conversationIntelligenceData);
  }
  if (intelligenceData) {
    console.log('intelligenceData:', intelligenceData);
  }
  
  

  if (!conversation) {
    return (
      <Box>
        <Alert variant="error">
          <Text as="span">Conversation not found</Text>
        </Alert>
      </Box>
    );
  }

  return (
    <Box paddingTop="space60" paddingLeft="space60" paddingRight="space60" paddingBottom="space60">
      {/* Header */}
      <Flex marginBottom="space70" vAlignContent="center" hAlignContent="space-between">
        <Box>
          <Flex vAlignContent="center" marginBottom="space30">
            <Button 
              variant="secondary" 
              size="small" 
              onClick={() => navigate('/conversations')}
              marginRight="space30"
            >
              <ArrowBackIcon decorative />
              Back to Conversations
            </Button>
            <ProductConversationsIcon decorative size="sizeIcon40" color="colorTextBrandHighlight" />
            <Box marginLeft="space30">
              <Heading as="h1" variant="heading10" marginBottom="space0">
                {conversation.friendlyName || conversation.uniqueName || 'Unnamed Conversation'}
              </Heading>
              <Text color="colorTextWeak" fontSize="fontSize30">
                {conversation.sid}
              </Text>
            </Box>
          </Flex>
        </Box>
        <Flex vAlignContent="center" columnGap="space30">
          <Button 
            variant="secondary" 
            onClick={openEditConversation}
          >
            <EditIcon decorative />
            Edit Conversation
          </Button>
          <Badge variant={conversation.state === 'active' ? 'success' : 'neutral'} size="large">
            {conversation.state}
          </Badge>
        </Flex>
      </Flex>

      {/* Conversation Overview Card */}
      <Card marginBottom="space70">
        <Box padding="space40">
          <Heading as="h2" variant="heading20" marginBottom="space30">
            Overview
          </Heading>
          <Flex wrap>
            <Box marginRight="space70" marginBottom="space40">
              <Text color="colorTextWeak" fontSize="fontSize30" marginBottom="space20">
                Friendly Name
              </Text>
              <Text fontWeight="fontWeightSemibold">
                {conversation.friendlyName || 'Not set'}
              </Text>
            </Box>
            <Box marginRight="space70" marginBottom="space40">
              <Text color="colorTextWeak" fontSize="fontSize30" marginBottom="space20">
                Unique Name
              </Text>
              <Text fontWeight="fontWeightSemibold">
                {conversation.uniqueName || 'Not set'}
              </Text>
            </Box>
            <Box marginRight="space70" marginBottom="space40">
              <Text color="colorTextWeak" fontSize="fontSize30" marginBottom="space20">
                Created
              </Text>
              <Text fontWeight="fontWeightSemibold">
                {format(new Date(conversation.dateCreated), 'MMM dd, yyyy HH:mm')}
              </Text>
            </Box>
            <Box marginRight="space70" marginBottom="space40">
              <Text color="colorTextWeak" fontSize="fontSize30" marginBottom="space20">
                Last Updated
              </Text>
              <Text fontWeight="fontWeightSemibold">
                {format(new Date(conversation.dateUpdated), 'MMM dd, yyyy HH:mm')}
              </Text>
            </Box>
          </Flex>
          {conversation.attributes && Object.keys(conversation.attributes).length > 0 && (
            <Box marginTop="space40">
              <Text color="colorTextWeak" fontSize="fontSize30" marginBottom="space20">
                Attributes
              </Text>
              <ContentRenderer 
                content={JSON.stringify(conversation.attributes, null, 2)} 
                type="json" 
              />
            </Box>
          )}
        </Box>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="error" marginBottom="space70">
          <Text as="span">
            <strong>Error:</strong> {error}
          </Text>
        </Alert>
      )}

      {/* Management Tabs */}
      <Card>
        <Box padding="space40">
          <Tabs selectedId={selectedTab} baseId="conversation-management">
            <TabList aria-label="Conversation management tabs">
              <Tab id="participants" onClick={() => setSelectedTab('participants')}>
                <UserIcon decorative />
                Participants
              </Tab>
              <Tab id="messages" onClick={() => setSelectedTab('messages')}>
                <ChatIcon decorative />
                Messages  
              </Tab>
              <Tab id="media" onClick={() => setSelectedTab('media')}>
                <AttachIcon decorative />
                Media
              </Tab>
              <Tab id="webhooks" onClick={() => setSelectedTab('webhooks')}>
                <LinkIcon decorative />
                Webhooks
              </Tab>
              <Tab id="intelligence" onClick={() => setSelectedTab('intelligence')}>
                <DataLineChartIcon decorative />
                Intelligence
              </Tab>
              {shouldShowLiveMonitor() && (
                <Tab id="livemonitor" onClick={() => setSelectedTab('livemonitor')}>
                  <ConnectivityAvailableIcon decorative />
                  Live Monitor
                </Tab>
              )}
              {isVoiceConversation() && (
                <Tab id="transcription" onClick={() => setSelectedTab('transcription')}>
                  <ProductVoiceIcon decorative />
                  Live Transcription
                </Tab>
              )}
            </TabList>
            <TabPanels>
              <TabPanel>
                <Box padding="space40">
                  <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                    <Heading as="h3" variant="heading30">
                      Participants ({participants.length})
                    </Heading>
                    <Button 
                      variant="primary" 
                      size="small" 
                      onClick={() => {
                        setAddParticipantModal(true);
                        setError(null); // Clear any previous errors
                      }}
                    >
                      <PlusIcon decorative />
                      Add Participant
                    </Button>
                  </Flex>
                  
                  {participantsLoading ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Spinner decorative size="sizeIcon30" />
                      <Text marginLeft="space30">Loading participants...</Text>
                    </Flex>
                  ) : participants.length === 0 ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Box textAlign="center">
                        <UserIcon decorative size="sizeIcon70" color="colorTextWeak" />
                        <Text display="block" marginTop="space30" color="colorTextWeak">
                          No participants found
                        </Text>
                      </Box>
                    </Flex>
                  ) : (
                    <Table>
                      <THead>
                        <Tr>
                          <Th>Identity</Th>
                          <Th>Messaging Binding</Th>
                          <Th>Role</Th>
                          <Th>Date Added</Th>
                          <Th width="100px">Actions</Th>
                        </Tr>
                      </THead>
                      <TBody>
                        {participants.map((participant) => (
                          <Tr key={participant.sid}>
                            <Td>
                              <Text fontWeight="fontWeightSemibold">
                                {participant.identity}
                              </Text>
                              <Text fontSize="fontSize30" color="colorTextWeak">
                                {participant.sid}
                              </Text>
                            </Td>
                            <Td>
                              {participant.messagingBinding ? (
                                <Box>
                                  <Text fontSize="fontSize30" fontWeight="fontWeightSemibold">
                                    Customer: {participant.messagingBinding.address}
                                  </Text>
                                  {participant.messagingBinding.proxyAddress && (
                                    <Text fontSize="fontSize30" color="colorTextWeak">
                                      Twilio: {participant.messagingBinding.proxyAddress}
                                    </Text>
                                  )}
                                  {participant.messagingBinding.type && (
                                    <Badge variant="warning" size="small">
                                      {participant.messagingBinding.type}
                                    </Badge>
                                  )}
                                </Box>
                              ) : (
                                <Text fontSize="fontSize30" color="colorTextWeak">
                                  Chat only
                                </Text>
                              )}
                            </Td>
                            <Td>
                              <Badge variant="warning">
                                {participant.roleSid || 'Default'}
                              </Badge>
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {format(new Date(participant.dateCreated), 'MMM dd, HH:mm')}
                              </Text>
                            </Td>
                            <Td>
                              <Button 
                                variant="destructive_secondary" 
                                size="small"
                                onClick={() => openDeleteModal(participant, 'participant')}
                              >
                                <DeleteIcon decorative />
                              </Button>
                            </Td>
                          </Tr>
                        ))}
                      </TBody>
                    </Table>
                  )}
                </Box>
              </TabPanel>
              <TabPanel>
                <Box padding="space40">
                  <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                    <Heading as="h3" variant="heading30">
                      Messages ({messages.length})
                    </Heading>
                    <Button 
                      variant="primary" 
                      size="small" 
                      onClick={() => setSendMessageModal(true)}
                    >
                      <SendIcon decorative />
                      Send Message
                    </Button>
                  </Flex>
                  
                  {messagesLoading ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Spinner decorative size="sizeIcon30" />
                      <Text marginLeft="space30">Loading messages...</Text>
                    </Flex>
                  ) : messages.length === 0 ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Box textAlign="center">
                        <ChatIcon decorative size="sizeIcon70" color="colorTextWeak" />
                        <Text display="block" marginTop="space30" color="colorTextWeak">
                          No messages found
                        </Text>
                      </Box>
                    </Flex>
                  ) : (
                    <Table>
                      <THead>
                        <Tr>
                          <Th>Author</Th>
                          <Th>Message</Th>
                          <Th>Date Sent</Th>
                          <Th>Index</Th>
                          <Th width="100px">Actions</Th>
                        </Tr>
                      </THead>
                      <TBody>
                        {messages.map((message) => (
                          <Tr key={message.sid}>
                            <Td>
                              <Text fontWeight="fontWeightSemibold">
                                {message.author || 'System'}
                              </Text>
                              <Text fontSize="fontSize30" color="colorTextWeak">
                                {message.sid}
                              </Text>
                            </Td>
                            <Td>
                              <Text>
                                {message.body ? (
                                  message.body.length > 100 ? 
                                    `${message.body.substring(0, 100)}...` : 
                                    message.body
                                ) : 'Media message'}
                              </Text>
                              {message.media && message.media.length > 0 && (
                                <Text fontSize="fontSize30" color="colorTextWeak">
                                  📎 {message.media.length} attachment(s)
                                </Text>
                              )}
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {format(new Date(message.dateCreated), 'MMM dd, HH:mm')}
                              </Text>
                            </Td>
                            <Td>
                              <Badge variant="warning">
                                #{message.index}
                              </Badge>
                            </Td>
                            <Td>
                              <Button 
                                variant="destructive_secondary" 
                                size="small"
                                onClick={() => openDeleteModal(message, 'message')}
                              >
                                <DeleteIcon decorative />
                              </Button>
                            </Td>
                          </Tr>
                        ))}
                      </TBody>
                    </Table>
                  )}
                </Box>
              </TabPanel>
              <TabPanel>
                <Box padding="space40">
                  <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                    <Heading as="h3" variant="heading30">
                      Media Files ({allMedia.length})
                    </Heading>
                    <Button 
                      variant="primary" 
                      size="small" 
                      onClick={() => {
                        setUploadMediaModal(true);
                        setError(null);
                      }}
                    >
                      <UploadToCloudIcon decorative />
                      Upload Media
                    </Button>
                  </Flex>
                  
                  <Text color="colorTextWeak" marginBottom="space40">
                    Manage all media files attached to messages in this conversation. Upload new files or view existing attachments.
                  </Text>
                  
                  {mediaLoading ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Spinner decorative size="sizeIcon30" />
                      <Text marginLeft="space30">Loading media files...</Text>
                    </Flex>
                  ) : allMedia.length === 0 ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Box textAlign="center">
                        <FileIcon decorative size="sizeIcon70" color="colorTextWeak" />
                        <Text display="block" marginTop="space30" color="colorTextWeak">
                          No media files found
                        </Text>
                        <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space20">
                          Upload files or send messages with attachments to see them here
                        </Text>
                      </Box>
                    </Flex>
                  ) : (
                    <Table>
                      <THead>
                        <Tr>
                          <Th>File</Th>
                          <Th>Type & Size</Th>
                          <Th>Message Info</Th>
                          <Th>Date</Th>
                          <Th width="120px">Actions</Th>
                        </Tr>
                      </THead>
                      <TBody>
                        {allMedia.map((media) => (
                          <Tr key={media.sid}>
                            <Td>
                              <Flex vAlignContent="center">
                                <Text marginRight="space20" fontSize="fontSize40">
                                  {getMediaTypeIcon(media.contentType)}
                                </Text>
                                <Box>
                                  <Text fontWeight="fontWeightSemibold">
                                    {media.filename || 'Unnamed file'}
                                  </Text>
                                  <Text fontSize="fontSize30" color="colorTextWeak">
                                    {media.sid}
                                  </Text>
                                </Box>
                              </Flex>
                            </Td>
                            <Td>
                              <Box>
                                <Badge variant="warning" size="small">
                                  {media.contentType?.split('/')[1]?.toUpperCase() || 'FILE'}
                                </Badge>
                                <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space10">
                                  {formatFileSize(media.size)}
                                </Text>
                              </Box>
                            </Td>
                            <Td>
                              <Box>
                                <Text fontSize="fontSize30" fontWeight="fontWeightSemibold">
                                  #{media.messageIndex} by {media.messageAuthor || 'System'}
                                </Text>
                                <Text fontSize="fontSize30" color="colorTextWeak">
                                  {media.messageBody ? 
                                    (media.messageBody.length > 50 ? 
                                      `${media.messageBody.substring(0, 50)}...` : 
                                      media.messageBody
                                    ) : 'Media message'
                                  }
                                </Text>
                              </Box>
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {format(new Date(media.dateCreated), 'MMM dd, HH:mm')}
                              </Text>
                            </Td>
                            <Td>
                              <Flex columnGap="space20">
                                <Button 
                                  variant="secondary" 
                                  size="small"
                                  onClick={() => window.open(media.url, '_blank')}
                                >
                                  <DownloadIcon decorative />
                                </Button>
                                <Button 
                                  variant="destructive_secondary" 
                                  size="small"
                                  onClick={() => openDeleteMediaModal(media)}
                                >
                                  <DeleteIcon decorative />
                                </Button>
                              </Flex>
                            </Td>
                          </Tr>
                        ))}
                      </TBody>
                    </Table>
                  )}
                </Box>
              </TabPanel>
              <TabPanel>
                <Box padding="space40">
                  <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                    <Heading as="h3" variant="heading30">
                      Webhooks ({webhooks.length})
                    </Heading>
                    <Button 
                      variant="primary" 
                      size="small" 
                      onClick={() => setAddWebhookModal(true)}
                    >
                      <PlusIcon decorative />
                      Add Webhook
                    </Button>
                  </Flex>
                  
                  {webhooksLoading ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Spinner decorative size="sizeIcon30" />
                      <Text marginLeft="space30">Loading webhooks...</Text>
                    </Flex>
                  ) : webhooks.length === 0 ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="200px">
                      <Box textAlign="center">
                        <LinkIcon decorative size="sizeIcon70" color="colorTextWeak" />
                        <Text display="block" marginTop="space30" color="colorTextWeak">
                          No webhooks configured
                        </Text>
                      </Box>
                    </Flex>
                  ) : (
                    <Table>
                      <THead>
                        <Tr>
                          <Th>Target</Th>
                          <Th>URL</Th>
                          <Th>Method</Th>
                          <Th>Date Created</Th>
                          <Th width="100px">Actions</Th>
                        </Tr>
                      </THead>
                      <TBody>
                        {webhooks.map((webhook) => (
                          <Tr key={webhook.sid}>
                            <Td>
                              <Badge variant="warning">
                                {webhook.target}
                              </Badge>
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {webhook.configuration?.url || 'Not configured'}
                              </Text>
                            </Td>
                            <Td>
                              <Badge variant={webhook.configuration?.method === 'GET' ? 'success' : 'warning'}>
                                {webhook.configuration?.method || 'POST'}
                              </Badge>
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {format(new Date(webhook.dateCreated), 'MMM dd, HH:mm')}
                              </Text>
                            </Td>
                            <Td>
                              <Button 
                                variant="destructive_secondary" 
                                size="small"
                                onClick={() => openDeleteModal(webhook, 'webhook')}
                              >
                                <DeleteIcon decorative />
                              </Button>
                            </Td>
                          </Tr>
                        ))}
                      </TBody>
                    </Table>
                  )}
                </Box>
              </TabPanel>
              <TabPanel>
                <Box padding="space60">
                  <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space60">
                    <Heading as="h3" variant="heading20" color="colorTextBrandHighlight">
                      Conversation Intelligence
                    </Heading>
                    <Flex vAlignContent="center" columnGap="space30">
                      <Button
                        variant="primary"
                        size="small"
                        onClick={handleExportConversation}
                        loading={exportStatus.loading}
                        disabled={!conversationSid}
                      >
                        <DataLineChartIcon decorative />
                        Export for Analysis
                      </Button>
                      <ConnectivityAvailableIcon 
                        decorative 
                        size="sizeIcon30" 
                        color={conversationIntelligenceData || intelligenceData ? 'colorTextIconSuccess' : 'colorTextIconNeutral'} 
                      />
                      <Text fontSize="fontSize40" fontWeight="fontWeightSemibold" color={conversationIntelligenceData || intelligenceData ? 'colorTextSuccess' : 'colorTextNeutral'}>
                        {conversationIntelligenceData || intelligenceData ? 'Data Available' : 'No Data'}
                      </Text>
                    </Flex>
                  </Flex>
                  
                  {/* Export Status Messages */}
                  {exportStatus.success && (
                    <Alert variant="success" marginBottom="space40">
                      <Heading as="h4" variant="heading40" marginBottom="space20">
                        Export Successful
                      </Heading>
                      <Text>{exportStatus.success}</Text>
                      <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space10">
                        Intelligence analysis will be available in a few minutes.
                      </Text>
                    </Alert>
                  )}
                  
                  {exportStatus.error && (
                    <Alert variant="error" marginBottom="space40">
                      <Heading as="h4" variant="heading40" marginBottom="space20">
                        Export Failed
                      </Heading>
                      <Text>{exportStatus.error}</Text>
                    </Alert>
                  )}
                  
                  {exportStatus.loading && (
                    <Alert variant="warning" marginBottom="space40">
                      <Flex vAlignContent="center">
                        <Spinner decorative size="sizeIcon20" marginRight="space30" />
                        <Text>Exporting conversation to Intelligence Service...</Text>
                      </Flex>
                    </Alert>
                  )}
                  
                  {conversationIntelligenceLoading || intelligenceLoading ? (
                    <Flex vAlignContent="center" hAlignContent="center" height="300px">
                      <Spinner decorative size="sizeIcon30" />
                      <Text marginLeft="space30">Loading intelligence data...</Text>
                    </Flex>
                  ) : conversationIntelligenceError ? (
                    <Alert variant="error" marginBottom="space40">
                      <Heading as="h4" variant="heading40" marginBottom="space20">
                        Failed to Load Intelligence Data
                      </Heading>
                      <Text marginBottom="space20">
                        Could not connect to Signal SP Session server to fetch conversation intelligence.
                      </Text>
                      <Text fontSize="fontSize30" color="colorTextWeak">
                        Error: {conversationIntelligenceError?.message || 'Network error'}
                      </Text>
                      <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space10">
                        Make sure the Signal SP Session server is running on owlbank.ngrok.io
                      </Text>
                    </Alert>
                  ) : (
                    <Box>
                      {/* Show data from Signal SP Session (conversation-specific) */}
                      {conversationIntelligenceData?.data ? (
                        <Box>
                          {/* Transcript Section */}
                          {conversationIntelligenceData.data.transcript && (
                            <Box marginBottom="space50">
                              <Heading as="h4" variant="heading40" marginBottom="space30">
                                Transcript
                              </Heading>
                              <Card padding="space30">
                                <Box marginBottom="space20">
                                  <Flex columnGap="space20">
                                    {conversationIntelligenceData.data.transcript.language && (
                                      <Badge variant="warning" size="small">
                                        Language: {conversationIntelligenceData.data.transcript.language}
                                      </Badge>
                                    )}
                                    {conversationIntelligenceData.data.transcript.duration && (
                                      <Badge variant="warning" size="small">
                                        Duration: {conversationIntelligenceData.data.transcript.duration}s
                                      </Badge>
                                    )}
                                    {conversationIntelligenceData.data.transcript.status && (
                                      <Badge variant={conversationIntelligenceData.data.transcript.status === 'completed' ? 'success' : 'warning'} size="small">
                                        Status: {conversationIntelligenceData.data.transcript.status}
                                      </Badge>
                                    )}
                                  </Flex>
                                </Box>
                                <Box maxHeight="500px" overflowY="auto" padding="space20" backgroundColor="colorBackground" borderRadius="borderRadius20">
                                  {conversationIntelligenceData.data.transcript.sentences?.length > 0 ? (
                                    <Box>
                                      {conversationIntelligenceData.data.transcript.sentences.map((sentence, index) => (
                                        <Box 
                                          key={sentence.sid || index} 
                                          marginBottom="space30" 
                                          padding="space30" 
                                          backgroundColor={sentence.speaker === 'customer' || sentence.speaker === 1 ? 'colorBackgroundPrimaryWeakest' : 'colorBackgroundNeutralWeakest'} 
                                          borderRadius="borderRadius30"
                                          borderLeftWidth="borderWidth30"
                                          borderLeftStyle="solid"
                                          borderLeftColor={sentence.speaker === 'customer' || sentence.speaker === 1 ? 'colorBorderPrimary' : 'colorBorderSuccess'}
                                          position="relative"
                                          _before={{
                                            content: '""',
                                            position: 'absolute',
                                            top: '12px',
                                            left: '-6px',
                                            width: '12px',
                                            height: '12px',
                                            borderRadius: '50%',
                                            backgroundColor: sentence.speaker === 'customer' ? 'colorBackgroundPrimary' : 'colorBackgroundSuccess'
                                          }}
                                        >
                                          <Flex vAlignContent="center" marginBottom="space20" wrap>
                                            <Badge 
                                              variant={sentence.speaker === 'customer' || sentence.speaker === 1 ? 'new' : 'success'} 
                                              size="default" 
                                              marginRight="space30"
                                            >
                                              {sentence.speaker === 'customer' || sentence.speaker === 1 ? 'Customer' : 'AI Agent'}
                                            </Badge>
                                            {sentence.start_time !== undefined && sentence.end_time !== undefined && (
                                              <Badge variant="warning" size="small" marginRight="space20">
                                                {sentence.start_time}s - {sentence.end_time}s
                                              </Badge>
                                            )}
                                            {sentence.confidence && (
                                              <Badge 
                                                variant={sentence.confidence > 0.8 ? 'success' : sentence.confidence > 0.6 ? 'warning' : 'error'} 
                                                size="small"
                                              >
                                                {Math.round(sentence.confidence * 100)}% confidence
                                              </Badge>
                                            )}
                                          </Flex>
                                          <Text 
                                            fontSize="fontSize40" 
                                            lineHeight="lineHeight40" 
                                            color="colorText" 
                                            fontWeight={sentence.speaker === 'customer' || sentence.speaker === 1 ? 'fontWeightMedium' : 'fontWeightNormal'}
                                          >
                                            {sentence.text}
                                          </Text>
                                        </Box>
                                      ))}
                                    </Box>
                                  ) : (
                                    <Text color="colorTextWeak">No transcript sentences available</Text>
                                  )}
                                </Box>
                              </Card>
                            </Box>
                          )}
                          
                          {/* Operator Results Section */}
                          {conversationIntelligenceData.data.operator_results?.length > 0 && (
                            <Box marginBottom="space50">
                              <Heading as="h4" variant="heading30" marginBottom="space40" color="colorTextBrandHighlight">
                                Intelligence Analysis Results
                              </Heading>
                              <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(400px, 1fr))" gridGap="space40">
                                {conversationIntelligenceData.data.operator_results.map((result, index) => (
                                  <Card key={result.sid || index} padding="space40">
                                    <Flex vAlignContent="center" marginBottom="space30">
                                      <Badge variant="warning" marginRight="space20" size="large">
                                        {result.operator_type}
                                      </Badge>
                                      <Text fontWeight="fontWeightBold" fontSize="fontSize40">{result.name}</Text>
                                    </Flex>
                                    
                                    {/* Text Generation Results - handle all variations */}
                                    {(result.textGenerationResults || result.text_generation_results || result.text_result) && (
                                      <Box marginBottom="space30">
                                        <Text fontSize="fontSize40" fontWeight="fontWeightBold" marginBottom="space20" color="colorTextBrandHighlight">
                                          Analysis Result
                                        </Text>
                                        <ContentRenderer 
                                          content={
                                            result.textGenerationResults?.result || 
                                            result.text_generation_results?.result || 
                                            result.text_generation_results ||
                                            result.text_result
                                          }
                                          showTypeIndicator={true}
                                        />
                                      </Box>
                                    )}
                                    
                                    {/* Sentiment Classification Results */}
                                    {(result.labelProbabilities || result.label_probabilities) && Object.keys(result.labelProbabilities || result.label_probabilities || {}).length > 0 && (
                                      <Box marginBottom="space30">
                                        <Text fontSize="fontSize40" fontWeight="fontWeightBold" marginBottom="space20" color="colorTextBrandHighlight">
                                          Sentiment Analysis
                                        </Text>
                                        <Flex columnGap="space20" wrap marginBottom="space20">
                                          {Object.entries(result.labelProbabilities || result.label_probabilities).map(([label, probability]) => (
                                            <Badge 
                                              key={label}
                                              variant={label === 'positive' ? 'success' : label === 'negative' ? 'error' : 'warning'} 
                                              size="default"
                                            >
                                              {label}: {Math.round(probability * 100)}%
                                            </Badge>
                                          ))}
                                        </Flex>
                                        {(result.predictedLabel || result.predicted_label) && (
                                          <Text fontSize="fontSize30" marginTop="space10" fontWeight="fontWeightSemibold">
                                            Predicted: {result.predictedLabel || result.predicted_label} 
                                            ({Math.round(((result.predictedProbability || result.predicted_probability) || 0) * 100)}%)
                                          </Text>
                                        )}
                                      </Box>
                                    )}
                                    
                                    {/* Extract Results - handle both camelCase and snake_case */}
                                    {(result.extractResults || result.extract_results) && Object.keys(result.extractResults || result.extract_results || {}).length > 0 && (
                                      <Box marginBottom="space30">
                                        <Text fontSize="fontSize40" fontWeight="fontWeightBold" marginBottom="space30" color="colorTextBrandHighlight">
                                          Extracted Information
                                        </Text>
                                        {typeof (result.extractResults || result.extract_results) === 'object' && (result.extractResults || result.extract_results) !== null ? (
                                          <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(280px, 1fr))" gridGap="space20">
                                            {Object.entries(result.extractResults || result.extract_results).map(([key, value]) => {
                                              if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) return null;
                                              
                                              const displayKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                                              const isImportant = ['sentiment', 'score', 'rating', 'priority', 'status', 'category'].some(term => 
                                                key.toLowerCase().includes(term)
                                              );
                                              
                                              return (
                                                <Card key={key} padding="space30" borderRadius="borderRadius30">
                                                  <Box>
                                                    <Text 
                                                      fontSize="fontSize30" 
                                                      fontWeight="fontWeightBold" 
                                                      color="colorTextBrandHighlight" 
                                                      marginBottom="space20"
                                                    >
                                                      {displayKey}
                                                    </Text>
                                                    {Array.isArray(value) ? (
                                                      <Box>
                                                        {value.map((item, itemIndex) => (
                                                          <Badge 
                                                            key={itemIndex}
                                                            variant={isImportant ? 'success' : 'warning'} 
                                                            size="default"
                                                            marginRight="space10"
                                                            marginBottom="space10"
                                                          >
                                                            {String(item)}
                                                          </Badge>
                                                        ))}
                                                      </Box>
                                                    ) : typeof value === 'object' && value !== null ? (
                                                      <ContentRenderer 
                                                        content={JSON.stringify(value, null, 2)} 
                                                        type="json" 
                                                      />
                                                    ) : (
                                                      <Badge 
                                                        variant={isImportant ? 'success' : 'warning'} 
                                                        size={isImportant ? 'large' : 'default'}
                                                      >
                                                        {String(value)}
                                                      </Badge>
                                                    )}
                                                  </Box>
                                                </Card>
                                              );
                                            })}
                                          </Box>
                                        ) : (
                                          <ContentRenderer 
                                            content={
                                              typeof (result.extractResults || result.extract_results) === 'string' 
                                                ? (result.extractResults || result.extract_results) 
                                                : JSON.stringify((result.extractResults || result.extract_results), null, 2)
                                            } 
                                          />
                                        )}
                                      </Box>
                                    )}
                                    
                                    {result.date_created && (
                                      <Text fontSize="fontSize20" color="colorTextWeak">
                                        Created: {format(new Date(result.date_created), 'MMM dd, yyyy HH:mm')}
                                      </Text>
                                    )}
                                  </Card>
                                ))}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      ) : (
                        /* Fallback to Twilio Intelligence API if available */
                        intelligenceData?.data ? (
                          <Box>
                            {/* Transcript from Twilio Intelligence */}
                            {intelligenceData.data.transcript && (
                              <Box marginBottom="space40">
                                <Heading as="h4" variant="heading40" marginBottom="space30">
                                  Transcript (Twilio Intelligence)
                                </Heading>
                                <Card padding="space30">
                                  <Box maxHeight="300px" overflowY="auto">
                                    {intelligenceData.data.transcript.sentences?.map((sentence, index) => (
                                      <Box key={sentence.sid} marginBottom="space20" padding="space20" backgroundColor={sentence.speaker === 'customer' ? 'colorBackgroundPrimary' : 'colorBackgroundBody'} borderRadius="borderRadius20">
                                        <Flex vAlignContent="center" marginBottom="space10">
                                          <Badge variant={sentence.speaker === 'customer' ? 'success' : 'warning'} size="small" marginRight="space20">
                                            {sentence.speaker === 'customer' ? 'Customer' : 'Agent'}
                                          </Badge>
                                          <Text fontSize="fontSize20" color="colorTextWeak">
                                            {sentence.startTime}s - {sentence.endTime}s
                                          </Text>
                                        </Flex>
                                        <Text>{sentence.text}</Text>
                                      </Box>
                                    )) || (
                                      <Text color="colorTextWeak">No transcript sentences available</Text>
                                    )}
                                  </Box>
                                </Card>
                              </Box>
                            )}
                            
                            {/* Operator Results from Twilio Intelligence */}
                            {intelligenceData.data.operatorResults?.length > 0 && (
                              <Box>
                                <Heading as="h4" variant="heading40" marginBottom="space30">
                                  Analysis Results (Twilio Intelligence)
                                </Heading>
                                <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(300px, 1fr))" gridGap="space30">
                                  {intelligenceData.data.operatorResults.map((result) => (
                                    <Card key={result.sid} padding="space30">
                                      <Flex vAlignContent="center" marginBottom="space20">
                                        <Badge variant="warning" marginRight="space20">
                                          {result.operatorType}
                                        </Badge>
                                        <Text fontWeight="fontWeightSemibold">{result.name}</Text>
                                      </Flex>
                                      
                                      {result.extractResults && (
                                        <Box marginBottom="space20">
                                          <Text fontSize="fontSize30" fontWeight="fontWeightSemibold" marginBottom="space10">
                                            Extracted Data:
                                          </Text>
                                          <ContentRenderer 
                                            content={JSON.stringify(result.extractResults, null, 2)} 
                                            type="json" 
                                          />
                                        </Box>
                                      )}
                                      
                                      {result.predictResults && (
                                        <Box marginBottom="space20">
                                          <Text fontSize="fontSize30" fontWeight="fontWeightSemibold" marginBottom="space10">
                                            Predictions:
                                          </Text>
                                          <ContentRenderer 
                                            content={JSON.stringify(result.predictResults, null, 2)} 
                                            type="json" 
                                          />
                                        </Box>
                                      )}
                                      
                                      <Text fontSize="fontSize20" color="colorTextWeak">
                                        Updated: {format(new Date(result.dateUpdated), 'MMM dd, HH:mm')}
                                      </Text>
                                    </Card>
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        ) : (
                          /* No intelligence data available */
                          <Flex vAlignContent="center" hAlignContent="center" height="300px">
                            <Box textAlign="center">
                              <DataLineChartIcon decorative size="sizeIcon70" color="colorTextWeak" />
                              <Text display="block" marginTop="space30" color="colorTextWeak">
                                No intelligence data available for this conversation
                              </Text>
                              <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space20">
                                Intelligence analysis will appear here once the conversation is processed
                              </Text>
                            </Box>
                          </Flex>
                        )
                      )}
                    </Box>
                  )}
                </Box>
              </TabPanel>
              {shouldShowLiveMonitor() && (
                <TabPanel>
                  <Box padding="space60">
                    <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                      <Heading as="h3" variant="heading20" color="colorTextBrandHighlight">
                        Live Monitor
                      </Heading>
                      <Flex columnGap="space30" vAlignContent="center">
                        <Box>
                          <ConnectivityAvailableIcon 
                            decorative 
                            size="sizeIcon30" 
                            color={isConnectedToLiveMonitor ? 'colorTextIconSuccess' : 'colorTextIconError'} 
                          />
                          <Text 
                            fontSize="fontSize30" 
                            color={isConnectedToLiveMonitor ? 'colorTextSuccess' : 'colorTextError'} 
                            marginLeft="space10"
                          >
                            {isConnectedToLiveMonitor ? 'Live' : 'Disconnected'}
                          </Text>
                        </Box>
                        <Button 
                          variant={isConnectedToLiveMonitor ? 'destructive_secondary' : 'primary'}
                          size="small"
                          onClick={() => {
                            if (isConnectedToLiveMonitor && liveMonitorWebSocket) {
                              liveMonitorWebSocket.close();
                              setLiveMonitorWebSocket(null);
                              setIsConnectedToLiveMonitor(false);
                            } else {
                              // Connect to Dashboard WebSocket for live monitoring
                              const ws = new WebSocket(signalSpApi.getDashboardWebSocketUrl());
                              ws.onopen = () => {
                                setIsConnectedToLiveMonitor(true);
                                setLiveMonitorWebSocket(ws);
                              };
                              ws.onmessage = (event) => {
                                try {
                                  const data = JSON.parse(event.data);
                                  const parsedMessage = parseLogMessage(data);
                                  setLiveMonitorMessages(prev => [...prev, parsedMessage].slice(-100)); // Keep last 100 messages
                                } catch (e) {
                                  // Handle string log messages
                                  const parsedMessage = parseLogMessage(event.data);
                                  setLiveMonitorMessages(prev => [...prev, parsedMessage].slice(-100));
                                }
                              };
                              ws.onclose = () => {
                                setIsConnectedToLiveMonitor(false);
                                setLiveMonitorWebSocket(null);
                              };
                              ws.onerror = (error) => {
                                console.error('Live Monitor WebSocket error:', error);
                                setIsConnectedToLiveMonitor(false);
                              };
                            }
                          }}
                        >
                          {isConnectedToLiveMonitor ? 'Stop Monitor' : 'Start Monitor'}
                        </Button>
                      </Flex>
                    </Flex>
                    
                    <Text color="colorTextWeak" marginBottom="space40" fontSize="fontSize30">
                      Real-time monitoring of conversation processing, transcription, tools usage, and system events.
                    </Text>
                    
                    <Box 
                      ref={liveMonitorScrollRef}
                      height="600px" 
                      backgroundColor="colorBackgroundBody" 
                      borderRadius="borderRadius20" 
                      border="borderStyleSolid"
                      borderWidth="borderWidth10"
                      borderColor="colorBorderNeutralWeak"
                      padding="space20" 
                      overflowY="auto"
                      position="relative"
                    >
                      {liveMonitorMessages.length === 0 ? (
                        <Flex vAlignContent="center" hAlignContent="center" height="100%">
                          <Box textAlign="center">
                            <ConnectivityAvailableIcon decorative size="sizeIcon70" color="colorTextWeak" />
                            <Text display="block" marginTop="space30" color="colorTextWeak" fontSize="fontSize40">
                              {isConnectedToLiveMonitor ? 'Monitoring live conversation...' : 'Connect to start monitoring'}
                            </Text>
                            <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space20">
                              System logs, transcription, and tool usage will appear here in real-time
                            </Text>
                          </Box>
                        </Flex>
                      ) : (
                        <Box paddingBottom="space20">
                          {liveMonitorMessages.map((message, index) => {
                            
                            return (
                              <Box 
                                key={message.id} 
                                marginBottom="space20" 
                                padding="space20" 
                                backgroundColor={message.category === 'customer' ? 'colorBackgroundPrimaryWeakest' : 
                                                 message.category === 'agent' ? 'colorBackgroundSuccessWeakest' :
                                                 message.category === 'error' ? 'colorBackgroundErrorWeakest' :
                                                 'colorBackgroundNeutralWeakest'} 
                                borderRadius="borderRadius20"
                                borderLeftWidth="borderWidth30"
                                borderLeftStyle="solid"
                                borderLeftColor={message.color === 'primary' ? 'colorBorderPrimary' : 
                                               message.color === 'success' ? 'colorBorderSuccess' :
                                               message.color === 'error' ? 'colorBorderError' :
                                               message.color === 'warning' ? 'colorBorderWarning' :
                                               'colorBorderNeutral'}
                              >
                                <Flex vAlignContent="center" marginBottom="space10" wrap>
                                  <Badge 
                                    variant={message.color} 
                                    size="small" 
                                    marginRight="space20"
                                  >
                                    {message.type}
                                  </Badge>
                                  <Text fontSize="fontSize20" color="colorTextWeak">
                                    {format(new Date(message.timestamp), 'HH:mm:ss.SSS')}
                                  </Text>
                                </Flex>
                                <Text 
                                  fontSize="fontSize30" 
                                  lineHeight="lineHeight40"
                                  style={{ whiteSpace: 'pre-wrap' }}
                                >
                                  {message.content}
                                </Text>
                              </Box>
                            );
                          })}
                        </Box>
                      )}
                    </Box>
                  </Box>
                </TabPanel>
              )}
              {isVoiceConversation() && (
                <TabPanel>
                  <Box padding="space40">
                    <Flex vAlignContent="center" hAlignContent="space-between" marginBottom="space40">
                      <Heading as="h3" variant="heading30">
                        Live Transcription
                      </Heading>
                      <Flex columnGap="space30" vAlignContent="center">
                        <Box>
                          <ConnectivityAvailableIcon 
                            decorative 
                            size="sizeIcon20" 
                            color={isConnectedToWebSocket ? 'colorTextIconSuccess' : 'colorTextIconError'} 
                          />
                          <Text fontSize="fontSize30" color={isConnectedToWebSocket ? 'colorTextSuccess' : 'colorTextError'} marginLeft="space10">
                            {isConnectedToWebSocket ? 'Connected' : 'Disconnected'}
                          </Text>
                        </Box>
                        <Button 
                          variant={isConnectedToWebSocket ? 'destructive_secondary' : 'primary'}
                          size="small"
                          onClick={() => {
                            if (isConnectedToWebSocket && webSocket) {
                              webSocket.close();
                              setWebSocket(null);
                              setIsConnectedToWebSocket(false);
                            } else {
                              // Connect to WebSocket
                              const ws = new WebSocket(signalSpApi.getTranscriptionWebSocketUrl());
                              ws.onopen = () => {
                                setIsConnectedToWebSocket(true);
                                setWebSocket(ws);
                              };
                              ws.onmessage = (event) => {
                                try {
                                  const data = JSON.parse(event.data);
                                  if (data.event === 'prompt' || data.type === 'prompt') {
                                    setTranscriptionMessages(prev => [...prev, {
                                      id: Date.now() + Math.random(),
                                      type: 'customer',
                                      text: data.voicePrompt || data.text,
                                      timestamp: new Date().toISOString()
                                    }]);
                                  } else if (data.event === 'tts' || data.type === 'tts') {
                                    setTranscriptionMessages(prev => [...prev, {
                                      id: Date.now() + Math.random(),
                                      type: 'agent',
                                      text: data.text || data.content,
                                      timestamp: new Date().toISOString()
                                    }]);
                                  }
                                } catch (e) {
                                  console.warn('Failed to parse WebSocket message:', e);
                                }
                              };
                              ws.onclose = () => {
                                setIsConnectedToWebSocket(false);
                                setWebSocket(null);
                              };
                              ws.onerror = (error) => {
                                console.error('WebSocket error:', error);
                                setIsConnectedToWebSocket(false);
                              };
                            }
                          }}
                        >
                          {isConnectedToWebSocket ? 'Stop Feed' : 'Start Live Feed'}
                        </Button>
                      </Flex>
                    </Flex>
                    
                    <Box height="500px" backgroundColor="colorBackground" borderRadius="borderRadius20" padding="space30" overflowY="auto">
                      {transcriptionMessages.length === 0 ? (
                        <Flex vAlignContent="center" hAlignContent="center" height="100%">
                          <Box textAlign="center">
                            <ProductVoiceIcon decorative size="sizeIcon70" color="colorTextWeak" />
                            <Text display="block" marginTop="space30" color="colorTextWeak">
                              {isConnectedToWebSocket ? 'Listening for live transcription...' : 'Connect to see live transcription'}
                            </Text>
                            <Text fontSize="fontSize30" color="colorTextWeak" marginTop="space20">
                              Real-time customer and agent conversation will appear here
                            </Text>
                          </Box>
                        </Flex>
                      ) : (
                        <Box>
                          {transcriptionMessages.map((message) => (
                            <Box 
                              key={message.id} 
                              marginBottom="space30" 
                              padding="space20" 
                              backgroundColor={message.type === 'customer' ? 'colorBackgroundPrimary' : 'colorBackgroundBody'} 
                              borderRadius="borderRadius20"
                              borderLeftWidth="borderWidth20"
                              borderLeftStyle="solid"
                              borderLeftColor={message.type === 'customer' ? 'colorBorderPrimary' : 'colorBorderNeutral'}
                            >
                              <Flex vAlignContent="center" marginBottom="space10">
                                <Badge 
                                  variant={message.type === 'customer' ? 'success' : 'neutral'} 
                                  size="small" 
                                  marginRight="space20"
                                >
                                  {message.type === 'customer' ? '🎤 Customer' : '🤖 Agent'}
                                </Badge>
                                <Text fontSize="fontSize20" color="colorTextWeak">
                                  {format(new Date(message.timestamp), 'HH:mm:ss')}
                                </Text>
                              </Flex>
                              <Text>{message.text}</Text>
                            </Box>
                          ))}
                        </Box>
                      )}
                    </Box>
                  </Box>
                </TabPanel>
              )}
            </TabPanels>
          </Tabs>
        </Box>
      </Card>

      {/* Edit Conversation Modal */}
      <Modal
        ariaLabelledby="edit-conversation-modal"
        isOpen={editConversationModal}
        onDismiss={() => setEditConversationModal(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="edit-conversation-modal">
            Edit Conversation
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="edit-friendly-name">Friendly Name</Label>
              <Input
                id="edit-friendly-name"
                type="text"
                value={conversationForm.friendlyName}
                onChange={(e) => setConversationForm(prev => ({ ...prev, friendlyName: e.target.value }))}
              />
            </FormControl>
          </Box>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="edit-unique-name">Unique Name</Label>
              <Input
                id="edit-unique-name"
                type="text"
                value={conversationForm.uniqueName}
                onChange={(e) => setConversationForm(prev => ({ ...prev, uniqueName: e.target.value }))}
              />
            </FormControl>
          </Box>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="edit-state">State</Label>
              <Select
                id="edit-state"
                value={conversationForm.state}
                onChange={(e) => setConversationForm(prev => ({ ...prev, state: e.target.value }))}
              >
                <Option value="active">Active</Option>
                <Option value="inactive">Inactive</Option>
                <Option value="closed">Closed</Option>
              </Select>
            </FormControl>
          </Box>
          <Box>
            <FormControl>
              <Label htmlFor="edit-attributes">Attributes (JSON)</Label>
              <TextArea
                id="edit-attributes"
                value={conversationForm.attributes}
                onChange={(e) => setConversationForm(prev => ({ ...prev, attributes: e.target.value }))}
                rows={4}
              />
            </FormControl>
          </Box>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setEditConversationModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleUpdateConversation}
              loading={updateConversationMutation.isLoading}
            >
              Update Conversation
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Add Participant Modal */}
      <Modal
        ariaLabelledby="add-participant-modal"
        isOpen={addParticipantModal}
        onDismiss={() => setAddParticipantModal(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="add-participant-modal">
            Add Participant
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="participant-identity">
                Identity {participantForm.bindingType === 'chat' ? '(Required)' : '(Optional)'}
              </Label>
              <Input
                id="participant-identity"
                type="text"
                placeholder={participantForm.bindingType === 'chat' ? 'user@example.com' : 'user@example.com (optional)'}
                value={participantForm.identity}
                onChange={(e) => setParticipantForm(prev => ({ ...prev, identity: e.target.value }))}
              />
              <HelpText>
                {participantForm.bindingType === 'chat' 
                  ? 'Required unique identifier for chat-only participants'
                  : 'Optional identifier - messaging participants are identified by their address'
                }
              </HelpText>
            </FormControl>
          </Box>
          
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="binding-type">Binding Type</Label>
              <Select
                id="binding-type"
                value={participantForm.bindingType}
                onChange={(e) => setParticipantForm(prev => ({ ...prev, bindingType: e.target.value }))}
              >
                <Option value="sms">SMS</Option>
                <Option value="whatsapp">WhatsApp</Option>
                <Option value="messenger">Facebook Messenger</Option>
                <Option value="gbm">Google Business Messages</Option>
                <Option value="instagram">Instagram</Option>
                <Option value="chat">Chat only (no SMS/messaging)</Option>
              </Select>
              <HelpText>Channel type for messaging binding</HelpText>
            </FormControl>
          </Box>
          
          {participantForm.bindingType !== 'chat' && (
            <>
              <Box marginBottom="space40">
                <FormControl>
                  <Label htmlFor="participant-address">Customer Address (Required)</Label>
                  <Input
                    id="participant-address"
                    type="text"
                    placeholder={getAddressPlaceholder(participantForm.bindingType)}
                    value={participantForm.address}
                    onChange={(e) => setParticipantForm(prev => ({ ...prev, address: e.target.value }))}
                    required
                  />
                  <HelpText>
                    {getAddressHelpText(participantForm.bindingType)}
                  </HelpText>
                </FormControl>
              </Box>
              
              <Box>
                <FormControl>
                  <Label htmlFor="participant-proxy">
                    Twilio Sender Number {['whatsapp', 'messenger', 'gbm', 'instagram'].includes(participantForm.bindingType) ? '(Required)' : '(Optional)'}
                  </Label>
                  <Input
                    id="participant-proxy"
                    type="text"
                    placeholder={getProxyPlaceholder(participantForm.bindingType)}
                    value={participantForm.proxyAddress}
                    onChange={(e) => setParticipantForm(prev => ({ ...prev, proxyAddress: e.target.value }))}
                    required={['whatsapp', 'messenger', 'gbm', 'instagram'].includes(participantForm.bindingType)}
                  />
                  <HelpText>
                    {getProxyHelpText(participantForm.bindingType)}
                  </HelpText>
                </FormControl>
              </Box>
            </>
          )}
          
          {participantForm.bindingType === 'chat' && (
            <Box marginBottom="space40">
              <HelpText>
                Chat-only participants can only communicate through the conversation interface and cannot receive SMS, WhatsApp, or other messaging channel notifications.
              </HelpText>
            </Box>
          )}
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setAddParticipantModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleAddParticipant}
              loading={addParticipantMutation.isLoading}
            >
              Add Participant
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Send Message Modal */}
      <Modal
        ariaLabelledby="send-message-modal"
        isOpen={sendMessageModal}
        onDismiss={() => setSendMessageModal(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="send-message-modal">
            Send Message
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="message-author">Author (Optional)</Label>
              <Input
                id="message-author"
                type="text"
                placeholder="system"
                value={messageForm.author}
                onChange={(e) => setMessageForm(prev => ({ ...prev, author: e.target.value }))}
              />
              <HelpText>Leave empty for system message</HelpText>
            </FormControl>
          </Box>
          <Box>
            <FormControl>
              <Label htmlFor="message-body">Message</Label>
              <TextArea
                id="message-body"
                placeholder="Type your message here..."
                value={messageForm.body}
                onChange={(e) => setMessageForm(prev => ({ ...prev, body: e.target.value }))}
                rows={4}
              />
            </FormControl>
          </Box>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setSendMessageModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleSendMessage}
              loading={sendMessageMutation.isLoading}
            >
              Send Message
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Add Webhook Modal */}
      <Modal
        ariaLabelledby="add-webhook-modal"
        isOpen={addWebhookModal}
        onDismiss={() => setAddWebhookModal(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="add-webhook-modal">
            Add Webhook
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="webhook-target">Target</Label>
              <Select
                id="webhook-target"
                value={webhookForm.target}
                onChange={(e) => setWebhookForm(prev => ({ ...prev, target: e.target.value }))}
              >
                <Option value="webhook">Webhook</Option>
                <Option value="studio">Studio Flow</Option>
                <Option value="trigger">Trigger</Option>
              </Select>
            </FormControl>
          </Box>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="webhook-url">URL</Label>
              <Input
                id="webhook-url"
                type="url"
                placeholder="https://example.com/webhook"
                value={webhookForm.url}
                onChange={(e) => setWebhookForm(prev => ({ ...prev, url: e.target.value }))}
              />
            </FormControl>
          </Box>
          <Box>
            <FormControl>
              <Label htmlFor="webhook-method">HTTP Method</Label>
              <Select
                id="webhook-method"
                value={webhookForm.method}
                onChange={(e) => setWebhookForm(prev => ({ ...prev, method: e.target.value }))}
              >
                <Option value="POST">POST</Option>
                <Option value="GET">GET</Option>
              </Select>
            </FormControl>
          </Box>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setAddWebhookModal(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleAddWebhook}
              loading={addWebhookMutation.isLoading}
            >
              Add Webhook
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Upload Media Modal */}
      <Modal
        ariaLabelledby="upload-media-modal"
        isOpen={uploadMediaModal}
        onDismiss={() => setUploadMediaModal(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="upload-media-modal">
            Upload Media Files
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space40">
            <FormControl>
              <Label htmlFor="media-upload">Select Files</Label>
              <Input
                id="media-upload"
                type="file"
                multiple
                onChange={handleFileSelect}
                accept="image/*,video/*,audio/*,application/pdf,text/plain"
              />
              <HelpText>
                Supported formats: Images, Videos, Audio, PDF, Text files. Max 50MB per file.
              </HelpText>
            </FormControl>
          </Box>
          
          {selectedFiles.length > 0 && (
            <Box marginBottom="space40">
              <Text fontWeight="fontWeightSemibold" marginBottom="space30">
                Selected Files ({selectedFiles.length}):
              </Text>
              {selectedFiles.map((file, index) => (
                <Flex key={index} vAlignContent="center" marginBottom="space20" padding="space20" backgroundColor="colorBackgroundRowStriped" borderRadius="borderRadius20">
                  <Text marginRight="space20" fontSize="fontSize40">
                    {getMediaTypeIcon(file.type)}
                  </Text>
                  <Box flex="1">
                    <Text fontWeight="fontWeightSemibold">{file.name}</Text>
                    <Text fontSize="fontSize30" color="colorTextWeak">
                      {formatFileSize(file.size)} • {file.type}
                    </Text>
                    {uploadProgress[file.name] && (
                      <Box marginTop="space10">
                        <Text fontSize="fontSize20">Upload Progress: {uploadProgress[file.name]}%</Text>
                        <Box width="100%" height="4px" backgroundColor="colorBackgroundStrong" borderRadius="borderRadius20" marginTop="space10">
                          <Box 
                            width={`${uploadProgress[file.name]}%`} 
                            height="100%" 
                            backgroundColor="colorBorderSuccess" 
                            borderRadius="borderRadius20"
                            transition="width 0.3s ease"
                          />
                        </Box>
                      </Box>
                    )}
                  </Box>
                </Flex>
              ))}
            </Box>
          )}
          
          <Text color="colorTextWeak" fontSize="fontSize30">
            Note: Files will be uploaded to temporary storage for demonstration purposes. In production, files would be stored in cloud storage (AWS S3, Google Cloud, etc.).
          </Text>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button 
              variant="secondary" 
              onClick={() => {
                setUploadMediaModal(false);
                setSelectedFiles([]);
                setUploadProgress({});
              }}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleUploadMedia}
              loading={uploadMediaMutation.isLoading}
              disabled={selectedFiles.length === 0}
            >
              Upload {selectedFiles.length > 0 ? `${selectedFiles.length} File${selectedFiles.length > 1 ? 's' : ''}` : 'Files'}
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        ariaLabelledby="delete-modal"
        isOpen={deleteItemModal.open}
        onDismiss={() => setDeleteItemModal({ open: false, item: null, type: null })}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="delete-modal">
            Delete {deleteItemModal.type}
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Text>
            Are you sure you want to delete this {deleteItemModal.type}?
          </Text>
          <Text marginTop="space30" color="colorTextWeak">
            This action cannot be undone.
          </Text>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button 
              variant="secondary" 
              onClick={() => setDeleteItemModal({ open: false, item: null, type: null })}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              loading={deleteItemMutation.isLoading}
            >
              Delete
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>
    </Box>
  );
};

export default ConversationDetailPage;
