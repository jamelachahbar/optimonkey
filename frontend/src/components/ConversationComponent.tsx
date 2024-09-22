import React, { useState } from 'react';
import { Box, Button, Text } from '@chakra-ui/react';

const ConversationComponent: React.FC = () => {
  const [conversation, setConversation] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  // Function to trigger the API that runs the agents
  const startAgents = () => {
    setLoading(true);  // Indicate loading state
    fetch('/api/start-agents', { method: 'POST' })  // Trigger backend API
      .then((response) => response.json())
      .then((data) => {
        if (Array.isArray(data.conversation)) {
          setConversation(data.conversation);  // Set the conversation log
        } else {
          setConversation([]);  // Handle unexpected data format
      }})      
      .catch(() => {
        setLoading(false);  // Handle errors and stop loading
      });
  };

  return (
    <Box p={5}>
      <Button onClick={startAgents} colorScheme="teal" mb={4}>
        {loading ? 'Running Agents...' : 'Start Agents'}
      </Button>
      <Box>
        {conversation.map((message, index) => (
          <Text key={index} mb={2}>
            {message}
          </Text>
        ))}
      </Box>
    </Box>
  );
};

export default ConversationComponent;
