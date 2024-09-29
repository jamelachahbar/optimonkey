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
