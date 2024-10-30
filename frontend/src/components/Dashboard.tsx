import React, { useState, useRef, useEffect } from 'react';
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
import PromptTemplate from './PromptTemplate';
import { CheckCircleIcon, CloseIcon } from '@chakra-ui/icons';

interface Message {
  content: any | { confidence_score: number; explanation: string };
  role: string;
  name: string;
  timestamp?: string;
}

const Dashboard: React.FC = () => {
  const [userMessage, setUserMessage] = useState<string>('');
  const [conversation, setConversation] = useState<Message[]>([]);
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null); // WebSocket state
  const { isOpen } = useDisclosure();  
  const toast = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toggleColorMode, colorMode } = useColorMode();
  const bgColor = useColorModeValue('gray.100', 'gray.800');
  const API_BASE_URL = 'http://localhost:8081/api';
  const [loadingScore, setLoadingScore] = useState<boolean>(true);

  useEffect(() => {
    // Initialize WebSocket connection
    const ws = new WebSocket('ws://localhost:8081/ws/conversation');
    setWebSocket(ws);

    ws.onopen = () => {
      console.log("WebSocket connection established.");
      toast({
        title: 'WebSocket Connected',
        description: 'Connection to the server established.',
        status: 'info',
        duration: 2000,
        isClosable: true,
      });
    };
    ws.onmessage = (event) => {
      const messageData = JSON.parse(event.data);
      // Check if it's a normal message or validation message
      if (messageData.content && typeof messageData.content === 'object' && 'confidence_score' in messageData.content) {
        setLoadingScore(true); // Start spinner for the score
        setTimeout(() => {
          setLoadingScore(false); // Simulate score calculation delay
        }, 2000); // Adjust the delay if necessary
      
        // Validation message, format differently
        const formattedMessage = {
          ...messageData,
          content: `Confidence Score: ${messageData.content.confidence_score}\nExplanation: ${messageData.content.explanation}`,
        };
        setConversation((prev) => [...prev, formattedMessage]);
      } else {
        // Normal message, just add to the conversation
        setConversation((prev) => [...prev, messageData]);
      }
    };


    ws.onclose = () => {
      console.log("WebSocket connection closed.");
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      toast({
        title: 'WebSocket Error',
        description: 'Error occurred in WebSocket connection.',
        status: 'error',
        duration: 2000,
        isClosable: true,
      });
    };

    return () => {
      ws.close(); // Clean up the WebSocket connection on component unmount
    };
  }, []);

  const sendMessage = () => {
    const trimmedMessage = userMessage.trim();
    if (trimmedMessage === '' || !webSocket || webSocket.readyState !== WebSocket.OPEN) return;

    const newMessage = {
      content: trimmedMessage,
      role: 'user',
      name: 'You',
      timestamp: new Date().toLocaleTimeString(),
    };

    // Send message to the WebSocket server
    webSocket.send(JSON.stringify({ message: trimmedMessage }));

    // Update conversation with the new message
    setConversation((prev) => [...prev, newMessage]);
    setUserMessage(''); // Clear input after sending
  };

  // Handle input changes
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserMessage(e.target.value);
  };

  // Send message when pressing "Enter"
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevents newline
      sendMessage();
    }
  };
  const startAgents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/start-agents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
  
      const result = await response.json();
      if (result.status === 'chat_ongoing') {
        toast({
          title: 'Agents Started',
          description: 'Agents have started successfully.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        throw new Error(result.error || 'Failed to start agents');
      }
    } catch (error) {
      console.error('Error starting agents:', error);
      toast({
        title: 'Error',
        description: 'There was an error starting the agents.',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
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
                onClick={startAgents} // Now triggers the startAgents function
                disabled={!webSocket || webSocket.readyState !== WebSocket.OPEN}
              >
                Start Chat
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
                <Flex
                  key={index}
                  alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'}
                  p={3}
                  boxShadow="md"
                  maxWidth="80%"
                  flexDir="row"
                  alignItems="center"
                >
                  {/* Display the avatar for non-user messages */}
                  {msg.role !== 'user' && <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />}
                  
                  <Box>
                    {/* Display the agent's name and the timestamp */}
                    <Text fontWeight="bold" mb={2}>
                      {msg.name ? `${msg.name}` : 'Agent'} • {msg.timestamp}
                    </Text>

                    {/* Conditionally render validation score with spinner */}
                    {msg.content.confidence_score !== undefined ? (
                      <Box>
                        {loadingScore ? (
                          <Flex alignItems="center" mb={2}>
                            <Spinner size="sm" color="blue.500" />
                            <Text ml={2}>Calculating validation score...</Text>
                          </Flex>
                        ) : (
                          <Flex alignItems="center" mb={2}>
                            <Text fontWeight="bold">Confidence Score: {msg.content.confidence_score}</Text>
                            {msg.content.confidence_score === 0 ? (
                              <CloseIcon ml={2} color="red.500" fontSize="xl" />
                            ) : (
                              <CheckCircleIcon ml={2} color="green.500" fontSize="xl" />
                            )}
                          </Flex>
                        )}
                        <Text fontStyle="italic" whiteSpace="pre-wrap">{msg.content.explanation}</Text>
                      </Box>
                    ) : (
                      // Normal message content
                      <Text whiteSpace="pre-wrap">{msg.content}</Text>
                    )}
                  </Box>

                  {/* Display the user's avatar on the right side for user messages */}
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
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            size="md"
            resize="none"
            maxH="200px"
            minH="50px"
            mr={2}
            bg="transparent"
            border="1px solid"
            borderColor={colorMode === 'light' ? 'gray.300' : 'gray.600'}
            disabled={!webSocket || webSocket.readyState !== WebSocket.OPEN}
          />
          <Button colorScheme="teal" onClick={sendMessage} disabled={!webSocket || webSocket.readyState !== WebSocket.OPEN}>
            Send
          </Button>
        </Box>
      </Box>
    </Flex>
  );
};

export default Dashboard;
