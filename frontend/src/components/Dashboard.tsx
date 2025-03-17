import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Spinner,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  UnorderedList,
  ListItem,
} from '@chakra-ui/react';
import { MoonIcon, SunIcon, DeleteIcon, CheckIcon, WarningIcon, InfoIcon, ChevronDownIcon } from '@chakra-ui/icons';
import ReactMarkdown from 'react-markdown';
import PromptTemplate from '../components/PromptTemplate';

interface Message {
  user: string;
  name: string;
  message: string | { 
    recommendations?: Array<Record<string, unknown>>; 
    resourceType?: string; 
    explanation?: string; 
    confidence_score?: number | string | { value: number | string } | { name: string, value: number | string }; 
    board_decision?: string 
  } | object;
  timestamp: string;
  role: string;
  type?: string; // "csv", "text", "final_recommendations", or "confidence_score"
}

interface WebSocketMessageData {
  content?: string;
  message?: string | object;
  recommendations?: Array<Record<string, unknown>>;
  confidence_score?: number | string | { value: number | string } | { name: string, value: number | string };  // Support all formats
  explanation?: string;
  board_decision?: string;
  score_name?: string; // Add score_name from backend
  role?: string;
  name?: string;
  timestamp?: string;
  type?: string; // Added for heartbeat type
}

