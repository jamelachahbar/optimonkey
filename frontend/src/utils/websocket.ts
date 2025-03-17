const websocket = new WebSocket('ws://localhost:8081/ws/conversation');

websocket.onopen = () => console.log('Connected to WebSocket');
websocket.onclose = () => console.log('Disconnected from WebSocket');

export default websocket;
