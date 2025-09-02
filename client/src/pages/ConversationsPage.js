import React from 'react';
import { Box } from '@twilio-paste/core/box';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';

const ConversationsPage = () => {
  return (
    <Box>
      <Heading as="h1" variant="heading10" marginBottom="space30">
        Conversations
      </Heading>
      <Text color="colorTextWeak">
        Manage your Twilio Conversations - coming soon!
      </Text>
    </Box>
  );
};

export default ConversationsPage;
