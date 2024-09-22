import React, { useEffect, useState } from 'react';
import { Box, Heading, Spinner, Text } from '@chakra-ui/react';

const AgentsConversation: React.FC = () => {
  const [conversation, setConversation] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/run-agents')  // This triggers the agents in the backend
      .then((response) => response.json())
      .then((data) => {
        setConversation(data.message);  // Display the conversation or outcome
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <Spinner size="xl" />;
  }

  return (
    <Box p={5}>
      <Heading as="h2" size="lg" mb={4}>
        Agent Conversation Outcome
      </Heading>
      <Text>{conversation}</Text>
    </Box>
  );
};

export default AgentsConversation;
