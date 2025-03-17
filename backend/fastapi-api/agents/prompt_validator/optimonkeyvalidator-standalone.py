import re
import json
import logging
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor
import asyncio
import openai
import os
from typing import List, Optional

# Initialize OpenAI API
openai.api_type = "azure"
openai.api_version = "2023-09-15-preview"  # Or the version you're using
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
openai.azure_endpoint = os.getenv("AZURE_OPENAI_API_BASE")

# logging.basicConfig(level=logging.INFO)

# Define the response structure for validation
class Response(BaseModel):
    confidence_score: int
    explanation: str

# Validate whether the response contains a valid JSON object
def is_valid_json(json_str: str) -> bool:
    try:
        json.loads(json_str)
        return True
    except ValueError:
        return False

# Function to validate the prompt using Azure OpenAI API
from openai import AzureOpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
)

# Validate subscription ID from the prompt message
def validate_subscription_id(prompt: str) -> bool:
    pattern = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    match = re.search(pattern, prompt)
    return match is not None

# Search for subscription IDs in the prompt message
def search_subscription_id(prompt: str) -> List[str]:
    # Adjusted pattern to match UUIDs (subscription IDs) that may not be surrounded by JSON structure
    pattern = r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    matches = re.findall(pattern, prompt)
    return matches

# Use the validation function on subscription IDs in the guidance validation function
def validate_prompt_with_guidance(prompt: str, reviewer_name: str) -> dict:
    try:
        logging.info(f"Task sent to {reviewer_name}: {prompt}")

        # Search for all subscription IDs in the prompt
        found_subscription_ids = search_subscription_id(prompt)
        has_subscription_id = len(found_subscription_ids) > 0

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Ensure you use the correct model name
            messages=[
                {
                    "role": "system",
                    "content": "You are an Azure cost optimization expert."
                },
                {
                    "role": "user",
                    "content": (
                        f"{reviewer_name}, please review the following prompt for Azure cost optimization:\n\n"
                        f"\"{prompt}\"\n\n"
                        f"Make sure to respond strictly in the following JSON format:\n\n"
                        "{\n"
                        "  \"confidence_score\": <integer between 0-5>,\n"
                        "  \"explanation\": \"<your explanation here>\"\n"
                        "}\n\n"
                        "Do not include any additional text outside the JSON object. "
                        f"Valid subscription IDs found: {found_subscription_ids}. If no IDs are found, the confidence score should be lower.\n\n"
                        "Example response:\n"
                        '{\n'
                        '  "confidence_score": 4,\n'
                        '  "explanation": "Your explanation here."\n'
                        '}'
                    )
                }
            ]
        )

        response_text = response.choices[0].message.content.strip()
        logging.info(f"{reviewer_name} raw response: {response_text}")

        # Clean up the response (optional)
        response_text = response_text.replace("\n", "").strip()  # Remove newlines

        # Validate the JSON format
        if is_valid_json(response_text):
            validation_response = json.loads(response_text)
            # Adjust confidence score if no subscription IDs were found
            if not has_subscription_id:
                validation_response['confidence_score'] = max(0, validation_response['confidence_score'] - 2)  # Decrease score if no ID

            return validation_response
        else:
            logging.error(f"{reviewer_name} returned an invalid JSON response.")
            return {
                "confidence_score": 0,
                "explanation": "Invalid JSON format. Please provide a valid JSON response without any additional text."
            }

    except Exception as e:
        logging.error(f"Validation error in {reviewer_name}: {str(e)}")
        return {"confidence_score": 0, "explanation": str(e)}

# Run guidance in a separate thread
async def run_guidance_in_executor(prompt: str, reviewer_name: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, validate_prompt_with_guidance, prompt, reviewer_name)

# Summarize explanations from multiple reviewers
def summarize_explanations(explanations: List[str]) -> str:
    try:
        prompt = (
            "Please provide a concise summary of the following reviewers' explanations:\n\n"
            + "\n\n".join([f"Reviewer {i+1}: {exp}" for i, exp in enumerate(explanations)])
            + "\n\nSummary:"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Ensure you use the correct model name
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that summarizes text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.5,
        )

        summary = response.choices[0].message.content.strip()
        return summary

    except Exception as e:
        logging.error(f"Error during summarization: {e}")
        return "An error occurred during summarization."

# Main function to start the conversation and validate the prompt
async def start_prompt_validation(prompt: Optional[str] = None):
    global chat_status
    chat_status = "Chat ongoing"

    if not prompt:
        prompt = """
        Help me make more money on crypto trading. I have $1000 to invest. What should I do?
        """
        
    print(f"Starting conversation with prompt: {prompt}")
    try:
        reviewer1_response = await run_guidance_in_executor(prompt, "Reviewer1")
        reviewer2_response = await run_guidance_in_executor(prompt, "Reviewer2")
        reviewer3_response = await run_guidance_in_executor(prompt, "Reviewer3")

        logging.info(f"Reviewer1 Response (type: {type(reviewer1_response)}): {reviewer1_response}")
        logging.info(f"Reviewer2 Response (type: {type(reviewer2_response)}): {reviewer2_response}")
        logging.info(f"Reviewer3 Response (type: {type(reviewer3_response)}): {reviewer3_response}")

        # Check if reviewer response is a dict and contains the expected fields
        if isinstance(reviewer1_response, dict):
            confidence_scores = [
                reviewer1_response.get("confidence_score", 0),
                reviewer2_response.get("confidence_score", 0),
                reviewer3_response.get("confidence_score", 0)
            ]
        else:
            logging.error(f"Unexpected reviewer1 response: {reviewer1_response}")
            raise ValueError(f"Unexpected response format from reviewer1: {type(reviewer1_response)}")

        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        explanations = [
            reviewer1_response.get("explanation", ""),
            reviewer2_response.get("explanation", ""),
            reviewer3_response.get("explanation", "")
        ]
        summary = summarize_explanations(explanations)

        if avg_confidence >= 3:
            print(f"""✅ FinOps Governing Board Approved - Valid prompt.
    Average Confidence Score: {avg_confidence:.1f}

    Reviewer Evaluations Summary:
    {summary}

    Proceeding to group chat.""")
            return True  # Validation passed
        else:
            print(f"""❌ FinOps Governing Board Rejected - Average confidence too low.
    Average Confidence Score: {avg_confidence:.1f}

    Reviewer Evaluations Summary:
    {summary}

    Please provide a valid prompt.""")
            return False  # Validation failed

    except Exception as e:
        logging.error(f"Error during validation: {e}")
        return False
    
# Run the conversation asynchronously
# Run the asynchronous function
# Define the prompt you want to test
prompt = """
Help me optimize costs in Azure for this subscription: 000013213-0000-0000-0000-000000000000
"""
if __name__ == "__main__":
    asyncio.run(start_prompt_validation(prompt))