from fastapi import APIRouter, Response
from agents.optimonkeyagents import start_agent_conversation  # Import your agent function
import os

router = APIRouter()

@router.post("/start-agents")
async def start_agents():
    conversation = start_agent_conversation()
    return {"conversation": conversation}
@router.get("/download-recommendations")
async def download_recommendations():
    csv_file_path = "azure_cost_optimization_recommendations.csv"  # Update the file path as necessary
    if os.path.exists(csv_file_path):
        return Response(open(csv_file_path, "rb").read(), media_type="text/csv")
    return {"error": "CSV file not found"}