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
    resource_name: str
    resource_type: str
    usage_metrics: Optional[dict]
    recommendations: Optional[List[str]] = Field(default_factory=list)

# Function to initialize the instructor client
def get_instructor_client():
    client = instructor.from_openai(AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version="2023-09-15-preview",
        azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
    ))
    return client

# Function to extract Azure resource details
def extract_azure_resource_details(client, user_message_content: str):
    messages = [{"role": "user", "content": user_message_content}]
    
    # Call instructor to process and extract structured data
    user_message = client.chat.completions.create(
        model="gpt-4o",  # Ensure you are using the correct GPT model
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








