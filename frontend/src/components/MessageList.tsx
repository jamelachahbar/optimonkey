import React from 'react';
import { VStack, Box, Text } from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Message {
  role: string;
  content: string | { confidence_score?: number; explanation?: string; board_decision?: string };
  timestamp: string;
  type?: string;
}

interface MessageListProps {
  messages: Message[];
  renderMessageContent: (msgContent: any, type?: string) => React.ReactElement;
}

const MessageList: React.FC<MessageListProps> = ({ messages, renderMessageContent }) => (
  <VStack align="stretch" spacing={4}>
    {messages.map((msg, index) => (
      <Box
        key={index}
        p={4}
        shadow="md"
        bg={msg.role === 'user' ? 'blue.100' : 'gray.200'}
        borderRadius="md"
      >
        <Text fontWeight="bold">{msg.role}</Text>
        {/* Use the renderMessageContent function */}
        {renderMessageContent(msg.content, msg.type)}
        <Text fontSize="xs" color="gray.500">{msg.timestamp}</Text>
      </Box>
    ))}
  </VStack>
);

export default MessageList;
