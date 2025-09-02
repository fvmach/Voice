import React from 'react';
import { Box } from '@twilio-paste/core/box';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';

const WebhooksPage = () => {
  return (
    <Box>
      <Heading as="h1" variant="heading10" marginBottom="space30">
        Webhooks
      </Heading>
      <Text color="colorTextWeak">
        Manage conversation webhooks - coming soon!
      </Text>
    </Box>
  );
};

export default WebhooksPage;
