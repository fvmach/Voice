import React, { useState } from 'react';
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
import { format } from 'date-fns';
import { conversationsApi, participantsApi, messagesApi, webhooksApi } from '../services/api';

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
  
  // Form states
  const [conversationForm, setConversationForm] = useState({
    friendlyName: '',
    uniqueName: '',
    state: 'active',
    attributes: '{}'
  });
  const [participantForm, setParticipantForm] = useState({ identity: '', messagingBinding: '' });
  const [messageForm, setMessageForm] = useState({ body: '', author: '' });
  const [webhookForm, setWebhookForm] = useState({ target: 'webhook', url: '', method: 'POST' });
  
  const [error, setError] = useState(null);

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
      enabled: !!conversationSid && selectedTab === 'messages',
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
        setParticipantForm({ identity: '', messagingBinding: '' });
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
    ({ itemId, type }) => {
      switch (type) {
        case 'participant':
          return participantsApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        case 'message':
          return messagesApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        case 'webhook':
          return webhooksApi.delete(conversationSid, itemId, serviceSid ? { serviceSid } : {});
        default:
          throw new Error('Unknown delete type');
      }
    },
    {
      onSuccess: (_, variables) => {
        queryClient.invalidateQueries([variables.type + 's', conversationSid]);
        setDeleteItemModal({ open: false, item: null, type: null });
        setError(null);
      },
      onError: (error) => setError(error.response?.data?.message || 'Failed to delete item')
    }
  );

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

  const conversation = conversationData?.data;
  
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
    const data = {
      identity: participantForm.identity.trim()
    };
    if (participantForm.messagingBinding.trim()) {
      data['messaging_binding.address'] = participantForm.messagingBinding.trim();
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
        type: deleteItemModal.type 
      });
    }
  };
  
  // Data extraction
  const participants = participantsData?.data?.participants || [];
  const messages = messagesData?.data?.messages || [];
  const webhooks = webhooksData?.data?.webhooks || [];

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
    <Box>
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
              <Text color="colorTextWeak">
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
          <Badge variant={conversation.state === 'active' ? 'success' : 'neutral'}>
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
              <Box backgroundColor="colorBackgroundRowStriped" padding="space20" borderRadius="borderRadius20">
                <Text fontFamily="fontFamilyCode" fontSize="fontSize30">
                  {JSON.stringify(conversation.attributes, null, 2)}
                </Text>
              </Box>
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
                      onClick={() => setAddParticipantModal(true)}
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
                                <Text fontSize="fontSize30">
                                  {participant.messagingBinding.address}
                                </Text>
                              ) : (
                                <Text fontSize="fontSize30" color="colorTextWeak">
                                  None
                                </Text>
                              )}
                            </Td>
                            <Td>
                              <Badge variant="neutral">
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
                              <Badge variant="neutral">
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
                  <Heading as="h3" variant="heading30" marginBottom="space30">
                    Media Management
                  </Heading>
                  <Text color="colorTextWeak" marginBottom="space40">
                    Media files are attached to messages. View message attachments in the Messages tab above.
                  </Text>
                  <Flex vAlignContent="center" hAlignContent="center" height="200px">
                    <Box textAlign="center">
                      <AttachIcon decorative size="sizeIcon70" color="colorTextWeak" />
                      <Text display="block" marginTop="space30" color="colorTextWeak">
                        Media management coming soon
                      </Text>
                      <Text fontSize="fontSize30" color="colorTextWeak">
                        Upload and manage media through message sending
                      </Text>
                    </Box>
                  </Flex>
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
                              <Badge variant="neutral">
                                {webhook.target}
                              </Badge>
                            </Td>
                            <Td>
                              <Text fontSize="fontSize30">
                                {webhook.configuration?.url || 'Not configured'}
                              </Text>
                            </Td>
                            <Td>
                              <Badge variant={webhook.configuration?.method === 'GET' ? 'success' : 'neutral'}>
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
              <Label htmlFor="participant-identity">Identity</Label>
              <Input
                id="participant-identity"
                type="text"
                placeholder="user@example.com"
                value={participantForm.identity}
                onChange={(e) => setParticipantForm(prev => ({ ...prev, identity: e.target.value }))}
              />
              <HelpText>Unique identifier for the participant</HelpText>
            </FormControl>
          </Box>
          <Box>
            <FormControl>
              <Label htmlFor="participant-binding">Messaging Binding (Optional)</Label>
              <Input
                id="participant-binding"
                type="text"
                placeholder="+1234567890"
                value={participantForm.messagingBinding}
                onChange={(e) => setParticipantForm(prev => ({ ...prev, messagingBinding: e.target.value }))}
              />
              <HelpText>Phone number or address for SMS/WhatsApp binding</HelpText>
            </FormControl>
          </Box>
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
