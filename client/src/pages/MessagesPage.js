import React from 'react';
import { Box } from '@twilio-paste/core/box';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';

const MessagesPage = () => {
  return (
    <Box>
      <Heading as="h1" variant="heading10" marginBottom="space30">
        Messages
      </Heading>
      <Text color="colorTextWeak">
        Manage conversation messages - coming soon!
      </Text>
    </Box>
  );
};

export default MessagesPage;
