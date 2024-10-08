import React, { useState, useRef } from 'react';
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
  Textarea,
  useDisclosure,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import PromptTemplate from './PromptTemplate';

interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

const Dashboard: React.FC = () => {
  const [userMessage, setUserMessage] = useState<string>('');
  const [conversation, setConversation] = useState<Message[]>([]);
  const [eventSource, setEventSource] = useState<EventSource | null>(null);
  const { isOpen, onClose } = useDisclosure();
  const toast = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toggleColorMode, colorMode } = useColorMode();
  const bgColor = useColorModeValue('gray.100', 'gray.800');
  const API_BASE_URL = 'http://localhost:8081/api';

  // Helper function to start SSE conversation stream
  const startStreamingConversation = (url: string) => {
    if (eventSource) {
      eventSource.close();
    }

    const source = new EventSource(url);
    setEventSource(source);

    source.onmessage = (event) => {
      try {
        const messageData = JSON.parse(event.data);
        console.log("Received message from backend:", messageData);
        if (messageData.content && messageData.content.toLowerCase().includes('chat ended')) {
          source.close();
          setEventSource(null);  // Clear the EventSource after it closes
        } else {
          setConversation((prev) => [...prev, messageData]);
        }
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
    
    source.onerror = (error) => {
      console.error('Error with SSE:', error);
      source.close();
    };
    
    source.onerror = (error) => {
      console.error('Error with SSE:', error);
      source.close();
    };
  };

  // Mutation to start agents and begin conversation stream
  // Start agents mutation
  const startAgentsMutation = useMutation<void, Error, void>({
    mutationFn: () => axios.post(`/api/start-agents`).then((res) => res.data),
    onMutate: () => {
      toast({
        title: 'Starting agents...',
        status: 'info',
        duration: 2000,
        isClosable: true,
      });
    },
    onSuccess: () => {
      startStreamingConversation('http://localhost:8081/api/stream-conversation');
      toast({
        title: 'Agents Started',
        description: 'Agents have started with the default prompt.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'There was an error starting the agents.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });


  // Mutation to send a message
  const sendMessageMutation = useMutation<void, Error, string>({
    mutationFn: (message: string) => axios.post(`/api/send-message`, { message }).then((res) => res.data),
    onMutate: () => {
      const newMessage: Message = {
        content: userMessage,
        role: 'user',
        name: 'You',
        timestamp: new Date().toLocaleTimeString(),
      };
      setConversation((prev) => [...prev, newMessage]);
    },
    onSuccess: () => {
      setUserMessage(''); // Clear user input after message is sent
    },
    onError: () => {
      
      toast({
        title: 'Error',
        description: 'There was an error sending the message.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    },
  });

  const sendMessage = () => {
    if (userMessage.trim() === '') return;
    sendMessageMutation.mutate(userMessage);
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserMessage(e.target.value);
    e.target.style.height = 'auto'; // Reset textarea height
    e.target.style.height = `${e.target.scrollHeight}px`; // Adjust based on content
  };

  // Handle selection from the prompt template
  const handlePromptSelection = (prompt: string) => {
    setUserMessage(prompt);
    sendMessage(); // Automatically send the selected prompt
  };

  return (
    <Flex h="100vh" direction="column">
      <Flex direction="row" flex="1">
        <Box w={{ base: '20%', md: '15%' }} bg={bgColor} p={4} borderRight="1px solid #e2e8f0">
          <Heading size="sm" mb={6}>Home</Heading>
          <VStack align="stretch" spacing={4}>
            <Button variant="link">Model Catalog</Button>
            <Button variant="link">Model Benchmarks</Button>
            <Button variant="link">Azure OpenAI</Button>
            <Button variant="link">AI Services</Button>
          </VStack>
        </Box>

        <Box w={{ base: '80%', md: '85%' }} p={6} position="relative" flex="1">
          <Flex justifyContent="space-between" alignItems="center" mb={6}>
            <Flex alignItems="center">
              <Button
                mr={4}
                colorScheme="teal"
                onClick={() => startAgentsMutation.mutate()}
                disabled={startAgentsMutation.isLoading}
              >
                {startAgentsMutation.isLoading ? <><Spinner size="sm" mr={2} /> Running Agents...</> : 'Start Agents'}
              </Button>
              <Button onClick={toggleColorMode}>
                {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              </Button>
            </Flex>
            <Heading as="h3" size="lg">OptiMonkey Dashboard</Heading>
          </Flex>

          {!isOpen && (
            <Box mb={6}>
              <PromptTemplate onSelectPrompt={handlePromptSelection} />
            </Box>
          )}

          <Box flex="1" overflowY="auto" p={4} mt={4} maxH="60vh">
            {conversation.length > 0 ? (
              <VStack spacing={4} align="stretch">
                {conversation.map((msg, index) => (
                  <Flex key={index} alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'} p={3} boxShadow="md" maxWidth="80%" flexDir="row" alignItems="center">
                    {msg.role !== 'user' && <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />}
                    <Box>
                      <Text fontWeight="bold">{msg.name} {msg.timestamp ? `• ${msg.timestamp}` : ''}</Text>
                      <Text whiteSpace="pre-wrap">{msg.content}</Text>
                    </Box>
                    {msg.role === 'user' && <Avatar size="sm" name={msg.name} bg="gray.500" ml={2} />}
                  </Flex>
                ))}
              </VStack>
            ) : (
              <Text>No conversation yet</Text>
            )}
          </Box>
        </Box>
      </Flex>

      <Box mt={4} width="100%" display="flex" alignItems="center" position="sticky" bottom={0} left={0} p={4} bg={bgColor}>
        <Box flex="1" maxW="60%" mx="auto" display="flex" alignItems="center">
          <Textarea
            ref={textareaRef}
            value={userMessage}
            onChange={handleTextareaChange}
            placeholder="Type your message..."
            size="md"
            resize="none"
            maxH="200px"
            minH="50px"
            mr={2}
            bg="transparent"
            border="1px solid"
            borderColor={colorMode === 'light' ? 'gray.300' : 'gray.600'}
            disabled={sendMessageMutation.isLoading || startAgentsMutation.isLoading}
          />
          <Button colorScheme="teal" onClick={sendMessage} disabled={sendMessageMutation.isLoading || startAgentsMutation.isLoading}>
            {sendMessageMutation.isLoading ? <Spinner size="sm" /> : 'Send'}
          </Button>
        </Box>
      </Box>
    </Flex>
  );
};

export default Dashboard;