const Dashboard: React.FC = () => {
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [socketStatus, setSocketStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const { colorMode, toggleColorMode } = useColorMode();
  const codeBgColor = useColorModeValue('gray.100', 'gray.700');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track if WebSocket is being initialized to prevent multiple connections
  const isInitializingRef = useRef(false);

  const bgColor = useColorModeValue('white', 'gray.800');
  const userBgColor = useColorModeValue('blue.100', 'blue.700');
  const agentBgColor = useColorModeValue('gray.100', 'gray.600');
  const textColor = useColorModeValue('blue.500', 'blue.300');

  // Debug logger
  const debugLogger = useCallback((message: string, data?: unknown) => {
    console.log(`[DEBUG] ${message}`, data || '');
  }, []);

  // Initialize WebSocket
  const initializeWebSocket = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isInitializingRef.current) {
      debugLogger('Already initializing WebSocket - skipping');
      return;
    }
    
    isInitializingRef.current = true;
    debugLogger('Initializing WebSocket connection');
    
    // Close any existing connection
    if (ws) {
      debugLogger('Closing existing WebSocket connection');
      ws.close();
    }
    
    setSocketStatus('connecting');
    
    const websocket = new WebSocket('ws://127.0.0.1:8081/ws/conversation');
    
    websocket.onopen = () => {
      debugLogger('WebSocket connection established successfully');
      setSocketStatus('connected');
      isInitializingRef.current = false;
    };

    websocket.onmessage = (event) => {
      try {
        const messageData: WebSocketMessageData = JSON.parse(event.data);
        
        // Skip system messages silently without logging
        if (messageData.type === 'heartbeat' || messageData.type === 'pong') {
          return;
        }
        
        debugLogger('Message received:', messageData);
        setLoading(false);

        // Check if content is CSV-like data
        if (messageData.content && typeof messageData.content === 'string') {
          const content = messageData.content;
          // Check for CSV format (comma separated values with multiple lines)
          const isCSV = content.includes(',') && 
                        content.includes('\n') && 
                        content.split('\n').length > 1 && 
                        content.split('\n')[0].split(',').length > 3;
          
          if (isCSV) {
            setMessages((prev) => [
              ...prev,
              {
                user: messageData.name || 'Agent',
                name: messageData.name || 'Agent',
                message: content,
                timestamp: messageData.timestamp || new Date().toLocaleTimeString(),
                role: messageData.role || 'agent',
                type: 'csv',
              },
            ]);
            return;
          }
        }

        // Handle different message formats from the server
        if (messageData.content) {
          // Format from the FastAPI backend
          setMessages((prev) => [
            ...prev,
            {
              user: messageData.name || 'Agent',
              name: messageData.name || 'Agent',
              message: messageData.content || '', // Ensure non-null with empty string fallback
              timestamp: messageData.timestamp || new Date().toLocaleTimeString(),
              role: messageData.role || 'agent',
              type: 'text',
            },
          ]);
          return;
        }

        // Handle confidence score messages
        if (messageData.confidence_score !== undefined) {
          let confidenceScoreValue = 1; // Default to 1 (LOW)
          let scoreName = messageData.score_name || '';
          const boardDecision = messageData.board_decision || 'No board decision provided';
          
          try {
            const rawScore = messageData.confidence_score;
            
            // Handle number values
            if (typeof rawScore === 'number') {
              // Ensure value is between 1-4
              confidenceScoreValue = Math.max(1, Math.min(4, Math.round(rawScore)));
            } 
            // Handle string values 
            else if (typeof rawScore === 'string') {
              // Check if it's a numeric string
              if (/^\d+$/.test(rawScore)) {
                const parsedValue = parseInt(rawScore, 10);
                confidenceScoreValue = Math.max(1, Math.min(4, parsedValue));
              } 
              // Handle named score values (e.g., "LOW", "MEDIUM", "HIGH", "EXCELLENT")
              else {
                const scoreMap: {[key: string]: number} = {
                  'LOW': 1,
                  'MEDIUM': 2,
                  'HIGH': 3,
                  'EXCELLENT': 4,
                  'VERY_HIGH': 4 // Add alias
                };
                
                // Convert to uppercase for case-insensitive comparison
                const upperScore = rawScore.toUpperCase();
                if (scoreMap[upperScore] !== undefined) {
                  confidenceScoreValue = scoreMap[upperScore];
                  if (!scoreName) scoreName = upperScore;
                }
              }
            }
            // Handle object with value property (from enum serialization)
            else if (typeof rawScore === 'object' && rawScore !== null) {
              if ('value' in rawScore) {
                const enumValue = (rawScore as { value: number | string }).value;
                
                if (typeof enumValue === 'number') {
                  confidenceScoreValue = Math.max(1, Math.min(4, enumValue));
                } else if (typeof enumValue === 'string') {
                  if (/^\d+$/.test(enumValue)) {
                    confidenceScoreValue = parseInt(enumValue, 10);
                  } else {
                    // Handle named values in enum object
                    const scoreMap: {[key: string]: number} = {
                      'LOW': 1,
                      'MEDIUM': 2,
                      'HIGH': 3,
                      'EXCELLENT': 4,
                      'VERY_HIGH': 4
                    };
                    
                    const upperScore = enumValue.toUpperCase();
                    if (scoreMap[upperScore] !== undefined) {
                      confidenceScoreValue = scoreMap[upperScore];
                      if (!scoreName) scoreName = upperScore;
                    }
                  }
                }
              }
              
              // If it has a name property directly
              if ('name' in rawScore && typeof rawScore.name === 'string') {
                scoreName = rawScore.name.toUpperCase();
              }
            }
            
            // Set a default score name if we don't have one
            if (!scoreName) {
              scoreName = confidenceScoreValue === 4 ? "EXCELLENT" : 
                         confidenceScoreValue === 3 ? "HIGH" : 
                         confidenceScoreValue === 2 ? "MEDIUM" : "LOW";
            }
            
            // Log info about parsed score
            debugLogger('Confidence Score Processed:', { 
              original: messageData.confidence_score, 
              parsed: confidenceScoreValue,
              name: scoreName
            });
            
          } catch (error) {
            console.error('Error parsing confidence score:', error);
            // Keep default value of 1
          }
          
          const explanation = messageData.explanation || 'No explanation provided.';
          
          // Create a formatted message for the confidence score
          setMessages((prev) => [
            ...prev,
            {
              user: 'FinOps Board',
              name: 'FinOps Board',
              message: {
                confidence_score: confidenceScoreValue,
                explanation,
                board_decision: boardDecision,
                score_name: scoreName
              },
              timestamp: messageData.timestamp || new Date().toLocaleTimeString(),
              role: 'system',
              type: 'confidence_score',
            },
          ]);
          
          // Log low scores
          if (confidenceScoreValue < 3) {
            debugLogger('Confidence score below threshold:', confidenceScoreValue);
          }
          
          return;
        }

        // Handle recommendations
        if (messageData.recommendations) {
          console.log('Recommendations received:', messageData.recommendations);
          const recommendations = messageData.message || {}; // Ensure non-null
          setMessages((prev) => [
            ...prev,
            {
              user: messageData.name || 'Agent',
              name: messageData.name || 'Agent',
              message: recommendations,
              timestamp: messageData.timestamp || new Date().toLocaleTimeString(),
              role: 'agent',
              type: 'text',
            },
          ]);
          return;
        }

        // Handle generic or fallback messages
        setMessages((prev) => [
          ...prev,
          {
            user: messageData.name || 'Agent',
            name: messageData.name || 'Agent',
            message: messageData.message || messageData,
            timestamp: messageData.timestamp || new Date().toLocaleTimeString(),
            role: 'agent',
            type: 'text',
          },
        ]);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    websocket.onclose = (event) => {
      debugLogger(`WebSocket connection closed. Code: ${event.code}`);
      setSocketStatus('disconnected');
      setLoading(false);
      isInitializingRef.current = false;
      
      // Simple reconnection with fixed delay, but only if not closed intentionally
      if (event.code !== 1000) {
        setTimeout(() => {
          if (!isInitializingRef.current) {
            debugLogger('Attempting to reconnect after timeout...');
            initializeWebSocket();
          }
        }, 5000);
      }
    };

    websocket.onerror = () => {
      debugLogger('WebSocket error occurred');
      setSocketStatus('error');
      setLoading(false);
      isInitializingRef.current = false;
    };

    // Set the websocket object in state
    setWs(websocket);
  }, [debugLogger, ws]);

  useEffect(() => {
    // Only initialize on mount
    if (!ws && socketStatus === 'disconnected' && !isInitializingRef.current) {
      debugLogger('Initial WebSocket connection on mount');
      initializeWebSocket();
    }
    
    // Return a cleanup function
    return () => {
      if (ws) {
        debugLogger('Closing WebSocket on component unmount');
        ws.close(1000, 'Component unmounting');
      }
    };
  }, []); // Empty dependency array to only run on mount/unmount

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => 
    setUserInput(e.target.value), 
  []);

  const handleSend = useCallback(() => {
    if (userInput.trim() === '') {
      debugLogger('Cannot send empty message');
      return;
    }

    if (ws) {
      if (ws.readyState === WebSocket.OPEN) {
        try {
          debugLogger('Sending message:', userInput);
          const message = JSON.stringify({ message: userInput });
          ws.send(message);
          setMessages((prev) => [
            ...prev,
            {
              user: 'You',
              name: 'You',
              message: userInput,
              timestamp: new Date().toLocaleTimeString(),
              role: 'user',
            },
          ]);
          setLoading(true);
          setUserInput('');
        } catch (error) {
          console.error('Error sending message:', error);
        }
      } else {
        console.error('WebSocket is not open. Current state:', ws.readyState);
        // Try to reconnect
        debugLogger('Attempting to reconnect WebSocket...');
        initializeWebSocket();
      }
    } else {
      console.error('WebSocket is not initialized');
      // Try to initialize
      debugLogger('Attempting to initialize WebSocket...');
      initializeWebSocket();
    }
  }, [ws, userInput, debugLogger, initializeWebSocket]);

  const handleClearChat = useCallback(() => setMessages([]), []);

  // Function to clear all system messages (pongs, heartbeats)
  const handleClearSystemMessages = useCallback(() => {
    setMessages(prevMessages => 
      prevMessages.filter(msg => 
        msg.name !== 'System' || (msg.type !== 'heartbeat' && msg.type !== 'pong')
      )
    );
  }, []);

  // Clear system messages automatically when they accumulate
  useEffect(() => {
    const systemMessages = messages.filter(
      msg => msg.name === 'System' && (msg.type === 'heartbeat' || msg.type === 'pong')
    );
    
    // If there are more than 3 system messages, clear them
    if (systemMessages.length > 3) {
      handleClearSystemMessages();
    }
  }, [messages, handleClearSystemMessages]);

  const handlePromptSelection = useCallback((prompt: string) => setUserInput(prompt), []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  }, [handleSend]);

  // Render message type badge
  const renderMessageTypeBadge = useCallback((type?: string) => {
    if (!type) return null;
    
    let icon = null;
    let label = '';
    let color = '';
    
    switch (type) {
      case 'confidence_score':
        icon = <InfoIcon mr={1} />;
        label = 'FinOps Score';
        color = 'blue';
        break;
      case 'final_recommendations':
        icon = <CheckIcon mr={1} />;
        label = 'Recommendations';
        color = 'green';
        break;
      case 'text':
        return null; // Don't show badge for regular text
      default:
        icon = null;
        label = type;
        color = 'gray';
    }
    
    return (
      <Badge colorScheme={color} ml={2} display="flex" alignItems="center">
        {icon}{label}
      </Badge>
    );
  }, []);

  // Define renderCSVContent first (no dependencies on renderMessageContent)
  const renderCSVContent = useCallback((csvContent: string) => {
    try {
      // Split the CSV into rows
      const rows = csvContent.trim().split('\n');
      
      if (rows.length === 0) return <Text>Empty data</Text>;
      
      // Parse header row
      const headers = rows[0].split(',').map(h => h.trim());
      
      // Parse data rows
      const dataRows = rows.slice(1).map(row => {
        // Handle special case: the row itself might contain commas inside quotes
        const values: string[] = [];
        let inQuotes = false;
        let currentValue = '';
        
        for (let i = 0; i < row.length; i++) {
          const char = row[i];
          
          if (char === '"' && (i === 0 || row[i-1] !== '\\')) {
            inQuotes = !inQuotes;
          } else if (char === ',' && !inQuotes) {
            values.push(currentValue.trim());
            currentValue = '';
          } else {
            currentValue += char;
          }
        }
        
        // Add the last value
        values.push(currentValue.trim());
        
        // If we don't have enough values, pad with empty strings
        while (values.length < headers.length) {
          values.push('');
        }
        
        return values;
      });
      
      // Generate the table UI
      return (
        <Box overflowX="auto" width="100%" maxWidth="100%" py={2}>
          <Text fontWeight="bold" fontSize="md" mb={2}>Azure Resource Recommendations</Text>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse', 
            fontSize: '0.75em',
            tableLayout: 'fixed' 
          }}>
            <thead>
              <tr style={{ backgroundColor: codeBgColor }}>
                {headers.map((header, index) => (
                  <th key={index} style={{ 
                    textAlign: 'left', 
                    padding: '4px 6px',
                    fontWeight: 'bold',
                    maxWidth: index === 0 ? '180px' : '120px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                  }}>
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dataRows.map((row, rowIndex) => (
                <tr key={rowIndex} style={{ 
                  borderBottom: '1px solid #ddd',
                  backgroundColor: rowIndex % 2 === 0 ? 'transparent' : 'rgba(0,0,0,0.02)'
                }}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} style={{ 
                      padding: '4px 6px',
                      maxWidth: cellIndex === 0 ? '180px' : '120px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: cellIndex === 0 ? 'nowrap' : 'normal'
                    }}>
                      {/* If this is recommendation column (typically last), show it differently */}
                      {cellIndex === row.length - 1 && headers[cellIndex].toLowerCase().includes('recommendation') ? (
                        <Text fontWeight="medium" color="blue.600">{cell}</Text>
                      ) : (
                        cell
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          
          {/* Add download button */}
          <Button 
            size="xs" 
            leftIcon={<CheckIcon />} 
            colorScheme="blue" 
            mt={2}
            onClick={() => {
              const blob = new Blob([csvContent], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'azure_recommendations.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}
          >
            Download CSV
          </Button>
        </Box>
      );
    } catch (error) {
      console.error('Error parsing CSV content:', error);
      return (
        <Box>
          <Text color="red.500">Error parsing CSV data</Text>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8em' }}>{csvContent}</pre>
        </Box>
      );
    }
  }, [codeBgColor]);

  // Now we can use renderCSVContent in renderMessageContent
  const renderMessageContent = useCallback((message: Message) => {
    const { message: content, type } = message;
    
    if (type === 'confidence_score' && typeof content === 'object' && content !== null) {
      try {
        // Cast to appropriate type
        const data = content as { 
          confidence_score?: number | string | { value: number | string }; 
          explanation?: string;
          board_decision?: string;
          score_name?: string;
        };
        
        const rawScore = data.confidence_score;
        let confidenceScoreValue = 1; // Default to LOW
        let scoreName = data.score_name || ""; // Get score name if available from backend
        
        try {
          // Handle different score formats
          if (typeof rawScore === 'number') {
            // Number between 1-4
            confidenceScoreValue = Math.max(1, Math.min(4, Math.round(rawScore)));
          } else if (typeof rawScore === 'string') {
            // Check if it's a numeric string
            if (/^\d+$/.test(rawScore)) {
              const parsedValue = parseInt(rawScore, 10);
              confidenceScoreValue = Math.max(1, Math.min(4, parsedValue));
            } else {
              // Handle named scores (LOW, MEDIUM, HIGH, VERY_HIGH, EXCELLENT)
              const scoreMap: { [key: string]: number } = {
                'LOW': 1,
                'MEDIUM': 2,
                'HIGH': 3,
                'VERY_HIGH': 4,
                'EXCELLENT': 4
              };
              
              const upperScore = rawScore.toUpperCase();
              if (scoreMap[upperScore] !== undefined) {
                confidenceScoreValue = scoreMap[upperScore];
                scoreName = upperScore; // Set the score name if it wasn't provided
              }
            }
          } else if (typeof rawScore === 'object' && rawScore !== null) {
            // Handle enum object format with value property
            if ('value' in rawScore) {
              const enumValue = rawScore.value;
              if (typeof enumValue === 'number') {
                confidenceScoreValue = Math.max(1, Math.min(4, enumValue));
              } else if (typeof enumValue === 'string') {
                if (/^\d+$/.test(enumValue)) {
                  confidenceScoreValue = parseInt(enumValue, 10);
                } else {
                  // Handle named values in the enum object
                  const scoreMap: { [key: string]: number } = {
                    'LOW': 1,
                    'MEDIUM': 2,
                    'HIGH': 3,
                    'VERY_HIGH': 4,
                    'EXCELLENT': 4
                  };
                  const upperScore = enumValue.toUpperCase();
                  if (scoreMap[upperScore] !== undefined) {
                    confidenceScoreValue = scoreMap[upperScore];
                    scoreName = upperScore; // Set the score name if it wasn't provided
                  }
                }
              }
            }
            
            // If it has a 'name' property (for enum objects with {name, value})
            if ('name' in rawScore && typeof rawScore.name === 'string') {
              scoreName = rawScore.name.toUpperCase();
            }
          }
        } catch (error) {
          console.warn('Error parsing confidence score:', error);
          confidenceScoreValue = 1; // Default to LOW on error
        }
        
        // If score name is not set, derive it from the confidence score value
        if (!scoreName) {
          scoreName = confidenceScoreValue === 4 ? "EXCELLENT" : 
                      confidenceScoreValue === 3 ? "HIGH" : 
                      confidenceScoreValue === 2 ? "MEDIUM" : "LOW";
        }
        
        const scoreExplanation = data.explanation || 'No explanation provided';
        const boardDecision = data.board_decision || 'No board decision provided';
        
        // Display warning if score is below threshold
        if (confidenceScoreValue < 3) {
          console.warn(`Low confidence score: ${confidenceScoreValue}`);
        }
        
        // Set colors based on score
        const scoreBgColor = confidenceScoreValue === 4 ? "green.50" : 
                            confidenceScoreValue === 3 ? "blue.50" : 
                            confidenceScoreValue === 2 ? "yellow.50" : "red.50";
                            
        const scoreBorderColor = confidenceScoreValue === 4 ? "green.500" : 
                                confidenceScoreValue === 3 ? "blue.500" : 
                                confidenceScoreValue === 2 ? "yellow.500" : "red.500";
                                
        const scoreHeadingColor = confidenceScoreValue === 4 ? "green.700" : 
                                 confidenceScoreValue === 3 ? "blue.700" : 
                                 confidenceScoreValue === 2 ? "yellow.700" : "red.700";
        
        // Icon based on score
        const ScoreIcon = confidenceScoreValue >= 3 ? CheckIcon : 
                         confidenceScoreValue === 2 ? WarningIcon : InfoIcon;
        
        return (
          <Box p={3} borderRadius="md" bg={scoreBgColor} borderLeft="4px solid" borderColor={scoreBorderColor} width="100%">
            <Heading size="sm" mb={2} color={scoreHeadingColor}>FinOps Assessment</Heading>
            <Flex alignItems="center" mb={3}>
              <Text fontWeight="bold" mr={2}>Score:</Text>
              <Badge colorScheme={
                confidenceScoreValue === 4 ? "green" : 
                confidenceScoreValue === 3 ? "blue" : 
                confidenceScoreValue === 2 ? "yellow" : "red"
              } fontSize="0.9em" display="flex" alignItems="center" p={1}>
                <ScoreIcon mr={1} />
                {confidenceScoreValue}/4 - {scoreName}
              </Badge>
            </Flex>
            <Box mb={3} p={2} bg="white" borderRadius="sm">
              <Text fontWeight="bold" mb={1}>Board Decision:</Text>
              <Text fontSize="sm" fontWeight="medium" 
                color={boardDecision.includes("PASS") ? "green.600" : "red.600"}>
                {boardDecision}
              </Text>
            </Box>
            <Box p={2} bg="white" borderRadius="sm">
              <Text fontWeight="bold" mb={1}>Explanation:</Text>
              <Text fontSize="sm">{scoreExplanation}</Text>
            </Box>
          </Box>
        );
      } catch (error) {
        console.error('Error rendering confidence score:', error);
        return <Text color="red.500">Error displaying confidence score</Text>;
      }
    }
    
    if (type === 'final_recommendations' && typeof content === 'object' && content !== null) {
      try {
        const recommendations = content as { recommendations?: string[] };
        return (
          <Box p={3} borderRadius="md" bg="blue.50" borderLeft="4px solid" borderColor="blue.500" width="100%">
            <Heading size="sm" mb={3} color="blue.700">Recommendations</Heading>
            {recommendations.recommendations && recommendations.recommendations.length > 0 ? (
              <UnorderedList spacing={2}>
                {recommendations.recommendations.map((rec: string, idx: number) => (
                  <ListItem key={idx}>{rec}</ListItem>
                ))}
              </UnorderedList>
            ) : (
              <Text>No recommendations provided</Text>
            )}
          </Box>
        );
      } catch (error) {
        console.error('Error parsing recommendations:', error);
        return <Text>{String(content)}</Text>;
      }
    }

    // Check if the content appears to be CSV data
    if (type === 'csv' && typeof content === 'string') {
      return renderCSVContent(content);
    } else if (typeof content === 'string' && 
        content.includes(',') && 
        content.includes('\n') && 
        content.split('\n').length > 1 &&
        content.split('\n')[0].includes(',')) {
      return renderCSVContent(content);
    }
    
    // Render as Markdown for text messages
    if (typeof content === 'string') {
      return (
        <Box className="markdown-body" width="100%">
          <ReactMarkdown
            components={{
              code({ className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                if (match) {
                  // Use pre/code tags for code blocks instead of SyntaxHighlighter to avoid prop type errors
                  return (
                    <pre
                      style={{
                        backgroundColor: 'rgb(40, 44, 52)',
                        color: 'white',
                        padding: '1em',
                        borderRadius: '5px',
                        overflow: 'auto'
                      }}
                    >
                      <code {...props} className={className}>
                        {String(children).replace(/\n$/, '')}
                      </code>
                    </pre>
                  );
                }
                
                return (
                  <code className={className} {...props} style={{ backgroundColor: codeBgColor }}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {content}
          </ReactMarkdown>
        </Box>
      );
    }
    
    // Fallback for other content types
    return <Text>{String(content)}</Text>;
  }, [codeBgColor, renderCSVContent]);

  // Add a new function to determine the avatar for different agents
  const getAgentAvatar = useCallback((agentName: string) => {
    if (agentName === 'FinOps Board') {
      return <Avatar size="sm" name="FinOps" bg="blue.500" icon={<InfoIcon fontSize="1.2rem" />} mr={2} />;
    } else if (agentName === 'Planner') {
      return <Avatar size="sm" name="Planner" bg="purple.500" mr={2} />;
    } else if (agentName === 'Code_Guru' || agentName === 'Coder') {
      return <Avatar size="sm" name="Coder" bg="green.500" mr={2} />;
    } else if (agentName === 'Critic') {
      return <Avatar size="sm" name="Critic" bg="red.500" mr={2} />;
    } else if (agentName === 'Executor') {
      return <Avatar size="sm" name="Executor" bg="orange.500" mr={2} />;
    } else if (agentName === 'Recommendations') {
      return <Avatar size="sm" name="Recommendations" bg="teal.500" icon={<CheckIcon fontSize="1.2rem" />} mr={2} />;
    } else if (agentName === 'Error' || agentName === 'System') {
      return <Avatar size="sm" name="System" bg="red.500" icon={<WarningIcon fontSize="1.2rem" />} mr={2} />;
    } else {
      return <Avatar size="sm" name={agentName} bg="gray.500" mr={2} />;
    }
  }, []);

  // Update the renderMessageContent function to handle agent-specific content
  const renderAgentMessage = useCallback((msg: Message) => {
    // Convert message to string for display
    const messageContent = typeof msg.message === 'string' 
      ? msg.message 
      : JSON.stringify(msg.message, null, 2);
    
    // Apply different styles or formatting based on the agent type
    if (msg.name === 'Planner') {
      return (
        <Box p={2} bg="purple.50" borderLeft="3px solid" borderLeftColor="purple.500" borderRadius="md">
          <Text fontWeight="medium" color="purple.800" whiteSpace="pre-wrap">{messageContent}</Text>
        </Box>
      );
    } else if (msg.name === 'Code_Guru' || msg.name === 'Coder') {
      return (
        <Box p={2} bg="green.50" borderLeft="3px solid" borderLeftColor="green.500" borderRadius="md">
          <Text fontWeight="medium" color="green.800" whiteSpace="pre-wrap">{messageContent}</Text>
        </Box>
      );
    } else if (msg.name === 'Critic') {
      return (
        <Box p={2} bg="red.50" borderLeft="3px solid" borderLeftColor="red.500" borderRadius="md">
          <Text fontWeight="medium" color="red.800" whiteSpace="pre-wrap">{messageContent}</Text>
        </Box>
      );
    } else if (msg.name === 'Executor') {
      return (
        <Box p={2} bg="orange.50" borderLeft="3px solid" borderLeftColor="orange.500" borderRadius="md">
          <Text fontWeight="medium" color="orange.800" whiteSpace="pre-wrap">{messageContent}</Text>
        </Box>
      );
    } else {
      // Default rendering for other agent types
      return renderMessageContent(msg);
    }
  }, [renderMessageContent]);

  return (
    <Flex h="100vh" direction="column" bg={bgColor}>
      <Box p={4} margin={2}>
        <Heading as="h3" size="md" textAlign="center" mb={4}>
          Prompt Templates
        </Heading>
        <SimpleGrid columns={{ base: 1, sm: 1, md: 1, lg: 1 }} spacing={6} justifyItems="center">
          <PromptTemplate onSelectPrompt={handlePromptSelection} />
        </SimpleGrid>
      </Box>

      <VStack spacing={4} align="stretch" p={6} overflowY="auto" flex="1" overflowX="hidden">
        {messages
          .filter(msg => msg.name !== 'System' || (msg.type !== 'heartbeat' && msg.type !== 'pong'))
          .map((msg, index) => (
          <Flex
            key={index}
            alignSelf={msg.role === 'user' ? 'flex-end' : 'flex-start'}
            p={4}
            boxShadow="md"
            maxWidth={msg.type === 'confidence_score' ? '75%' : '60%'}
            flexDir="column"
            alignItems="flex-start"
            bg={
              msg.role === 'user' 
                ? userBgColor 
                : msg.type === 'confidence_score'
                  ? 'blue.50'
                  : agentBgColor
            }
            borderRadius="md"
            overflowWrap="break-word"
            borderLeft={msg.type === 'confidence_score' ? '4px solid' : 'none'}
            borderLeftColor="blue.500"
          >
            <Flex align="center" mb={2} width="100%">
              {msg.role !== 'user' && getAgentAvatar(msg.name)}
              <Text fontWeight="bold" color={
                msg.name === 'FinOps Board' ? 'blue.600' : 
                msg.name === 'Planner' ? 'purple.600' :
                msg.name === 'Code_Guru' || msg.name === 'Coder' ? 'green.600' :
                msg.name === 'Critic' ? 'red.600' :
                msg.name === 'Executor' ? 'orange.600' :
                msg.name === 'Recommendations' ? 'teal.600' :
                textColor
              }>
                {msg.name} • {msg.timestamp}
              </Text>
              {renderMessageTypeBadge(msg.type)}
            </Flex>
            <Box 
              p={3} 
              bg={bgColor} 
              borderRadius="md" 
              w="full" 
              display="flex" 
              flexDirection="column"
              overflowX="hidden"
              maxWidth="100%"
            >
              {msg.name === 'Planner' || msg.name === 'Code_Guru' || msg.name === 'Coder' || 
               msg.name === 'Critic' || msg.name === 'Executor' ? 
                renderAgentMessage(msg) : 
                renderMessageContent(msg)}
            </Box>
          </Flex>
        ))}
        <div ref={messagesEndRef} />
      </VStack>

      {loading && (
        <Flex align="center" justify="center" mb={2}>
          <Spinner size="md" mr={2} />
          <Text>Agent is working...</Text>
        </Flex>
      )}

      {socketStatus !== 'connected' && (
        <Flex align="center" justify="center" mb={2} p={4} bg={socketStatus === 'connecting' ? 'yellow.50' : 'red.50'} borderRadius="md">
          <Box mr={2}>
            {socketStatus === 'connecting' ? 
              <Spinner size="sm" color="yellow.500" /> : 
              <WarningIcon color="red.500" />
            }
          </Box>
          <Text color={socketStatus === 'connecting' ? 'yellow.700' : 'red.700'} fontWeight="medium">
            {socketStatus === 'connecting' 
              ? 'Connecting to server...' 
              : 'Connection to server lost. Attempting to reconnect...'}
          </Text>
          {(socketStatus === 'error' || socketStatus === 'disconnected') && (
            <Button 
              size="sm" 
              colorScheme="red" 
              ml={4} 
              onClick={initializeWebSocket}
            >
              Retry Now
            </Button>
          )}
        </Flex>
      )}

      <Box display="flex" alignItems="center" p={4} bg={bgColor} borderTop="1px solid" borderColor="gray.300">
        <Input
          width="60%"
          type="text"
          value={userInput}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
        />
        <Button 
          colorScheme="blue" 
          onClick={handleSend} 
          mr={2}
          isDisabled={!ws || ws.readyState !== WebSocket.OPEN}
        >
          Send
        </Button>
        
        <Menu>
          <MenuButton as={Button} rightIcon={<ChevronDownIcon />} colorScheme="red" variant="outline" mr={2}>
            <Flex align="center">
              <DeleteIcon mr={2} /> Clear
            </Flex>
          </MenuButton>
          <MenuList>
            <MenuItem onClick={handleClearChat}>Clear All Messages</MenuItem>
            <MenuItem onClick={handleClearSystemMessages}>Clear System Messages Only</MenuItem>
          </MenuList>
        </Menu>
        
        <IconButton
          aria-label="Toggle dark mode"
          icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
          onClick={toggleColorMode}
        />
        
        <Flex align="center" ml={2}>
          <Text 
            fontSize="sm" 
            fontWeight="medium"
            color={
              socketStatus === 'connected' ? 'green.500' : 
              socketStatus === 'connecting' ? 'orange.500' : 
              'red.500'
            }
          >
            {socketStatus === 'connected' 
              ? 'Connected' 
              : socketStatus === 'connecting' 
                ? 'Connecting...' 
                : socketStatus === 'error'
                  ? 'Connection Error'
                  : 'Disconnected'}
          </Text>
        </Flex>
      </Box>
    </Flex>
  );
};

export default Dashboard;
