import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  VStack,
  Flex,
  Text,
  IconButton,
  useColorMode,
  useColorModeValue,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon } from '@chakra-ui/icons';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import AgentCard from './AgentCard';
import websocket from '../utils/WebSocket';

interface Message {
  role: string;
  content: string | { confidence_score?: number; explanation?: string; board_decision?: string };
  timestamp: string;
  type?: string;
}

const DashboardAutogen: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userInput, setUserInput] = useState<string>('');
  const { toggleColorMode, colorMode } = useColorMode();
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const bgColor = useColorModeValue('white', 'gray.800');

  const renderCSVContent = (csvText: string) => {
    const rows = csvText.split('\n').map((row) => row.split(','));
    const headers = rows[0];
    const dataRows = rows.slice(1);

    return (
      <Box overflowX="auto">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {headers.map((header, idx) => (
                <th key={idx} style={{ border: '1px solid gray', padding: '8px' }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dataRows.map((row, rowIndex) => (
              <tr key={rowIndex}>
                {row.map((cell, cellIndex) => (
                  <td key={cellIndex} style={{ border: '1px solid gray', padding: '8px' }}>
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Box>
    );
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderMessageContent = (msgContent: any, type: string = 'text') => {
    if (type === 'csv' && typeof msgContent === 'string') {
      return renderCSVContent(msgContent);
    }
  
    if (typeof msgContent === 'string') {
      return <Text>{msgContent}</Text>;
    }
  
    if (msgContent && typeof msgContent === 'object') {
      return (
        <Box>
          {msgContent.confidence_score !== undefined && (
            <Text>Confidence Score: {msgContent.confidence_score}</Text>
          )}
          {msgContent.explanation && <Text>Explanation: {msgContent.explanation}</Text>}
          {msgContent.board_decision && <Text>Board Decision: {msgContent.board_decision}</Text>}
          {msgContent.content && <Text>{msgContent.content}</Text>}
        </Box>
      );
    }
  
    return <Text>{JSON.stringify(msgContent)}</Text>; // Add fallback for unknown message formats
  };
  

  useEffect(() => {
    websocket.onmessage = (event) => {
      const messageData: Message = JSON.parse(event.data);
      console.log("Received message data:", messageData); // Add this line to inspect incoming data
      setMessages((prev) => [...prev, messageData]);
    };
  }, []);
  

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = () => {
    if (websocket.readyState === WebSocket.OPEN && userInput.trim()) {
      websocket.send(JSON.stringify({ message: userInput }));
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: userInput, timestamp: new Date().toLocaleTimeString() },
      ]);
      setUserInput('');
    } else {
      console.error('WebSocket is not open');
    }
  };

  return (
    <Flex h="100vh" direction="column" bg={bgColor}>
      <Box p={4} margin={2}>
        <Text fontSize="xl" fontWeight="bold" textAlign="center">Optimonkey Dashboard</Text>
      </Box>

      <Flex direction="row" flex="1">
        {/* Sidebar with Agent Cards */}
        <VStack
          w="20%"
          p={4}
          spacing={4}
          align="stretch"
          overflowY="auto"
          borderRight="1px solid gray"
        >
          <AgentCard name="Planner" description="Coordinates tasks" />
          <AgentCard name="Coder" description="Writes code for analysis" />
          <AgentCard name="Critic" description="Evaluates code quality" />
          <AgentCard name="User Proxy" description="Interacts with system" />
        </VStack>

        {/* Message Display Area */}
        <VStack w="80%" p={4} overflowY="auto" spacing={4} align="stretch">
          <MessageList messages={messages} renderMessageContent={renderMessageContent} />
          <div ref={messagesEndRef} />
        </VStack>
      </Flex>

      {/* Input and Theme Toggle Section */}
      <Flex p={4} bg={bgColor} borderTop="1px solid gray" alignItems="center">
        <MessageInput
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          onSend={handleSend}
        />
        <IconButton
          aria-label="Toggle dark mode"
          icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
          onClick={toggleColorMode}
          ml={2}
        />
      </Flex>
    </Flex>
  );
};

export default DashboardAutogen;
