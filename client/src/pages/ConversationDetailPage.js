import React from 'react';
import { Box } from '@twilio-paste/core/box';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';

const ConversationDetailPage = () => {
  return (
    <Box>
      <Heading as="h1" variant="heading10" marginBottom="space30">
        Conversation Details
      </Heading>
      <Text color="colorTextWeak">
        View conversation details - coming soon!
      </Text>
    </Box>
  );
};

export default ConversationDetailPage;
