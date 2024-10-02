from fastapi import APIRouter, Response
from agents.optimonkeyagents import start_agent_conversation  # Import your agent function
from pydantic import BaseModel
import os

router = APIRouter()

# Define a Pydantic model for receiving custom prompt data
class PromptInput(BaseModel):
    prompt: str

@router.post("/start-agents")
async def start_agents():
    try:
        conversation = start_agent_conversation()  # No custom prompt, use default
        return {"conversation": conversation}  # Return it as JSON
    except Exception as e:
        return {"error": str(e)}

@router.post("/start-agents-with-prompt")
async def start_agents_with_prompt(prompt_input: PromptInput):
    try:
        conversation = start_agent_conversation(prompt_input.prompt)  # Use the custom prompt
        return {"conversation": conversation}
    except Exception as e:
        return {"error": str(e)}

@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"  # Update the file path as necessary
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}
    
# Define a Pydantic model for receiving the message data
class MessageInput(BaseModel):
    message: str

# Define the /send-message route
@router.post("/send-message")
async def send_message(message_input: MessageInput):
    # Pass the message to the start_agent_conversation function
    try:
        conversation = start_agent_conversation(message_input.message)  # Call your autogen conversation function
        return {"conversation": conversation}  # Return the updated conversation as JSON
    except Exception as e:
        return {"error": str(e)}
