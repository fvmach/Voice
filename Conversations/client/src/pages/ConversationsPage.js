import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Box } from '@twilio-paste/core/box';
import { Flex } from '@twilio-paste/core/flex';
import { Heading } from '@twilio-paste/core/heading';
import { Button } from '@twilio-paste/core/button';
import { Card } from '@twilio-paste/core/card';
import { Text } from '@twilio-paste/core/text';
import { Table, THead, TBody, Tr, Th, Td } from '@twilio-paste/core/table';
import { Modal, ModalHeader, ModalHeading, ModalBody, ModalFooter, ModalFooterActions } from '@twilio-paste/core/modal';
import { Input } from '@twilio-paste/core/input';
import { Label } from '@twilio-paste/core/label';
import { Select, Option } from '@twilio-paste/core/select';
import { FormControl } from '@twilio-paste/core/form';
import { HelpText } from '@twilio-paste/core/help-text';
import { Alert } from '@twilio-paste/core/alert';
import { Spinner } from '@twilio-paste/core/spinner';
import { Badge } from '@twilio-paste/core/badge';
import { PlusIcon } from '@twilio-paste/icons/esm/PlusIcon';
import { DeleteIcon } from '@twilio-paste/icons/esm/DeleteIcon';
import { EditIcon } from '@twilio-paste/icons/esm/EditIcon';
import { ProductConversationsIcon } from '@twilio-paste/icons/esm/ProductConversationsIcon';
import { format } from 'date-fns';
import { conversationsApi, servicesApi } from '../services/api';

const ConversationsPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedService, setSelectedService] = useState('default');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [conversationToDelete, setConversationToDelete] = useState(null);
  const [newConversation, setNewConversation] = useState({
    friendlyName: '',
    uniqueName: '',
    attributes: '{}'
  });
  const [error, setError] = useState(null);

  // Fetch services for the dropdown
  const { data: servicesData } = useQuery(
    'services',
    () => servicesApi.list(),
    { enabled: true }
  );

  // Fetch conversations for the selected service
  const { data: conversationsData, isLoading, error: fetchError } = useQuery(
    ['conversations', selectedService],
    () => conversationsApi.list(selectedService === 'default' ? undefined : selectedService),
    {
      refetchOnMount: true,
    }
  );

  // Create conversation mutation
  const createConversationMutation = useMutation(
    (data) => conversationsApi.create({
      ...data,
      serviceSid: selectedService === 'default' ? undefined : selectedService
    }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['conversations', selectedService]);
        setIsCreateModalOpen(false);
        setNewConversation({ friendlyName: '', uniqueName: '', attributes: '{}' });
        setError(null);
      },
      onError: (error) => {
        setError(error.response?.data?.message || 'Failed to create conversation');
      },
    }
  );

  // Delete conversation mutation
  const deleteConversationMutation = useMutation(
    (conversationSid) => conversationsApi.delete(conversationSid, selectedService === 'default' ? undefined : selectedService),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['conversations', selectedService]);
        setIsDeleteModalOpen(false);
        setConversationToDelete(null);
        setError(null);
      },
      onError: (error) => {
        setError(error.response?.data?.message || 'Failed to delete conversation');
      },
    }
  );

  const handleCreateConversation = () => {
    if (!newConversation.friendlyName.trim() && !newConversation.uniqueName.trim()) {
      setError('Either Friendly Name or Unique Name is required');
      return;
    }

    let attributes = {};
    if (newConversation.attributes.trim()) {
      try {
        attributes = JSON.parse(newConversation.attributes);
      } catch (e) {
        setError('Invalid JSON in attributes field');
        return;
      }
    }

    createConversationMutation.mutate({
      friendlyName: newConversation.friendlyName.trim() || undefined,
      uniqueName: newConversation.uniqueName.trim() || undefined,
      attributes
    });
  };

  const handleDeleteConversation = () => {
    if (conversationToDelete) {
      deleteConversationMutation.mutate(conversationToDelete.sid);
    }
  };

  const openDeleteModal = (conversation) => {
    setConversationToDelete(conversation);
    setIsDeleteModalOpen(true);
  };

  const viewConversation = (conversation) => {
    navigate(`/conversations/${conversation.sid}`);
  };

  const services = servicesData?.data?.services || [];
  const conversations = conversationsData?.data?.conversations || [];
  const allServices = [{ sid: 'default', friendlyName: 'Default Service' }, ...services];

  if (isLoading) {
    return (
      <Flex vAlignContent="center" hAlignContent="center" height="400px">
        <Spinner decorative size="sizeIcon110" />
        <Text marginLeft="space40">Loading conversations...</Text>
      </Flex>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Flex marginBottom="space70" vAlignContent="center" hAlignContent="space-between">
        <Box>
          <Heading as="h1" variant="heading10" marginBottom="space30">
            Conversations
          </Heading>
          <Text color="colorTextWeak">
            Manage conversations across your Twilio Conversation Services. Create, view, and delete conversations with multi-service support.
          </Text>
        </Box>
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
          <PlusIcon decorative />
          Create Conversation
        </Button>
      </Flex>

      {/* Service Selector */}
      <Card marginBottom="space70">
        <Box padding="space40">
          <FormControl>
            <Label htmlFor="service-select">Conversation Service</Label>
            <Select
              id="service-select"
              value={selectedService}
              onChange={(e) => setSelectedService(e.target.value)}
            >
              {allServices.map((service) => (
                <Option key={service.sid} value={service.sid}>
                  {service.friendlyName} {service.sid !== 'default' ? `(${service.sid})` : ''}
                </Option>
              ))}
            </Select>
            <HelpText>
              Select which Conversation Service to manage. Use "Default Service" for conversations in your account's default service, or select a specific service for service-scoped conversations.
            </HelpText>
          </FormControl>
        </Box>
      </Card>

      {/* Error Alert */}
      {(error || fetchError) && (
        <Alert variant="error" marginBottom="space70">
          <Text as="span">
            <strong>Error:</strong> {error || fetchError?.response?.data?.message || fetchError?.message}
          </Text>
        </Alert>
      )}

      {/* Conversations Table */}
      <Card>
        <Table>
          <THead>
            <Tr>
              <Th>Name</Th>
              <Th>SID</Th>
              <Th>State</Th>
              <Th>Service</Th>
              <Th>Created</Th>
              <Th width="160px">Actions</Th>
            </Tr>
          </THead>
          <TBody>
            {conversations.length === 0 ? (
              <Tr>
                <Td colSpan="6">
                  <Flex vAlignContent="center" hAlignContent="center" height="200px">
                    <Box textAlign="center">
                      <ProductConversationsIcon decorative size="sizeIcon70" color="colorTextWeak" />
                      <Text display="block" marginTop="space40" color="colorTextWeak">
                        No conversations found in {allServices.find(s => s.sid === selectedService)?.friendlyName}.
                      </Text>
                      <Text display="block" marginTop="space20" color="colorTextWeak" fontSize="fontSize30">
                        Create your first conversation to get started.
                      </Text>
                    </Box>
                  </Flex>
                </Td>
              </Tr>
            ) : (
              conversations.map((conversation) => (
                <Tr key={conversation.sid}>
                  <Td>
                    <Flex vAlignContent="center">
                      <ProductConversationsIcon decorative size="sizeIcon30" color="colorTextBrandHighlight" />
                      <Box marginLeft="space30">
                        <Text fontWeight="fontWeightSemibold">
                          {conversation.friendlyName || conversation.uniqueName || 'Unnamed Conversation'}
                        </Text>
                        {conversation.friendlyName && conversation.uniqueName && (
                          <Text fontSize="fontSize30" color="colorTextWeak">
                            {conversation.uniqueName}
                          </Text>
                        )}
                      </Box>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge variant="neutral_counter" as="span">
                      {conversation.sid}
                    </Badge>
                  </Td>
                  <Td>
                    <Badge variant={conversation.state === 'active' ? 'success' : 'neutral'}>
                      {conversation.state}
                    </Badge>
                  </Td>
                  <Td>
                    <Text fontSize="fontSize30">
                      {selectedService === 'default' ? 'Default' : allServices.find(s => s.sid === selectedService)?.friendlyName || selectedService}
                    </Text>
                  </Td>
                  <Td>
                    <Text fontSize="fontSize30">
                      {format(new Date(conversation.dateCreated), 'MMM dd, yyyy HH:mm')}
                    </Text>
                  </Td>
                  <Td>
                    <Flex columnGap="space20">
                      <Button 
                        variant="primary" 
                        size="small"
                        onClick={() => viewConversation(conversation)}
                      >
                        <EditIcon decorative />
                        View
                      </Button>
                      <Button 
                        variant="secondary" 
                        size="small"
                        onClick={() => openDeleteModal(conversation)}
                      >
                        <DeleteIcon decorative />
                        Delete
                      </Button>
                    </Flex>
                  </Td>
                </Tr>
              ))
            )}
          </TBody>
        </Table>
      </Card>

      {/* Create Conversation Modal */}
      <Modal
        ariaLabelledby="create-conversation-modal"
        isOpen={isCreateModalOpen}
        onDismiss={() => setIsCreateModalOpen(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="create-conversation-modal">
            Create New Conversation
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Box marginBottom="space70">
            <FormControl>
              <Label htmlFor="friendly-name">Friendly Name</Label>
              <Input
                id="friendly-name"
                type="text"
                placeholder="My Conversation"
                value={newConversation.friendlyName}
                onChange={(e) => setNewConversation(prev => ({ ...prev, friendlyName: e.target.value }))}
              />
              <HelpText>Human-readable name for the conversation</HelpText>
            </FormControl>
          </Box>
          <Box marginBottom="space70">
            <FormControl>
              <Label htmlFor="unique-name">Unique Name (Optional)</Label>
              <Input
                id="unique-name"
                type="text"
                placeholder="my_unique_conversation"
                value={newConversation.uniqueName}
                onChange={(e) => setNewConversation(prev => ({ ...prev, uniqueName: e.target.value }))}
              />
              <HelpText>Unique identifier for programmatic access (no spaces or special characters)</HelpText>
            </FormControl>
          </Box>
          <Box marginBottom="space70">
            <FormControl>
              <Label htmlFor="attributes">Attributes (JSON)</Label>
              <Input
                id="attributes"
                type="text"
                placeholder='{ "topic": "support", "priority": "high" }'
                value={newConversation.attributes}
                onChange={(e) => setNewConversation(prev => ({ ...prev, attributes: e.target.value }))}
              />
              <HelpText>Custom metadata as JSON object</HelpText>
            </FormControl>
          </Box>
          <Box>
            <Text fontSize="fontSize30" color="colorTextWeak">
              Service: <strong>{allServices.find(s => s.sid === selectedService)?.friendlyName}</strong>
            </Text>
          </Box>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleCreateConversation}
              loading={createConversationMutation.isLoading}
            >
              Create Conversation
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        ariaLabelledby="delete-conversation-modal"
        isOpen={isDeleteModalOpen}
        onDismiss={() => setIsDeleteModalOpen(false)}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="delete-conversation-modal">
            Delete Conversation
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Text>
            Are you sure you want to delete the conversation <strong>"{conversationToDelete?.friendlyName || conversationToDelete?.uniqueName}"</strong>?
          </Text>
          <Text marginTop="space30" color="colorTextWeak">
            This action cannot be undone. All messages and participants will be permanently removed.
          </Text>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button variant="secondary" onClick={() => setIsDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteConversation}
              loading={deleteConversationMutation.isLoading}
            >
              Delete Conversation
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>
    </Box>
  );
};

export default ConversationsPage;
