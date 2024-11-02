import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  Flex,
  Avatar,
  Text,
  Input,
  Button,
  IconButton,
  SimpleGrid,
  Heading,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/esm/styles/prism';
import PromptTemplate from '../components/PromptTemplate';

interface Message {
  user: string;
  name: string;
  message: string | { confidence_score?: number; explanation?: string; content?: string } | object;
  timestamp: string;
  role: string;
}

const Dashboard: React.FC = () => {
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const { toggleColorMode, colorMode } = useColorMode();
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');
  const cardBgColor = useColorModeValue('white', 'gray.700');
  const textColor = useColorModeValue('blue.500', 'blue.300');
  const codeStyle = colorMode === 'light' ? vs : vscDarkPlus;

  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8081/ws/conversation');
    setWs(websocket);

    websocket.onopen = () => {
        console.log("WebSocket connection established.");
    };

    websocket.onmessage = (event) => {
        const messageData = JSON.parse(event.data);
        console.log("Received message from backend:", messageData);

        // Detect if message content is CSV-like and add a type property
        const isCSV = typeof messageData.content === 'string' && messageData.content.includes(',') && /\n/.test(messageData.content);
        const messageWithType = {
            ...messageData,
            type: isCSV ? 'csv' : 'text'  // Add 'csv' or 'text' type based on content
        };

        setMessages((prev) => [
            ...prev,
            { 
                user: messageWithType.name, 
                name: messageWithType.content.name || 'Agent', 
                message: messageWithType.content, 
                timestamp: messageWithType.timestamp, 
                role: messageWithType.role,
                type: messageWithType.type  // Include the type property
            }
        ]);
    };

    websocket.onclose = () => {
        console.log("WebSocket connection closed.");
    };

    return () => {
        websocket.close();
    };
}, []);


  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUserInput(e.target.value);
  };

  const handleSend = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ message: userInput });
      ws.send(message);
      setMessages((prev) => [
        ...prev,
        {
          user: 'You',
          name: 'You',
          message: userInput,
          timestamp: new Date().toLocaleTimeString(),
          role: 'user'
        }
      ]);
      setUserInput('');
    } else {
      console.error('WebSocket is not open');
    }
  };

  const handlePromptSelection = (prompt: string) => {
    setUserInput(prompt);
  };

  const renderMessageContent = (msgContent: any, role: string, type: string = 'text') => {
    if (role === 'agent' && type === 'csv') {
        // CSV handling remains the same
    }

    // JSON-like content rendering
    if (typeof msgContent === 'string' && msgContent.trim().startsWith('{') && msgContent.trim().endsWith('}')) {
        try {
            const jsonObject = JSON.parse(msgContent);
            return (
                <Box overflowX="auto">
                    <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>
                        {JSON.stringify(jsonObject, null, 2)}
                    </pre>
                </Box>
            );
        } catch (error) {
            return <ReactMarkdown remarkPlugins={[remarkGfm]}>{msgContent}</ReactMarkdown>;
        }
    }

    // Markdown rendering for other plain text content
    if (typeof msgContent === 'string') {
        return <ReactMarkdown remarkPlugins={[remarkGfm]}>{msgContent}</ReactMarkdown>;
    }

    // Object handling for structured agent responses
    if (msgContent && typeof msgContent === 'object') {
        return (
            <Box>
                {msgContent.confidence_score !== undefined && (
                    <Text fontWeight="bold">
                        Confidence Score: {msgContent.confidence_score}
                    </Text>
                )}
                {msgContent.explanation && (
                    <Text fontStyle="italic">Explanation: {msgContent.explanation}</Text>
                )}
                {msgContent.content ? (
                    <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            code({ inline, className, children, ...props }: {
                              inline?: boolean;
                              className?: string;
                              children?: React.ReactNode;
                              [key: string]: any;
                            }) {
                                const match = /language-(\w+)/.exec(className || '');
                                return !inline && match ? (
                                    <SyntaxHighlighter style={codeStyle} language={match[1]} PreTag="div" {...props}>
                                        {String(children).replace(/\n$/, '')}
                                    </SyntaxHighlighter>
                                ) : (
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                );
                            },
                        }}
                    >
                        {msgContent.content}
                    </ReactMarkdown>
                ) : (
                    Object.keys(msgContent).map((key) =>
                        key !== 'confidence_score' && key !== 'explanation' && key !== 'content' ? (
                            <Text key={key}>
                                <strong>{key}:</strong> {JSON.stringify(msgContent[key])}
                            </Text>
                        ) : null
                    )
                )}
            </Box>
        );
    }

    // Render user messages as plain text or Markdown without special formatting
    return typeof msgContent === 'string' ? (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msgContent}</ReactMarkdown>
    ) : (
        <Text>{JSON.stringify(msgContent)}</Text>
    );
};



  

  return (
    <Flex h="100vh" direction="column" bg={bgColor}>
      {/* Prompt Template Section */}
      <Box p={4} margin={2}>
        <Heading as="h3" size="md" textAlign="center" mb={4}>
          Prompt Templates
        </Heading>
        <SimpleGrid columns={{ base: 1, sm: 1, md: 1, lg: 1 }} spacing={6} justifyItems="center">
          <PromptTemplate onSelectPrompt={handlePromptSelection} />
        </SimpleGrid>
      </Box>

      {/* Message Display Section */}
      <VStack spacing={4} align="stretch" p={6} overflowY="auto" flex="1" overflowX="hidden">
        {messages.map((msg, index) => (
          <Flex
            key={index}
            alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'}
            p={4}
            boxShadow="md"
            maxWidth="60%"
            flexDir="column"
            alignItems="flex-start"
            bg={msg.role === 'user' ? 'blue.100' : cardBgColor}
            borderRadius="md"
            overflowWrap="break-word"
          >
            <Flex align="center" mb={2}>
              {msg.role !== 'user' && (
                <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />
              )}
              <Text fontWeight="bold" color={textColor}>
                {msg.name ? `${msg.name}` : 'Agent'} • {msg.timestamp}
              </Text>
            </Flex>
            <Box p={3} bg={bgColor} borderRadius="md" w="full" display="flex" overflowX="auto">
              {renderMessageContent(msg.message, msg.role)}
            </Box>
          </Flex>
        ))}
        <div ref={messagesEndRef} />
      </VStack>

      {/* Input and Theme Toggle Section */}
      <Box
        display="flex"
        alignItems="center"
        p={4}
        bg={bgColor}
        borderTop="1px solid"
        borderColor="gray.300"
      >
        <Input
          width="80%"
          type="text"
          value={userInput}
          onChange={handleInputChange}
          placeholder="Type your message..."
        />
        <Button colorScheme="blue" onClick={handleSend} mr={2}>
          Send
        </Button>
        <IconButton
          aria-label="Toggle dark mode"
          icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
          onClick={toggleColorMode}
        />
      </Box>
    </Flex>
  );
};

export default Dashboard;
