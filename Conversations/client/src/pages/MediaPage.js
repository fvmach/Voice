import React from 'react';
import { Box } from '@twilio-paste/core/box';
import { Heading } from '@twilio-paste/core/heading';
import { Text } from '@twilio-paste/core/text';

const MediaPage = () => {
  return (
    <Box>
      <Heading as="h1" variant="heading10" marginBottom="space30">
        Media
      </Heading>
      <Text color="colorTextWeak">
        Manage conversation media - coming soon!
      </Text>
    </Box>
  );
};

export default MediaPage;
