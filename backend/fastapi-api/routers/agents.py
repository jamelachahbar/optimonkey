import json
import queue
import os
import asyncio
from fastapi import APIRouter, Request, Response, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from agents.optimonkeyagents import start_agent_conversation_stream  # Import the agent function

# Initialize APIRouter for organizing routes
router = APIRouter()

# Queues to handle asynchronous communication
print_queue = queue.Queue()
user_queue = queue.Queue()

# Chat status to track the current state of the AutoGen conversation
chat_status = "ended"


# Modify start_agents to use BackgroundTasks
@router.post("/start-agents")
async def start_agents(background_tasks: BackgroundTasks):
    global chat_status

    try:
        # Reset chat status and clear queues
        if chat_status == 'error':
            chat_status = 'ended'
        with print_queue.mutex:
            print_queue.queue.clear()
        with user_queue.mutex:
            print_queue.queue.clear()

        # Start background task for running the agents
        background_tasks.add_task(run_chat)
        chat_status = "Chat ongoing"

        return JSONResponse({"status": chat_status})
    except Exception as e:
        chat_status = "error"
        return JSONResponse({"status": "error", "error": str(e)})


# Route to send a message and start the conversation stream
@router.post("/send-message")
async def send_message(request: Request):
    data = await request.json()
    user_input = data['message']
    
    # Add user input to the queue
    user_queue.put(user_input)
    
    # Return response indicating the message was received
    return JSONResponse({"status": "Message received"})


# Route to fetch messages from the conversation
@router.get("/api/get-message")
async def get_message():
    global chat_status
    if not print_queue.empty():
        msg = print_queue.get()
        return JSONResponse({"message": msg, "chat_status": chat_status})
    else:
        return JSONResponse({"message": None, "chat_status": chat_status})


# Function to handle the conversation asynchronously
async def run_chat():
    global chat_status
    try:
        # Use the `start_agent_conversation_stream` to start the agent conversation
        async for message in start_agent_conversation_stream():
            # Format and put messages in print_queue for the frontend to fetch
            print_queue.put(message)

        chat_status = "Chat ended"
    except Exception as e:
        chat_status = "error"
        print_queue.put(json.dumps({"error": str(e)}))


# Route to download CSV recommendations
@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"  # Path to the CSV file
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}


# Route to stream conversation using Server-Sent Events (SSE)
@router.get("/api/stream-conversation")
async def stream_conversation():
    async def event_stream():
        while True:
            if not print_queue.empty():
                message = print_queue.get()
                yield f"data: {message}\n\n"
            await asyncio.sleep(1)  # Small delay to avoid overwhelming the client
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

