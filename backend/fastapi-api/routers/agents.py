from fastapi import APIRouter, Response
from agents.optimonkeyagents import start_agent_conversation  # Import your agent function
import os

router = APIRouter()

@router.post("/start-agents")
async def start_agents():
    try:
        conversation = start_agent_conversation()  # Ensure this returns conversation data
        return {"conversation": conversation}  # Return it as JSON
    except Exception as e:
        return {"error": str(e)}
@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_analysis_results.csv"  # Update the file path as necessary
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}