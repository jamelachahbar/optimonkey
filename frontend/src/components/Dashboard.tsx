import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import {
  Box,
  Button,
  Heading,
  VStack,
  Text,
  Spinner,
  Flex,
  InputGroup,
  Input,
  InputRightElement,
  useToast,
  useColorModeValue,
} from "@chakra-ui/react";
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  BackgroundVariant,
  NodeTypes,
} from "reactflow";
import "reactflow/dist/style.css";

// Define the structure of a message
interface Message {
  content: string;
  role: string;
  name: string;
  timestamp?: string;
}

// Define the structure of an agent update from WebSocket
interface AgentUpdate {
  agentId: string;
  status: string;
  task: string;
}

const Dashboard: React.FC = () => {
  const [conversation, setConversation] = useState<Message[]>([]);
  const [messageInput, setMessageInput] = useState("");
  const [loadingMessage, setLoadingMessage] = useState(false);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const toast = useToast();

  // React Flow states for nodes and edges
  const initialNodes = [
    { id: "1", position: { x: 0, y: 0 }, data: { label: "User Proxy", status: "idle", task: "Waiting for tasks" }, type: "agent" },
    { id: "2", position: { x: 300, y: 0 }, data: { label: "Planner", status: "idle", task: "Waiting for plan" }, type: "agent" },
    { id: "3", position: { x: 600, y: 0 }, data: { label: "Code Guru", status: "idle", task: "Waiting for coding tasks" }, type: "agent" },
    { id: "4", position: { x: 900, y: 0 }, data: { label: "Critic", status: "idle", task: "Waiting to review" }, type: "agent" },
  ];

  const initialEdges = [{ id: "e1-2", source: "1", target: "2" }];
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Memoize nodeTypes to prevent re-creation on every render
  const nodeTypes: NodeTypes = useMemo(() => ({
    agent: ({ data }) => (
      <Box borderRadius="lg" bg="blue.200" p={3} shadow="md">
        <strong>{data.label}</strong>
        <p>Status: {data.status}</p>
        <p>Task: {data.task}</p>
      </Box>
    ),
  }), []);

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null;  // Declare WebSocket instance locally
    let reconnectTimer: NodeJS.Timeout | null = null; // Timer for reconnection
  
    const connectWebSocket = () => {
      ws = new WebSocket("ws://localhost:8081/ws"); // Connect to your backend WebSocket
      wsRef.current = ws;
  
      ws.onopen = () => {
        console.log("WebSocket connection established.");
        if (reconnectTimer) {
          clearTimeout(reconnectTimer); // Clear the reconnection timer if WebSocket is reconnected
          reconnectTimer = null;
        }
      };
  
      ws.onmessage = (event) => {
        const data: AgentUpdate | Message = JSON.parse(event.data);
  
        // Handle agent update based on WebSocket data
        if ("agentId" in data) {
          // Update the agent node with the new status and task
          setNodes((nds) =>
            nds.map((node) =>
              node.id === data.agentId
                ? { ...node, data: { ...node.data, status: data.status, task: data.task } }
                : node
            )
          );
        } else {
          // Handle chat messages
          setConversation((prev) => [
            ...prev,
            {
              content: data.content,
              role: data.role,
              name: data.name,
              timestamp: new Date().toLocaleTimeString(),
            },
          ]);
        }
        setLoadingMessage(false);
      };
  
      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast({
          title: "WebSocket Error",
          description: "Connection failed. Retrying...",
          status: "error",
          duration: 3000,
          isClosable: true,
        });
      };
  
      ws.onclose = () => {
        console.log("WebSocket connection closed. Attempting to reconnect...");
        toast({
          title: "WebSocket Disconnected",
          description: "Attempting to reconnect...",
          status: "warning",
          duration: 3000,
          isClosable: true,
        });
  
        // Set up reconnection after a delay
        if (!reconnectTimer) {
          reconnectTimer = setTimeout(() => {
            connectWebSocket(); // Try to reconnect after a delay
          }, 5000); // 5 seconds delay for reconnection
        }
      };
    };
  
    connectWebSocket(); // Initial connection
  
    return () => {
      if (ws) {
        ws.close(); // Clean up WebSocket on component unmount
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer); // Clear the reconnection timer if component unmounts
      }
    };
  }, [toast]);
  
  // Handle message sending
  const handleSendMessage = () => {
    if (messageInput.trim() === "" || loadingMessage) return;

    const newMessage: Message = {
      content: messageInput,
      role: "user",
      name: "User",
      timestamp: new Date().toLocaleTimeString(),
    };
    setConversation((prev) => [...prev, newMessage]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(messageInput);
    } else {
      toast({
        title: "WebSocket Disconnected",
        description: "Attempting to reconnect...",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
    }

    setMessageInput("");
  };

  return (
    <Box display="flex" flexDirection="column" height="100vh" p={5}>
      <Box mb={6}>
        <Heading size="lg">OptiMonkey Dashboard</Heading>
      </Box>

      {/* ReactFlow Area */}
      <Box mb={6} height="40vh">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(params) => setEdges((eds) => addEdge(params, eds))}
          nodeTypes={nodeTypes}  // Use memoized nodeTypes
        >
          <Controls />
          <MiniMap />
          <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
        </ReactFlow>
      </Box>

      {/* Scrollable Chat Area */}
      <Box
        ref={chatContainerRef}
        flex="1"
        overflowY="auto"
        borderWidth="1px"
        borderRadius="lg"
        p={4}
        bg={useColorModeValue("gray.50", "gray.800")}
        mb={4}
      >
        <VStack spacing={4} align="stretch">
          {conversation.map((message, index) => (
            <Flex key={index} alignSelf={message.role === "user" ? "flex-end" : "flex-start"} my={2} maxWidth="80%">
              <Box bg={message.role === "user" ? "blue.100" : "green.100"} p={3} borderRadius="lg" boxShadow="md" flex="1">
                <Text fontSize="sm" fontWeight="bold" mb={1}>
                  {message.name} {message.timestamp ? `• ${message.timestamp}` : ""}
                </Text>
                <Text>{message.content}</Text>
              </Box>
            </Flex>
          ))}
          {loadingMessage && (
            <Flex justify="center">
              <Spinner size="sm" />
            </Flex>
          )}
        </VStack>
      </Box>

      {/* Message Input Area */}
      <Box>
        <InputGroup size="md">
          <Input
            placeholder="Type your message..."
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === "Enter") {
                handleSendMessage();
              }
            }}
            isDisabled={loadingMessage}
          />
          <InputRightElement width="4.5rem">
            <Button h="1.75rem" size="sm" onClick={handleSendMessage} isDisabled={loadingMessage}>
              {loadingMessage ? <Spinner size="xs" /> : "Send"}
            </Button>
          </InputRightElement>
        </InputGroup>
      </Box>
    </Box>
  );
};

export default Dashboard;
