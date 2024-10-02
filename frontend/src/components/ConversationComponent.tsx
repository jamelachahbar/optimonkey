// ConversationComponent.tsx
import React from 'react';
import { Box, Text, Flex, Avatar, VStack } from '@chakra-ui/react';

// Define the type for each message in the conversation
interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

interface ConversationComponentProps {
  conversation: Message[];
}

const ConversationComponent: React.FC<ConversationComponentProps> = ({ conversation }) => {
  return (
    <VStack spacing={4} align="stretch">
      {conversation.map((msg, index) => (
        <Flex
          key={index}
          alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'}
          bg={msg.role === 'user' ? 'blue.100' : 'green.100'}
          borderRadius={msg.role === 'user' ? '20px 20px 0 20px' : '20px 20px 20px 0'}
          p={3}
          boxShadow="md"
          maxWidth="80%"
          flexDir="row"
          alignItems="center"
        >
          {msg.role !== 'user' && (
            <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />
          )}
          <Box>
            <Text fontSize="sm" fontWeight="bold" mb={1}>
              {msg.name} {msg.timestamp ? `• ${msg.timestamp}` : ''}
            </Text>
            <Text>{msg.content}</Text>
          </Box>
          {msg.role === 'user' && (
            <Avatar size="sm" name={msg.name} bg="gray.500" ml={2} />
          )}
        </Flex>
      ))}
    </VStack>
  );
};

export default ConversationComponent;
