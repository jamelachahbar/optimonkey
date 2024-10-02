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
  Grid,
  useDisclosure,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons'; // Importing icons for color mode
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import PromptTemplate from './PromptTemplate';

// Define the type for each message in the conversation
interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

interface ConversationResponse {
  conversation: Message[];
  error?: string;
}

const Dashboard: React.FC = () => {
  const [userMessage, setUserMessage] = useState<string>('');
  const [conversation, setConversation] = useState<Message[]>([]);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { toggleColorMode, colorMode } = useColorMode(); // Added colorMode here
  const bgColor = useColorModeValue('white', 'gray.800');
  const [isSending, setIsSending] = useState(false); // State to control spinner and textarea disabling

  // React Query - Mutation to start agents with default prompt
  const startAgentsMutation = useMutation<ConversationResponse, Error, void>({
    mutationFn: () => axios.post('/api/start-agents').then((res) => res.data),
    onSuccess: (data) => {
      setConversation(data.conversation);
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

  // React Query - Mutation to send a message
  const sendMessageMutation = useMutation<ConversationResponse, Error, string>({
    mutationFn: (message: string) =>
      axios.post('/api/send-message', { message }).then((res) => res.data),
    onSuccess: (data) => {
      setConversation((prev) => [...prev, ...data.conversation]);
      setIsSending(false); // Re-enable textarea
      onClose(); // Hide the prompt template and start button after sending a message
      toast({
        title: 'Message Sent',
        description: 'Your message was successfully sent to the agents.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: () => {
      setIsSending(false); // Re-enable textarea
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
    const newMessage: Message = {
      content: userMessage,
      role: 'user',
      name: 'You',
      timestamp: new Date().toLocaleTimeString(),
    };
    setConversation((prev) => [...prev, newMessage]);
    setIsSending(true); // Disable textarea and show spinner
    sendMessageMutation.mutate(userMessage);
    setUserMessage('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '48px'; // Reset to initial height
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setUserMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const handlePromptSelection = (prompt: string) => {
    setUserMessage(prompt); // Automatically set the selected prompt into the input box
    sendMessage(); // Send the selected prompt as a message
  };

  return (
    <Flex h="100vh" direction="column">
      {/* Sidebar */}
      <Flex direction="row" flex="1">
        <Box
          w={{ base: '20%', md: '15%' }}
          bg={bgColor}
          p={4}
          display="flex"
          flexDirection="column"
          alignItems="flex-start"
          justifyContent="space-between"
          borderRight="1px solid #e2e8f0"
        >
          <Heading size="sm" mb={6}>
            Home
          </Heading>
          <VStack align="stretch" spacing={4}>
            <Button variant="link">Model Catalog</Button>
            <Button variant="link">Model Benchmarks</Button>
            <Button variant="link">Azure OpenAI</Button>
            <Button variant="link">AI Services</Button>
          </VStack>
        </Box>

        {/* Main Content Area */}
        <Box w={{ base: '80%', md: '85%' }} p={6} position="relative" flex="1">
          <Flex justifyContent="space-between" alignItems="center" mb={6}>
            {/* Start Agents and Color Mode Toggle */}
            <Flex alignItems="center">
              <Button
                mr={4}
                colorScheme="teal"
                onClick={() => startAgentsMutation.mutate()}
                disabled={startAgentsMutation.isPending}
              >
                {startAgentsMutation.isPending ? (
                  <>
                    <Spinner size="sm" mr={2} /> Running Agents...
                  </>
                ) : (
                  'Start Agents'
                )}
              </Button>
              {/* Color Mode Toggle */}
              <Button onClick={toggleColorMode}>
                {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              </Button>
            </Flex>
            <Heading as="h3" size="lg">
              OptiMonkey Dashboard
            </Heading>
          </Flex>

          {/* Cards Section */}
          {!isOpen && (
            <Box mb={6}>
              <PromptTemplate onSelectPrompt={handlePromptSelection} />
            </Box>
          )}

          {/* Conversation and Chatbox */}
          <Box
            flex="1"
            overflowY="auto"
            borderRadius="md"
            p={4}
            mt={4}
            bg="transparent"
            maxH="60vh"
            width="80%"
            mx="auto"
            sx={{
              '::-webkit-scrollbar': { width: '6px' },
              '::-webkit-scrollbar-thumb': { background: '#ccc', borderRadius: '6px' },
            }}
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
                  fontSize="sm"
                >
                  {msg.role !== 'user' && <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />}
                  <Box>
                    <Text fontWeight="bold" mb={1}>
                      {msg.name} {msg.timestamp ? `• ${msg.timestamp}` : ''}
                    </Text>
                    <Text whiteSpace="pre-wrap" wordBreak="break-word">
                      {msg.content}
                    </Text>
                  </Box>
                  {msg.role === 'user' && <Avatar size="sm" name={msg.name} bg="gray.500" ml={2} />}
                </Flex>
              ))}
            </VStack>
          </Box>
        </Box>
      </Flex>

      {/* Input box for sending a message */}
      <Box
        mt={4}
        width="100%"
        display="flex"
        alignItems="center"
        position="fixed"
        bottom={0}
        left={0}
        p={4}
        bg={bgColor}
        boxShadow="md"
      >
        <Box flex="1" maxW="60%" mx="auto" display="flex" alignItems="center">
          <Textarea
            ref={textareaRef}
            value={userMessage}
            onChange={handleTextareaChange}
            placeholder="Type your message..."
            size="md"
            resize="none"
            overflowY="auto"
            maxH={200}
            minH="50px"
            mr={2}
            disabled={isSending} // Disable when sending a message
          />
          <Button
            colorScheme="teal"
            onClick={sendMessage}
            disabled={sendMessageMutation.isPending || isSending}
          >
            {sendMessageMutation.isPending || isSending ? (
              <Spinner size="sm" />
            ) : (
              'Send'
            )}
          </Button>
        </Box>
      </Box>
    </Flex>
  );
};

export default Dashboard;
