from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import agents
from agents.optimonkeyagents import start_agent_conversation_stream
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import datetime
import json
@app.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        # Listen for messages from the client
        while True:
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")

            # Trigger the agent conversation based on client input
            async for message in start_agent_conversation_stream(data):
                response_message = {
                    "content": message,
                    "role": "agent",
                    "name": "Agent",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                # Send each message to the client as soon as it’s available
                await websocket.send_text(json.dumps(response_message))
    
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)