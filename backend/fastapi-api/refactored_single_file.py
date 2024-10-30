
import os
import json
import queue
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from azure.mgmt.monitor import MonitorManagementClient
from dotenv import load_dotenv
import autogen
import threading
from queue import Queue

# --- Initialize Environment Variables ---
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Configuration and credentials
subscription_id = "38c26c07-ccce-4839-b504-cddac8e5b09d"
llm_config = {
    "config_list": autogen.config_list_from_json("./agents/OAI_CONFIG_LIST.json"),
    "cache_seed": 0,
    "timeout": 180
}

# --- AGENT SETUP ---
# Initialize agents
user_proxy = autogen.UserProxyAgent(
    name="admin",
    human_input_mode='NEVER',
    system_message='Give task and send instruction to the critic to evaluate code.',
    code_execution_config=False
)
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="Plan tasks and ensure steps are executed correctly using Python and Azure SDKs.",
    llm_config=llm_config
)
coder = autogen.AssistantAgent(
    name="Code_Guru",
    system_message="Write and evaluate code using Azure SDKs.",
    llm_config=llm_config,
    human_input_mode="NEVER"
)
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="Critique code and provide score based on best practices.",
    llm_config=llm_config
)
code_executor = autogen.UserProxyAgent(
    name="Executor",
    code_execution_config={"use_docker": "python:3.10"},
    llm_config=llm_config
)

# Initialize GroupChat with the agents
groupchat = autogen.GroupChat(
    agents=[planner, coder, critic, user_proxy, code_executor],
    messages=[],
    max_round=50,
    speaker_selection_method="round_robin"
)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# --- FASTAPI SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- Queue Management for WebSocket ---
print_queue = Queue()
user_queue = Queue()
chat_status = "ended"
connections = {}

@app.websocket("/ws/conversation")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)
    connections[client_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from client {client_id}: {data}")

            user_queue.put(data)
            await websocket.send_text(json.dumps({"message": "Processing message..."}))

    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")
        del connections[client_id]
    except Exception as e:
        print(f"Error: {e}")

# Function to handle agent conversations asynchronously
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
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    }
                    websocket_connections = list(connections.values())
                    for websocket in websocket_connections:
                        await websocket.send_text(json.dumps(msg_content))
                    await asyncio.sleep(0.1)
            await asyncio.sleep(1)
    except Exception as e:
        chat_status = "error"
        error_message = {
            "content": f"An error occurred: {str(e)}",
            "role": "system",
            "name": "Error",
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        for websocket in websocket_connections:
            await websocket.send_text(json.dumps(error_message))

@app.post("/api/start-agents")
async def start_agents(background_tasks: BackgroundTasks):
    global chat_status
    try:
        if chat_status == 'error':
            chat_status = 'ended'
        user_queue.queue.clear()
        print_queue.queue.clear()

        background_tasks.add_task(run_chat)
        chat_status = "chat_ongoing"
        return JSONResponse({"status": chat_status})
    except Exception as e:
        chat_status = "error"
        return JSONResponse({"status": "error", "error": str(e)})

@app.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}

# Function to start agent conversation
async def start_agent_conversation_stream(prompt: Optional[str] = None):
    global chat_status
    chat_status = "Chat ongoing"
    
    if not prompt:
        prompt = "Analyze the Azure environment and provide optimization recommendations."

    try:
        validation_responses = await start_prompt_validation(prompt)
        avg_confidence = sum(r.get("confidence_score", 0) for r in validation_responses) / len(validation_responses)

        if avg_confidence >= 3:
            chat_result = user_proxy.initiate_chat(manager, message=prompt, max_round=50, clear_history=True)
            for message in chat_result['messages']:
                yield message.get('content')
        else:
            yield "Prompt validation failed."

    except Exception as e:
        yield f"Error: {str(e)}"
