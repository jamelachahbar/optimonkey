import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

import './DashboardTest.css';  // Import the CSS file
const DashboardTest = () => {
  const [conversation, setConversation] = useState<any[]>([]);
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8081/ws/conversation');
    setWebSocket(ws);
  
    ws.onopen = () => {
      console.log("WebSocket connection established.");
    };
  
    ws.onmessage = (event) => {
      try {
        const messageData = JSON.parse(event.data);
        console.log("Received message from backend:", messageData);
        setConversation((prev) => [...prev, messageData]);
      } catch (error) {
        console.error('Error parsing message:', error);
      }
    };
  
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);
  
  // Function to send message to backend
  const sendMessage = (message: string) => {
    if (webSocket && webSocket.readyState === WebSocket.OPEN) {
      webSocket.send(JSON.stringify({ message }));
    }
  };

  return (
    <div>
      {/* Chat UI */}
      <div className="chat-window">
        {conversation.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            <strong>{msg.name}:</strong>
            <ReactMarkdown>{msg.content}</ReactMarkdown>
            <em>({msg.timestamp})</em>
          </div>
        ))}
      </div>

      {/* Input Box */}
      <input
        type="text"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.target as HTMLInputElement).value) {
            sendMessage((e.target as HTMLInputElement).value);
            (e.target as HTMLInputElement).value = ''; // Clear the input box
          }
        }}
        placeholder="Type your message..."
      />
    </div>
  );
};

export default DashboardTest;
