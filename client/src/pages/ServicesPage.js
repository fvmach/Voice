import React, { useState } from 'react';
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
import { FormControl } from '@twilio-paste/core/form';
import { HelpText } from '@twilio-paste/core/help-text';
import { Alert } from '@twilio-paste/core/alert';
import { Spinner } from '@twilio-paste/core/spinner';
import { Badge } from '@twilio-paste/core/badge';
import { PlusIcon } from '@twilio-paste/icons/esm/PlusIcon';
import { DeleteIcon } from '@twilio-paste/icons/esm/DeleteIcon';
import { EditIcon } from '@twilio-paste/icons/esm/EditIcon';
import { ServiceIcon } from '@twilio-paste/icons/esm/ServiceIcon';
import { format } from 'date-fns';
import { servicesApi } from '../services/api';

const ServicesPage = () => {
  const queryClient = useQueryClient();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [serviceToDelete, setServiceToDelete] = useState(null);
  const [newServiceName, setNewServiceName] = useState('');
  const [error, setError] = useState(null);

  // Fetch services
  const { data: servicesData, isLoading, error: fetchError, refetch } = useQuery(
    'services',
    () => servicesApi.list(),
    {
      refetchOnMount: true,
    }
  );

  // Create service mutation
  const createServiceMutation = useMutation(
    (data) => servicesApi.create(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('services');
        setIsCreateModalOpen(false);
        setNewServiceName('');
        setError(null);
      },
      onError: (error) => {
        setError(error.response?.data?.message || 'Failed to create service');
      },
    }
  );

  // Delete service mutation
  const deleteServiceMutation = useMutation(
    (serviceSid) => servicesApi.delete(serviceSid),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('services');
        setIsDeleteModalOpen(false);
        setServiceToDelete(null);
        setError(null);
      },
      onError: (error) => {
        setError(error.response?.data?.message || 'Failed to delete service');
      },
    }
  );

  const handleCreateService = () => {
    if (!newServiceName.trim()) {
      setError('Service name is required');
      return;
    }

    createServiceMutation.mutate({
      friendlyName: newServiceName.trim()
    });
  };

  const handleDeleteService = () => {
    if (serviceToDelete) {
      deleteServiceMutation.mutate(serviceToDelete.sid);
    }
  };

  const openDeleteModal = (service) => {
    setServiceToDelete(service);
    setIsDeleteModalOpen(true);
  };

  const services = servicesData?.data?.services || [];

  if (isLoading) {
    return (
      <Flex vAlignContent="center" hAlignContent="center" height="400px">
        <Spinner decorative size="sizeIcon110" />
        <Text marginLeft="space40">Loading services...</Text>
      </Flex>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Flex marginBottom="space70" vAlignContent="center" hAlignContent="space-between">
        <Box>
          <Heading as="h1" variant="heading10" marginBottom="space30">
            Conversation Services
          </Heading>
          <Text color="colorTextWeak">
            Manage your Twilio Conversation Services. Services allow you to create multiple environments under a single Twilio account.
          </Text>
        </Box>
        <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
          <PlusIcon decorative />
          Create Service
        </Button>
      </Flex>

      {/* Error Alert */}
      {(error || fetchError) && (
        <Alert variant="error" marginBottom="space70">
          <Text as="span">
            <strong>Error:</strong> {error || fetchError?.response?.data?.message || fetchError?.message}
          </Text>
        </Alert>
      )}

      {/* Services Table */}
      <Card>
        <Table>
          <THead>
            <Tr>
              <Th>Service Name</Th>
              <Th>SID</Th>
              <Th>Created</Th>
              <Th>Updated</Th>
              <Th width="120px">Actions</Th>
            </Tr>
          </THead>
          <TBody>
            {services.length === 0 ? (
              <Tr>
                <Td colSpan="5">
                  <Flex vAlignContent="center" hAlignContent="center" height="200px">
                    <Box textAlign="center">
                      <ServiceIcon decorative size="sizeIcon70" color="colorTextWeak" />
                      <Text display="block" marginTop="space40" color="colorTextWeak">
                        No services found. Create your first service to get started.
                      </Text>
                    </Box>
                  </Flex>
                </Td>
              </Tr>
            ) : (
              services.map((service) => (
                <Tr key={service.sid}>
                  <Td>
                    <Flex vAlignContent="center">
                      <ServiceIcon decorative size="sizeIcon30" color="colorTextBrandHighlight" />
                      <Text marginLeft="space30" fontWeight="fontWeightSemibold">
                        {service.friendlyName}
                      </Text>
                    </Flex>
                  </Td>
                  <Td>
                    <Badge variant="neutral_counter" as="span">
                      {service.sid}
                    </Badge>
                  </Td>
                  <Td>
                    <Text fontSize="fontSize30">
                      {format(new Date(service.dateCreated), 'MMM dd, yyyy HH:mm')}
                    </Text>
                  </Td>
                  <Td>
                    <Text fontSize="fontSize30">
                      {format(new Date(service.dateUpdated), 'MMM dd, yyyy HH:mm')}
                    </Text>
                  </Td>
                  <Td>
                    <Flex columnGap="space20">
                      <Button 
                        variant="secondary" 
                        size="small"
                        onClick={() => openDeleteModal(service)}
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

      {/* Create Service Modal */}
      <Modal 
        ariaLabelledby="create-service-modal-heading"
        isOpen={isCreateModalOpen}
        onDismiss={() => {
          setIsCreateModalOpen(false);
          setNewServiceName('');
          setError(null);
        }}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="create-service-modal-heading">
            Create New Service
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <FormControl>
            <Label htmlFor="service-name" required>
              Service Name
            </Label>
            <Input
              id="service-name"
              value={newServiceName}
              onChange={(e) => {
                setNewServiceName(e.target.value);
                if (error) setError(null);
              }}
              placeholder="Enter a friendly name for your service"
              hasError={!!error}
            />
            <HelpText>
              Choose a descriptive name for your Conversation Service (e.g., "Production", "Development", "Customer Support").
            </HelpText>
          </FormControl>
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button 
              variant="secondary" 
              onClick={() => {
                setIsCreateModalOpen(false);
                setNewServiceName('');
                setError(null);
              }}
            >
              Cancel
            </Button>
            <Button 
              variant="primary" 
              onClick={handleCreateService}
              loading={createServiceMutation.isLoading}
            >
              Create Service
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>

      {/* Delete Service Modal */}
      <Modal 
        ariaLabelledby="delete-service-modal-heading"
        isOpen={isDeleteModalOpen}
        onDismiss={() => {
          setIsDeleteModalOpen(false);
          setServiceToDelete(null);
          setError(null);
        }}
        size="default"
      >
        <ModalHeader>
          <ModalHeading as="h3" id="delete-service-modal-heading">
            Delete Service
          </ModalHeading>
        </ModalHeader>
        <ModalBody>
          <Text>
            Are you sure you want to delete the service "{serviceToDelete?.friendlyName}"? 
            This action cannot be undone and will delete all conversations, messages, and participants within this service.
          </Text>
          {serviceToDelete && (
            <Box marginTop="space40" padding="space40" backgroundColor="colorBackgroundErrorWeakest" borderRadius="borderRadius20">
              <Text fontSize="fontSize30" color="colorTextWeak">
                Service SID: <strong>{serviceToDelete.sid}</strong>
              </Text>
            </Box>
          )}
        </ModalBody>
        <ModalFooter>
          <ModalFooterActions>
            <Button 
              variant="secondary" 
              onClick={() => {
                setIsDeleteModalOpen(false);
                setServiceToDelete(null);
                setError(null);
              }}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteService}
              loading={deleteServiceMutation.isLoading}
            >
              Delete Service
            </Button>
          </ModalFooterActions>
        </ModalFooter>
      </Modal>
    </Box>
  );
};

export default ServicesPage;
