import json
import queue
import os
import asyncio
from datetime import datetime
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from agents.optimonkeyagents import start_agent_conversation_stream, save_results_to_csv

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
    global chat_status  # Access global chat status
    try:
        while True:
            # Listen for messages from the client
            data = await websocket.receive_text()
            print(f"Received message from client: {data}")

            # Start a new conversation if chat_status is not "ongoing"
            if chat_status != "chat_ongoing":
                chat_status = "chat_ongoing"
                with print_queue.mutex:
                    print_queue.queue.clear()
                with user_queue.mutex:
                    user_queue.queue.clear()

            # Trigger the agent conversation
            async for message in start_agent_conversation_stream(data):
                if message.get("content") == "TERMINATE":
                    # Conversation ended, prepare CSV response
                    result = []
                    csv_file_path = save_results_to_csv(result)
                    with open(csv_file_path, 'r') as csv_file:
                        csv_content = csv_file.read()
                    
                    response_message = {
                        "content": csv_content,
                        "role": "agent",
                        "name": "Executor",
                        "type": "csv",
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    await websocket.send_text(json.dumps(response_message))

                    # Reset chat_status to allow new conversations
                    chat_status = "ended"
                    print("Conversation ended. Ready for new messages.")
                    break  # Exit the loop to close the WebSocket

                else:
                    # Handle regular messages
                    response_message = {
                        "content": message.get("content"),
                        "role": message.get("role"),
                        "name": message.get("name"),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    await websocket.send_text(json.dumps(response_message))
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del connections[client_id]

async def run_chat():
    global chat_status
    try:
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
                    for websocket in connections.values():
                        await websocket.send_text(json.dumps(msg_content))
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
        for websocket in connections.values():
            await websocket.send_text(json.dumps(error_message))
    finally:
        chat_status = "ended"  # Ensure the status is reset once the chat is finished

@router.post("/start-agents")
async def start_agents(background_tasks: BackgroundTasks):
    global chat_status
    try:
        chat_status = 'ended' if chat_status == 'error' else chat_status
        if chat_status != "chat_ongoing":
            background_tasks.add_task(run_chat)
            chat_status = "chat_ongoing"
        return JSONResponse({"status": chat_status})
    except Exception as e:
        chat_status = "error"
        return JSONResponse({"status": "error", "error": str(e)})

@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}

@router.post("/api/send_message")
async def send_message(request: Request):
    body = await request.json()
    user_input = body.get("message", "")
    if user_input:
        user_queue.put(user_input)
        return JSONResponse({"status": "Message Received"})
    return JSONResponse({"status": "Error", "message": "No message provided"}, status_code=400)
