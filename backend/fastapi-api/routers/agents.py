import json
import queue
import os
import asyncio
from datetime import datetime
from fastapi import APIRouter, Request, Response, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from agents.optimonkeyagents import start_agent_conversation_stream  # Import the agent function

# Initialize APIRouter for organizing routes
router = APIRouter()

# Queues to handle asynchronous communication
print_queue = queue.Queue()
user_queue = queue.Queue()

# Chat status to track the current state of the AutoGen conversation
chat_status = "ended"

# Manage WebSocket connections
connections = {}


@router.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)
    connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            data_json = json.loads(data)

            if data_json.get("message") == "start_chat":
                # Start chat logic, initiate conversation with agents
                await send_message_to_clients("Chat has started!")  # Notify clients that the chat started

                # Optionally start the agent conversation asynchronously
                asyncio.create_task(run_chat())

            else:
                print(f"Received message from client {client_id}: {data_json['message']}")
                # Send back a response for testing purposes
                response = {"message": f"Echo: {data_json['message']}"}
                await websocket.send_text(json.dumps(response))
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del connections[client_id]

# Function to handle the conversation asynchronously
async def run_chat():
    global chat_status
    try:
        # Process user inputs as they come in
        while chat_status == "chat_ongoing":
            if not user_queue.empty():
                user_input = user_queue.get()
                async for message in start_agent_conversation_stream(user_input):
                    msg_content = {
                        "content": message,
                        "role": "agent",
                        "name": "Agent",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                    }
                    # Send to all WebSocket connections
                    websocket_connections = list(connections.values())
                    for websocket in websocket_connections:
                        await websocket.send_text(json.dumps(msg_content))
                    # Introduce a small delay to simulate real-time streaming
                    await asyncio.sleep(0.1)
            await asyncio.sleep(1)
    except Exception as e:
        chat_status = "error"
        error_message = {
            "content": f"An error occurred: {str(e)}",
            "role": "system",
            "name": "Error",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        # Send error to all WebSocket connections
        for websocket in websocket_connections:
            await websocket.send_text(json.dumps(error_message))

# Function to send messages to all connected WebSocket clients
async def send_message_to_clients(message: str):
    disconnected_clients = []
    for client_id, ws in connections.items():
        try:
            await ws.send_text(message)
            print(f"Sent message to client {client_id}: {message}")
        except WebSocketDisconnect:
            print(f"Client {client_id} disconnected")
            disconnected_clients.append(client_id)

    for client_id in disconnected_clients:
        del connections[client_id]



@router.post("/start-agents")
async def start_agents(background_tasks: BackgroundTasks):
    global chat_status

    try:
        # Reset chat status and clear queues
        if chat_status == 'error':
            chat_status = 'ended'
        with print_queue.mutex:
            user_queue.queue.clear()
        with user_queue.mutex:
            print_queue.queue.clear()

        # Start background task for running the agents
        background_tasks.add_task(run_chat)
        chat_status = "chat_ongoing"

        return JSONResponse({"status": chat_status})
    except Exception as e:
        chat_status = "error"
        return JSONResponse({"status": "error", "error": str(e)})


@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"  # Path to the CSV file
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}
