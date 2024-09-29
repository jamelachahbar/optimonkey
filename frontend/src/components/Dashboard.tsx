import React, { useState } from 'react';
import {
  Box,
  Heading,
  VStack,
  Button,
  Spinner,
  Flex,
  Text,
  useToast,
  Avatar,
} from '@chakra-ui/react';
import PromptTemplate from './PromptTemplate';

// Define the type for each message in the conversation
interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

// Define the response type from the backend
interface ConversationResponse {
  conversation: Message[];
  error?: string;
}

const Dashboard: React.FC = () => {
  const [loadingAgents, setLoadingAgents] = useState<boolean>(false);
  const [conversation, setConversation] = useState<Message[]>([]);
  const toast = useToast();

  // Function to start agents with default prompt from the backend
  const startAgentsWithDefault = () => {
    setLoadingAgents(true);
    fetch('/api/start-agents', { method: 'POST' })
      .then((response) => response.json())
      .then((data: ConversationResponse) => {
        console.log(data); // Inspect the response
        setLoadingAgents(false);
        if (data.conversation) {
          setConversation(data.conversation); // Update the conversation state
        }
        toast({
          title: "Agents Started",
          description: "Agents have started with the default prompt.",
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      })
      .catch((error) => {
        console.error('Error starting agents:', error);
        setLoadingAgents(false);
        toast({
          title: "Error",
          description: "There was an error starting the agents.",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      });
  };

  // Function to start agents with a specific prompt
  const startAgentsWithPrompt = (prompt: string) => {
    setLoadingAgents(true);
    fetch('/api/start-agents-with-prompt', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt }), // Send the selected prompt
    })
      .then((response) => response.json())
      .then((data: ConversationResponse) => {
        console.log(data); // Inspect the response
        setLoadingAgents(false);
        if (data.conversation) {
          setConversation(data.conversation); // Update the conversation state
        }
        toast({
          title: "Agents Started",
          description: `Agents have started with the prompt: "${prompt}"`,
          status: "success",
          duration: 3000,
          isClosable: true,
        });
      })
      .catch((error) => {
        console.error('Error starting agents with prompt:', error);
        setLoadingAgents(false);
        toast({
          title: "Error",
          description: "There was an error starting the agents.",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      });
  };

  // Handler when a prompt is selected from the card
  const handleSelectPrompt = (prompt: string) => {
    startAgentsWithPrompt(prompt); // Trigger agent start with the selected prompt
  };

  return (
    <Box p={5} height="100vh" display="flex" flexDirection="column">
      <Heading as="h1" size="2xl" mb={6}>
        OptiMonkey Dashboard
      </Heading>

      {/* Button for Starting Agents with Default Prompt */}
      <Button onClick={startAgentsWithDefault} colorScheme="teal" mb={4} disabled={loadingAgents}>
        {loadingAgents ? (
          <>
            <Spinner size="sm" mr={2} /> Running Agents...
          </>
        ) : (
          'Start Agents with Default Prompt'
        )}
      </Button>

      {/* Prompt Template Cards */}
      <PromptTemplate onSelectPrompt={handleSelectPrompt} />

      {/* Show spinner while loading */}
      {loadingAgents && (
        <VStack mt={6}>
          <Spinner size="lg" />
        </VStack>
      )}

      {/* Render the chatbox conversation */}
      <Box
        flex="1"
        overflowY="auto"
        border="1px solid"
        borderColor="gray.300"
        borderRadius="md"
        p={4}
        mt={4}
        bg="gray.50"
      >
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
                <Avatar
                  size="sm"
                  name={msg.name}
                  bg="gray.500"
                  mr={2}
                />
              )}
              <Box>
                <Text fontSize="sm" fontWeight="bold" mb={1}>
                  {msg.name} {msg.timestamp ? `• ${msg.timestamp}` : ''}
                </Text>
                <Text>{msg.content}</Text>
              </Box>
              {msg.role === 'user' && (
                <Avatar
                  size="sm"
                  name={msg.name}
                  bg="gray.500"
                  ml={2}
                />
              )}
            </Flex>
          ))}
        </VStack>
      </Box>
    </Box>
  );
};

export default Dashboard;
