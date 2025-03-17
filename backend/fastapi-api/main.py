from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from routers import agents
from agents.optimonkeyagents import start_agent_conversation_stream
import asyncio
import datetime
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")

manager = ConnectionManager()

@app.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Listen for messages from the client
        while True:
            try:
                data = await websocket.receive_text()
                logger.info(f"Received message from client: {data}")

                # Trigger the agent conversation based on client input
                conversation_task = asyncio.create_task(
                    process_conversation(websocket, data)
                )
                
                # Wait for the conversation to complete
                await conversation_task
                
            except WebSocketDisconnect:
                logger.warning("Client disconnected during message processing")
                break  # Exit the loop to clean up
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                try:
                    error_message = {
                        "content": f"Error processing request: {str(e)}",
                        "role": "system",
                        "name": "System",
                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "error"
                    }
                    await websocket.send_text(json.dumps(error_message))
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {str(send_error)}")
                    break  # Exit the loop if we can't even send error messages
    
    except WebSocketDisconnect:
        logger.warning("Client disconnected unexpectedly")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}")
    finally:
        # Ensure connection is properly removed in all cases
        manager.disconnect(websocket)

async def process_conversation(websocket: WebSocket, data: str):
    try:
        # Parse the input data to extract the message
        try:
            parsed_data = json.loads(data)
            message_content = parsed_data.get("message", data)
        except json.JSONDecodeError:
            message_content = data  # Use raw data if not JSON
        
        logger.info(f"Processing message: {message_content}")
        message_count = 0
        
        # Process the stream of messages from the agents
        async for message in start_agent_conversation_stream(message_content):
            message_count += 1
            
            # Handle different types of messages from agents
            if "error" in message:
                # Error messages
                response_message = {
                    "content": message["error"],
                    "role": "system",
                    "name": "Error",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "error"
                }
            elif "confidence_score" in message:
                # Confidence score messages
                response_message = {
                    "confidence_score": message["confidence_score"],
                    "explanation": message.get("explanation", "No explanation provided"),
                    "board_decision": message.get("board_decision", "No decision provided"),
                    "role": "system",
                    "name": "FinOps Board",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "confidence_score"
                }
            elif "recommendations" in message:
                # Recommendation messages
                response_message = {
                    "recommendations": message["recommendations"],
                    "role": "agent",
                    "name": "Recommendations",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "final_recommendations"
                }
            elif "csv" in message:
                # CSV content
                response_message = {
                    "content": message.get("csv", ""),
                    "role": "agent",
                    "name": "CSV Export",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "csv"
                }
            else:
                # Standard agent messages
                response_message = {
                    "content": message.get("content", ""),
                    "role": message.get("role", "agent"),
                    "name": message.get("name", "Agent"),
                    "timestamp": message.get("timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "type": message.get("type", "text")
                }
            
            # Send each message to the client as soon as it's available
            await websocket.send_text(json.dumps(response_message))
            # Small delay to prevent overwhelming the client
            await asyncio.sleep(0.05)
        
        # If no messages were sent, send a fallback message
        if message_count == 0:
            no_response_message = {
                "content": "I'm sorry, I don't have a response for that query.",
                "role": "agent",
                "name": "Agent",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": "text"
            }
            await websocket.send_text(json.dumps(no_response_message))
            
    except Exception as e:
        logger.error(f"Error in conversation stream: {str(e)}")
        error_message = {
            "content": f"Error during conversation: {str(e)}",
            "role": "system",
            "name": "System",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "error"
        }
        await websocket.send_text(json.dumps(error_message))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)