import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from agents.optimonkeyagents import start_agent_conversation  # Import the start_agent_conversation from your agents module

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint to handle agent conversations dynamically.
    """
    await websocket.accept()
    logging.info("WebSocket connection accepted")

    try:
        while True:
            # Receive message from the client (user input)
            data = await websocket.receive_text()

            # Initiate the agent conversation
            async for response in start_agent_conversation(data, websocket):
                if response.get("content"):
                    # Send the message content back to the client via WebSocket
                    await websocket.send_text(json.dumps(response))
                    logging.info(f"Sent message: {response}")

    except WebSocketDisconnect:
        logging.warning("Client disconnected")
    finally:
        logging.info("WebSocket connection closed")
