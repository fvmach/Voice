import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Box } from '@twilio-paste/core/box';
import { Flex } from '@twilio-paste/core/flex';
import { Heading } from '@twilio-paste/core/heading';
import { Button } from '@twilio-paste/core/button';
import { Text } from '@twilio-paste/core/text';
import { Sidebar } from '@twilio-paste/core/sidebar';
import { SidebarNavigation } from '@twilio-paste/core/sidebar';
import { SidebarNavigationItem } from '@twilio-paste/core/sidebar';
import { TopbarActions } from '@twilio-paste/core/topbar';
import { Topbar } from '@twilio-paste/core/topbar';
import { Alert } from '@twilio-paste/core/alert';
import { Spinner } from '@twilio-paste/core/spinner';
import { ProductConversationsIcon } from '@twilio-paste/icons/esm/ProductConversationsIcon';
import { ServiceIcon } from '@twilio-paste/icons/esm/ServiceIcon';
import { UserIcon } from '@twilio-paste/icons/esm/UserIcon';
import { ChatIcon } from '@twilio-paste/icons/esm/ChatIcon';
import { AttachIcon } from '@twilio-paste/icons/esm/AttachIcon';
import { WebhookIcon } from '@twilio-paste/icons/esm/WebhookIcon';
import { useQuery } from 'react-query';
import { healthApi } from '../services/api';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [selectedService, setSelectedService] = useState('default');
  
  // Health check
  const { data: health, isLoading: healthLoading, error: healthError } = useQuery(
    'health',
    healthApi.check,
    {
      refetchInterval: 30000, // Check every 30 seconds
      retry: 3,
    }
  );

  const navigationItems = [
    {
      href: '/services',
      icon: ServiceIcon,
      label: 'Services',
      selected: location.pathname === '/services',
    },
    {
      href: '/conversations',
      icon: ProductConversationsIcon,
      label: 'Conversations',
      selected: location.pathname.startsWith('/conversations'),
    },
  ];

  const handleNavigation = (href) => {
    navigate(href);
  };

  const handleServiceChange = (serviceSid) => {
    setSelectedService(serviceSid);
    // You can add logic here to filter content by service
  };

  return (
    <Box minHeight="100vh" backgroundColor="colorBackgroundBody">
      {/* Topbar */}
      <Topbar>
        <Flex vAlignContent="center" hAlignContent="space-between" width="100%">
          <Flex vAlignContent="center">
            <ProductConversationsIcon decorative size="sizeIcon40" color="colorTextBrandHighlight" />
            <Heading as="h1" variant="heading20" marginLeft="space30" marginBottom="space0">
              Twilio Conversations Manager
            </Heading>
          </Flex>
          <TopbarActions>
            <Flex vAlignContent="center" columnGap="space30">
              {healthLoading && <Spinner decorative size="sizeIcon20" />}
              {health && (
                <Text as="span" color="colorTextSuccess" fontSize="fontSize20">
                  ● {health.data?.status || 'Connected'}
                </Text>
              )}
              {healthError && (
                <Text as="span" color="colorTextError" fontSize="fontSize20">
                  ● Disconnected
                </Text>
              )}
            </Flex>
          </TopbarActions>
        </Flex>
      </Topbar>

      <Flex>
        {/* Sidebar */}
        <Sidebar collapsed={false} variant="default">
          <Box padding="space40">
            <Text as="div" color="colorTextWeak" fontSize="fontSize20" marginBottom="space30">
              Navigation
            </Text>
            <SidebarNavigation aria-label="Main navigation">
              {navigationItems.map((item) => (
                <SidebarNavigationItem
                  key={item.href}
                  href={item.href}
                  icon={<item.icon decorative />}
                  selected={item.selected}
                  onClick={(e) => {
                    e.preventDefault();
                    handleNavigation(item.href);
                  }}
                >
                  {item.label}
                </SidebarNavigationItem>
              ))}
            </SidebarNavigation>
          </Box>
        </Sidebar>

        {/* Main Content */}
        <Box flex={1} padding="space60" minHeight="calc(100vh - 60px)">
          {healthError && (
            <Alert variant="error" marginBottom="space40">
              <Text as="span">
                <strong>Connection Error:</strong> Unable to connect to the backend API. Please check if the server is running.
              </Text>
            </Alert>
          )}
          {children}
        </Box>
      </Flex>
    </Box>
  );
};

export default Layout;
