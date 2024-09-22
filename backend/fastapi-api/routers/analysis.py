# routers/analysis.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis")
def analyze_azure_resources():
    # Mocked results, replace this with real data later
    results = [
        {
            "id": 1,
            "resource_name": "VM1",
            "resource_group": "GroupA",
            "cost_saving": "$500",
            "recommendation": "Decommission unused disk"
        },
        {
            "id": 2,
            "resource_name": "StorageAccount1",
            "resource_group": "GroupB",
            "cost_saving": "$1200",
            "recommendation": "Reduce access tiers"
        }
    ]
    return results
