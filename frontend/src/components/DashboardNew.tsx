import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  Flex,
  Avatar,
  Text,
  Input,
  Button,
  useColorModeValue,
} from '@chakra-ui/react';
import ReactMarkdown from 'react-markdown';

// Define the Message interface
interface Message {
  user: string;
  name: string;
  message: string | object; // Content can be a string or an object
  timestamp: string;
  role: string;
}

const DashboardNew: React.FC = () => {
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null); // State for WebSocket connection
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Create WebSocket connection
    const websocket = new WebSocket('ws://localhost:8081/ws/conversation');
    setWs(websocket);

    websocket.onopen = () => {
      console.log("WebSocket connection established.");
    };

    websocket.onmessage = (event) => {
      const messageData = JSON.parse(event.data);
      console.log("Received message from backend:", messageData);

      // Handle the case where content is an object
      if (typeof messageData.content === 'object') {
      } else {
      }

      setMessages((prev) => [...prev, { 
        user: messageData.name, 
        name: messageData.content.name,
        message: messageData.content, 
        timestamp: messageData.timestamp, 
        role: messageData.role 
      }]);
    };

    websocket.onclose = () => {
      console.log("WebSocket connection closed.");
    };

    return () => {
      websocket.close(); // Clean up WebSocket on component unmount
    };
  }, []);

  // Function to scroll to the bottom of the chat
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // Input change handler
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUserInput(e.target.value);
  };

  // Function to send message via WebSocket
  const handleSend = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      const message = JSON.stringify({ message: userInput });
      ws.send(message); // Send message over WebSocket
      setUserInput(''); // Clear input field after sending
    } else {
      console.error('WebSocket is not open');
    }
  };

  return (
    <Flex h="100vh" direction="column">
      <VStack spacing={4} align="stretch" p={6} overflowY="auto">
        {messages.map((msg, index) => (
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
            {msg.name !== 'admin' && (
              <Avatar size="sm" name={msg.name} bg="gray.500" mr={2} />
            )}

            <Box>
              {/* Display the agent's name and the timestamp */}
              <Text fontWeight="bold" mb={2}>
                {msg.name ? `${msg.name}` : 'Agent'} • {msg.timestamp}
              </Text>

              {/* Conditionally render markdown or plain text */}
              <ReactMarkdown>
                {typeof msg.message === 'string' ? msg.message : JSON.stringify(msg.message)}
              </ReactMarkdown>
            </Box>

            {/* Display the user's avatar on the right side for user messages */}
            {msg.role === 'name' && (
              <Avatar size="sm" name={msg.user} bg="gray.500" ml={2} />
            )}
          </Flex>
        ))}
        <div ref={messagesEndRef} />
      </VStack>

      <Box
        display="flex"
        alignItems="center"
        p={4}
        bg={useColorModeValue('gray.100', 'gray.800')}
        borderTop="1px solid"
        borderColor="gray.300"
        width="100%"
      >
        <Input
          type="text"
          value={userInput}
          onChange={handleInputChange}
          placeholder="Type your message..."
          mr={2}
        />
        <Button colorScheme="blue" onClick={handleSend}>
          Send
        </Button>
      </Box>
    </Flex>
  );
};

export default DashboardNew;
