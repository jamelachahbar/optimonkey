from pydantic import BaseModel, Field
from typing import List, Optional
import instructor
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the structured data model using Pydantic
class AzureResourceUsage(BaseModel):
    resource_name: List[str]
    resource_type: List[str]
    usage_metrics: Optional[List[str]] = Field(default_factory=list)
    recommendations: Optional[List[str]] = Field(default_factory=list)

# Function to initialize the instructor client
# Initialize Instructor client with AzureOpenAI
def get_instructor_client():
    return instructor.from_openai(AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
    ))

client = get_instructor_client()


# Function to extract Azure resource details
def extract_azure_resource_details(client, user_message_content: str):
    messages = [{"role": "user", "content": user_message_content}]
    
    # Call instructor to process and extract structured data
    user_message = client.chat.completions.create(
        model="gpt-4o-mini",  # Ensure you are using the correct GPT model
        response_model=AzureResourceUsage,
        messages=messages
    )

    # Return the structured response
    return {
        "resource_name": user_message.resource_name,
        "resource_type": user_message.resource_type,
        "usage_metrics": user_message.usage_metrics,
        "recommendations": user_message.recommendations
    }


# test it
# client = get_instructor_client()
# user_message_content = """
# We've successfully retrieved the metrics for each VM. Based on the collected data, all VMs seem to have very low usage for CPU, Network, and Disk over the last 30 days. Here's how we can interpret and report these findings, including cost-saving recommendations:

# Results and Recommendations
# Low Usage Detected:

# All VMs have 0% usage in CPU, Network In, Network Out, and Disk Read/Write metrics.
# Top 5 Underutilized VMs:

# Since all detected metrics are at 0%, all VMs in the list qualify as underutilized.
# Recommendations:

# VM-LINUX-01, vmwithhibernationmode, vm-forcedetachdemo1-1, vm-forcedetachdemo1-2, vm-forcedetachdemo1-3, vmacoademospot, vmencrypted1, vmtest, Sample-VM:
# Opt to shut down or deallocate VMs when not in use: This can lead to significant savings by reducing compute costs.
# Consider resizing or downgrading these VMs: If these were expected to have low usage for specific periods and don't need high performance consistently, resizing could be a cost-efficient solution.
# Output
# Let's store these findings and recommendations to a CSV file to provide to the user:

# import pandas as pd

# # Sample data preparation based on observations and recommendations
# results = [
#     {"vm_name": "VM-LINUX-01", "cpu_usage": "0%", "network_usage": "None", "disk_usage": "None", "recommendation": "Shut down or deallocate if not in use"},
#     {"vm_name": "vmwithhibernationmode", "cpu_usage": "10%", "network_usage": "None", "disk_usage": "None", "recommendation": "Shut down or deallocate if not in use"},
#     {"vm_name": "vm-forcedetachdemo1-1", "cpu_usage": "0%", "network_usage": "None", "disk_usage": "None", "recommendation": "Shut down or deallocate if not in use"},
#     {"vm_name": "vm-forcedetachdemo1-2", "cpu_usage": "0%", "network_usage": "None", "disk_usage": "None", "recommendation": "Shut down or deallocate if not in use"},
#     {"vm_name": "vm-forcedetachdemo1-3", "cpu_usage": "0%", "network_usage": "None", "disk_usage": "None", "recommendation": "Shut down or deallocate if not in use"}
# ]

# # Convert to DataFrame
# df = pd.DataFrame(results)

# # Save to CSV
# df.to_csv('underutilized_vms_recommendations.csv', index=False)
# Let's execute this code to generate the output CSV file with the recommendations.

# """
# response = extract_azure_resource_details(client, user_message_content)
# print(response)





