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
import ReactMarkdown from 'react-markdown'; 
import remarkGfm from 'remark-gfm';
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
  const [data, setData] = useState<any[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [loadingAgents, setLoadingAgents] = useState(false);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(false);

  const startAgents = () => {
    setLoadingAgents(true);
    fetch('/api/start-agents', { method: 'POST' })
      .then((response) => response.json())
      .then((data) => {
        console.log(data); // Add logging to inspect the response
        if (Array.isArray(data.conversation)) {
          setConversation(data.conversation);
        } else {
          console.error("Conversation data is not in the expected format.");
        }
        setLoadingAgents(false);
      })
      .catch((error) => {
        console.error('Error fetching agents:', error);
        setLoadingAgents(false);
      });
  };
  

  const fetchRecommendations = async () => {
    if (!showRecommendations && data.length === 0) {
      setLoadingRecommendations(true);
      try {
        const response = await fetch('/api/download-recommendations');
        const csvText = await response.text();
        Papa.parse(csvText, {
          header: true,
          complete: (result) => {
            const parsedData = result.data;
            if (parsedData.length > 0) {
              setHeaders(Object.keys(parsedData[0]));
            }
            setData(parsedData);
            setLoadingRecommendations(false);
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
    } else {
      setShowRecommendations(!showRecommendations);
    }
  };

  const isJSON = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch (e) {
      return false;
    }
  };

  // Function to render messages using Markdown, Syntax Highlighting, and JSON formatting
  const renderMessage = (message: Message, index: number) => {
    const isUser = message.role === 'user';
    const bgColor = useColorModeValue(isUser ? 'blue.100' : 'green.100', isUser ? 'blue.700' : 'green.700');
    const alignSelf = isUser ? 'flex-end' : 'flex-start';
    const borderRadius = isUser ? '20px 20px 0px 20px' : '20px 20px 20px 0px';

    const renderers = {
      code({ node, inline, className, children, ...props }: any) {
        const match = /language-(\w+)/.exec(className || '');
        return !inline && match ? (
          <SyntaxHighlighter style={dracula} language={match[1]} PreTag="div" {...props}>
            {String(children).replace(/\n$/, '')}
          </SyntaxHighlighter>
        ) : (
          <code className={className} {...props}>
            {children}
          </code>
        );
      },
    };

    const agentAvatars: { [key: string]: string | JSX.Element } = {
      Planner: '📝',
      Code_Guru: '💻',
      Critic: '🔍',
      user_proxy: '👤',
      default: <FontAwesomeIcon icon={faRobot} />,
    };

    const agentAvatar = agentAvatars[message.name] || agentAvatars['default'];

    const formatContent = () => {
      if (isJSON(message.content)) {
        // If content is JSON, format it using SyntaxHighlighter for better readability
        const parsedJSON = JSON.parse(message.content);
        return (
          <SyntaxHighlighter language="json" style={dracula}>
            {JSON.stringify(parsedJSON, null, 2)}
          </SyntaxHighlighter>
        );
      } else {
        // Render normal markdown content
        return (
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={renderers}>
            {message.content}
          </ReactMarkdown>
        );
      }
    };

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
            {message.name} {message.timestamp ? `• ${message.timestamp}` : ''}
          </Text>
          {formatContent()}
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

  const renderCSVDownloadLink = () => {
    if (data.length > 0) {
      return (
        <Flex justify="center" mt={6}>
          <a href="/api/download-recommendations" download="recommendations.csv">
            <Button colorScheme="green">Download CSV</Button>
          </a>
        </Flex>
      );
    }
    return null;
  };

  return (
    <Box p={5}>
      <Heading as="h1" size="2xl" mb={6}>
        OptiMonkey Dashboard
      </Heading>

      {/* Button for Starting Agents */}
      <Button onClick={startAgents} colorScheme="teal" mb={4} mr={4} disabled={loadingAgents}>
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
        <Box mt={4} p={4} borderWidth="1px" borderRadius="lg" maxHeight="600px" overflowY="auto" bg={useColorModeValue('gray.50', 'gray.800')}>
          <VStack spacing={4} align="stretch">
            {conversation.map((message, index) => {
              console.log('Rendering message:', message); // Add logging here
              return renderMessage(message, index);
            })}
            {renderCSVDownloadLink()}
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
