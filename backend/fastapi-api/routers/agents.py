import json
import queue
import os
import asyncio
from datetime import datetime
from fastapi import APIRouter, Response, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from agents.optimonkeyagents import start_agent_conversation_stream, initiate_final_recommendation

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
    global chat_status
    conversation_data = []

    try:
        data = await websocket.receive_text()  # Client's initial message
        print(f"Received from client: {data}")

        async for message in start_agent_conversation_stream(data):
            print(f"Sending message to frontend: {message}")  # Debug log
            conversation_data.append(message)
            await websocket.send_text(json.dumps(message))

        # Final recommendations
        if conversation_data:
            print(f"Passing conversation data to final recommendation: {conversation_data}")
            async for final_message in initiate_final_recommendation(conversation_data):
                print(f"Final recommendation message: {final_message}")
                await websocket.send_text(json.dumps(final_message))

        chat_status = "ended"

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del connections[client_id]
        chat_status = "ended"
    except Exception as e:
        print(f"Error in WebSocket: {e}")
        await websocket.send_text(json.dumps({"content": f"Error: {str(e)}", "role": "system", "name": "Error"}))
    finally:
        del connections[client_id]
        chat_status = "ended"
        print(f"WebSocket connection {client_id} closed.")



# OLD
# @router.websocket("/ws/conversation")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     client_id = id(websocket)
#     connections[client_id] = websocket
#     global chat_status  # Access global chat status
#     conversation_data = []  # Store conversation data for final recommendations

#     try:
#         # Listen for messages from the client
#         data = await websocket.receive_text()
#         print(f"Received message from client: {data}")

#         # Start a new conversation if chat_status is not "chat_ongoing"
#         if chat_status != "chat_ongoing":
#             chat_status = "chat_ongoing"
#             with print_queue.mutex:
#                 print_queue.queue.clear()
#             with user_queue.mutex:
#                 user_queue.queue.clear()

#         # Trigger the main agent conversation
#         async for message in start_agent_conversation_stream(data):
#             print(f"Main conversation message: {message}")  # Log main conversation messages
#             # Store conversation data for later use
#             conversation_data.append(message)

#             # Stream each message to the client
#             await websocket.send_text(json.dumps(message))

#             # Check for termination of the first group chat
#             if message.get("content") == "TERMINATE":
#                 print("First group chat has ended. Proceeding to final recommendations.")
#                 break

#         # Ensure conversation_data has content before initiating final recommendations
#         if not conversation_data:
#             error_message = "No messages collected during the main conversation. Cannot proceed to final recommendations."
#             print(error_message)
#             await websocket.send_text(json.dumps({
#                 "content": error_message,
#                 "role": "system",
#                 "name": "Error",
#                 "timestamp": datetime.now().strftime("%H:%M:%S")
#             }))
#             return

#         # Trigger final recommendations
#         try:
#             print(f"Initiating final recommendations with collected data: {conversation_data}")
#             async for final_message in initiate_final_recommendation(conversation_data):
#                 # Handle final recommendations
#                 if final_message.get("content") == "FINAL_RECOMMENDATIONS_COMPLETE":
#                     print("Final recommendations phase completed.")
#                     await websocket.send_text(json.dumps({
#                         "content": "Final recommendations have been generated.",
#                         "role": "system",
#                         "name": "System",
#                         "timestamp": datetime.now().strftime("%H:%M:%S"),
#                         "final_recommendations": True
#                     }))
#                     break
#                 await websocket.send_text(json.dumps(final_message))
#         except Exception as e:
#             print(f"Error during final recommendations phase: {e}")
#             await websocket.send_text(json.dumps({
#                 "content": f"Error during final recommendations phase: {str(e)}",
#                 "role": "system",
#                 "name": "Error",
#                 "timestamp": datetime.now().strftime("%H:%M:%S")
#             }))

#         # Send a final message to indicate the entire process has completed
#         await websocket.send_text(json.dumps({
#             "content": "Conversation completed with final recommendations.",
#             "role": "system",
#             "name": "System",
#             "timestamp": datetime.now().strftime("%H:%M:%S"),
#             "final_recommendations": True
#         }))

#         chat_status = "ended"  # Mark chat as ended after final recommendations
#         print("Final recommendations sent. Keeping WebSocket open momentarily.")
#         await asyncio.sleep(1)  # Delay to ensure message reaches client

#     except WebSocketDisconnect:
#         print(f"Client {client_id} disconnected")
#         del connections[client_id]
#         chat_status = "ended"
#     except Exception as e:
#         print(f"Unexpected error: {e}")
#     finally:
#         # Ensure cleanup and reset
#         del connections[client_id]
#         chat_status = "ended"
#         print(f"Connection {client_id} cleaned up. Chat status reset.")

# Other endpoint definitions remain unchanged

async def run_chat():
    # Define the logic for the run_chat function here
    pass

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
        print(f"Downloading CSV file: {csv_file_path}")  # Log file download
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    print("CSV file not found.")  # Log missing file
    return {"error": "CSV file not found"}

@router.post("/api/send_message")
async def send_message(request: Request):
    body = await request.json()
    user_input = body.get("message", "")
    if user_input:
        user_queue.put(user_input)
        print(f"Message received and added to queue: {user_input}")  # Log message
        return JSONResponse({"status": "Message Received"})
    print("Error: No message provided in send_message request.")
    return JSONResponse({"status": "Error", "message": "No message provided"}, status_code=400)
