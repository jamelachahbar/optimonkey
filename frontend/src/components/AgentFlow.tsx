import React, { useEffect, useState, useRef } from "react";
import ReactFlow, { Node, Edge } from "reactflow";
import 'reactflow/dist/style.css';

interface AgentStatus {
  agent: string;
  status: string;
  task: string;
}

const AgentFlow: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const ws = useRef<WebSocket | null>(null); // Ref to store WebSocket connection

  // Function to handle WebSocket messages
  const handleWebSocketMessage = (message: string) => {
    try {
      const agentStatus: AgentStatus = JSON.parse(message);

      // Update React Flow nodes based on the WebSocket message
      setNodes((currentNodes) => {
        const existingNode = currentNodes.find((node) => node.id === agentStatus.task);
      
        if (!existingNode) {
          // Create a node for the task if it doesn't exist
          const newNode: Node = {
            id: agentStatus.task,
            data: { label: `Task: ${agentStatus.task}` },
            position: { x: currentNodes.length * 200, y: 200 }, // Adjust position as needed
          };
          return [...currentNodes, newNode];
        }
      
        return currentNodes;
      });
    
      // Ensure edges are created only when valid
      setEdges((currentEdges) => {
        const existingEdge = currentEdges.find(
          (edge) => edge.source === agentStatus.agent && edge.target === agentStatus.task
        );
      
        if (existingEdge) {
          // Edge already exists, no need to add it again
          return currentEdges;
        }
      
        const newEdge: Edge = {
          id: `e-${agentStatus.agent}-${agentStatus.task}`,
          source: agentStatus.agent,  // Ensure this ID is valid
          target: agentStatus.task,   // Ensure this ID is valid
          label: agentStatus.task,
        };

        // Validate both source and target nodes exist before adding the edge
        if (nodes.find(node => node.id === agentStatus.agent) && 
            nodes.find(node => node.id === agentStatus.task)) {
          return [...currentEdges, newEdge];
        }

        return currentEdges;
      });
    } catch (error) {
      console.error("Error parsing WebSocket message: ", error);
    }
  };

  useEffect(() => {
    // Open WebSocket connection
    ws.current = new WebSocket("ws://localhost:8000/ws");

    // On receiving a message from the WebSocket, handle the message
    if (ws.current) {
      ws.current.onmessage = (event) => {
        handleWebSocketMessage(event.data);
      };

      ws.current.onclose = () => {
        console.log("WebSocket connection closed");
      };
    }

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  return (
    <div style={{ width: "100%", height: "500px" }}>
      <ReactFlow nodes={nodes} edges={edges} />
    </div>
  );
};

export default AgentFlow;
