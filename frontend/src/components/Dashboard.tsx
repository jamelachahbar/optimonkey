import React, { useState } from 'react';
import {
  Box,
  Button,
  Heading,
  VStack,
  Text,
  Avatar,
  Spinner,
  Flex,
  useColorModeValue,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
} from '@chakra-ui/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import Papa from 'papaparse';
import twemoji from 'twemoji';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faRobot } from '@fortawesome/free-solid-svg-icons';

interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

const Dashboard: React.FC = () => {
  const [conversation, setConversation] = useState<Message[]>([]);
  const [data, setData] = useState<any[]>([]);  // CSV data
  const [headers, setHeaders] = useState<string[]>([]);  // CSV headers
  const [loadingAgents, setLoadingAgents] = useState(false);  // Loading for Start Agents
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);  // Loading for Show Recommendations
  const [showRecommendations, setShowRecommendations] = useState(false);

  const startAgents = () => {
    setLoadingAgents(true);  // Set agents loading state
    fetch('/api/start-agents', { method: 'POST' })
      .then((response) => response.json())
      .then((data) => {
        if (Array.isArray(data.conversation)) {
          setConversation(data.conversation);
        }
        setLoadingAgents(false);  // Stop loading after agents finish
      })
      .catch(() => {
        setLoadingAgents(false);
      });
  };

  const fetchRecommendations = async () => {
    setLoadingRecommendations(true);  // Set recommendations loading state
    try {
      const response = await fetch('/api/download-recommendations');
      const csvText = await response.text();

      // Parse CSV data
      Papa.parse(csvText, {
        header: true,
        complete: (result) => {
          const parsedData = result.data;
          if (parsedData.length > 0) {
            setHeaders(Object.keys(parsedData[0]));
          }
          setData(parsedData);
          setLoadingRecommendations(false);  // Stop loading after fetching data
          setShowRecommendations(true);
        },
        error: (error) => {
          console.error('Error parsing CSV:', error);
          setLoadingRecommendations(false);
        }
      });
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      setLoadingRecommendations(false);
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    const bgColor = useColorModeValue(isUser ? 'blue.100' : 'green.100', isUser ? 'blue.700' : 'green.700');
    const alignSelf = isUser ? 'flex-end' : 'flex-start';
    const borderRadius = isUser ? '20px 20px 0px 20px' : '20px 20px 20px 0px';

    const codeBlockRegex = /```(.*?)\n([\s\S]*?)```/g;

    let contentElements: (string | JSX.Element)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(message.content)) !== null) {
      const [fullMatch, language, code] = match;
      const indexBeforeCode = match.index;
      const indexAfterCode = codeBlockRegex.lastIndex;

      if (indexBeforeCode > lastIndex) {
        contentElements.push(message.content.substring(lastIndex, indexBeforeCode));
      }

      contentElements.push(
        <SyntaxHighlighter
          language={language || 'python'}
          style={dracula}
          customStyle={{ borderRadius: '8px', margin: '8px 0' }}
        >
          {code}
        </SyntaxHighlighter>
      );

      lastIndex = indexAfterCode;
    }

    if (lastIndex < message.content.length) {
      contentElements.push(message.content.substring(lastIndex));
    }

    if (contentElements.length === 0) {
      contentElements = [message.content];
    }

    const agentAvatars: { [key: string]: string | JSX.Element } = {
      Planner: '📝',
      Code_Guru: '💻',
      Critic: '🔍',
      user_proxy: '👤',
      default: <FontAwesomeIcon icon={faRobot} />,
    };

    const agentAvatar = agentAvatars[message.name] || agentAvatars['default'];

    return (
      <Flex key={index} alignSelf={alignSelf} my={2} maxWidth="80%">
        {!isUser && (
          <Avatar
            name={message.name}
            bg="gray.500"
            icon={<span dangerouslySetInnerHTML={{ __html: twemoji.parse(agentAvatar) }} />}
            mr={2}
          />
        )}
        <Box bg={bgColor} p={3} borderRadius={borderRadius} boxShadow="md" flex="1">
          <Text fontSize="sm" fontWeight="bold" mb={1}>
            {message.name} {message.timestamp && `• ${message.timestamp}`}
          </Text>
          <Text>
            {contentElements.map((element, idx) => (
              <React.Fragment key={idx}>{element}</React.Fragment>
            ))}
          </Text>
        </Box>
        {isUser && (
          <Avatar
            name={message.name}
            bg="gray.500"
            icon={<span dangerouslySetInnerHTML={{ __html: twemoji.parse(agentAvatar) }} />}
            ml={2}
          />
        )}
      </Flex>
    );
  };

  return (
    <Box p={5}>
      <Heading as="h1" size="2xl" mb={6}>
        OptiMonkey Dashboard
      </Heading>

      {/* Button for Starting Agents */}
      <Button onClick={startAgents} colorScheme="teal" mb={4} disabled={loadingAgents}>
        {loadingAgents ? (
          <>
            <Spinner size="sm" mr={2} /> Running Agents...
          </>
        ) : (
          'Start Agents'
        )}
      </Button>

      {/* Button for Fetching Recommendations */}
      <Button onClick={fetchRecommendations} colorScheme="blue" mb={4} disabled={loadingRecommendations}>
        {loadingRecommendations ? (
          <>
            <Spinner size="sm" mr={2} /> Fetching Recommendations...
          </>
        ) : showRecommendations ? 'Hide Recommendations' : 'Show Recommendations'}
      </Button>

      {/* Render Chat Messages */}
      {conversation.length > 0 && (
        <Box
          mt={4}
          p={4}
          borderWidth="1px"
          borderRadius="lg"
          maxHeight="600px"
          overflowY="auto"
          bg={useColorModeValue('gray.50', 'gray.800')}
        >
          <VStack spacing={4} align="stretch">
            {conversation.map((message, index) => renderMessage(message, index))}
          </VStack>
        </Box>
      )}

      {/* Render CSV Data */}
      {showRecommendations && data.length > 0 && (
        <Table variant="simple" mt={4}>
          <Thead>
            <Tr>
              {headers.map((header, index) => (
                <Th key={index}>{header}</Th>
              ))}
            </Tr>
          </Thead>
          <Tbody>
            {data.map((row, rowIndex) => (
              <Tr key={rowIndex}>
                {headers.map((header, colIndex) => (
                  <Td key={colIndex}>{row[header]}</Td>
                ))}
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </Box>
  );
};

export default Dashboard;
