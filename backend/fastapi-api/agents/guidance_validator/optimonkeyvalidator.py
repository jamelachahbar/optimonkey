import json
from typing import Optional
import re
import asyncio
import logging
from enum import Enum
from pydantic import BaseModel, Field
import os
import instructor
from openai import AzureOpenAI
from typing import List, Optional
# Initialize Instructor client with AzureOpenAI
client = instructor.from_openai(AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
))

# Enum for Confidence Levels
class ConfidenceScore(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXCELLENT = 4

# Define the structured response model
class ReviewResponse(BaseModel):
    confidence_score: ConfidenceScore
    explanation: str = Field(..., description="Explanation of the confidence score.")
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

# Function to validate prompt with OpenAI and parse the response
def validate_prompt_with_instructor(prompt: str, reviewer_name: str = "Reviewer") -> ReviewResponse:
    try:
        logging.info(f"Task sent to {reviewer_name}: {prompt}")
                    # Search for all subscription IDs in the prompt
        found_subscription_ids = search_subscription_id(prompt)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_model=ReviewResponse,
            max_retries=3,
            messages=[
                {"role": "system", "content": "You are an Azure cost optimization expert. Review the prompt and provide feedback."},
                {
                    "role": "user",
                    "content": (
                        f"{reviewer_name}, please review the following prompt:\n\n\"{prompt}\"\n\n"
                        "Do not include any additional text outside the JSON object. "
                        f"Valid subscription IDs found: {found_subscription_ids}. If no IDs are found, the confidence score should be lower.\n\n"
                        "Respond strictly in JSON format:\n{\n"
                        "  \"confidence_score\": <integer between 1-4>,\n"
                        "  \"explanation\": \"<detailed explanation>\"\n"
                        "}"
                    ),
                },
            ],
        )

        # Check if the response is already in the form of a ReviewResponse object
        if isinstance(response, ReviewResponse):
            # Directly return the ReviewResponse as it's already structured
            return response

        # Debugging: Log the type and structure of the response to handle other cases
        print("Response Type:", type(response))
        print("Response Content:", response)

        # Handle case where response might be a dict
        if isinstance(response, dict):
            if "choices" in response and response["choices"]:
                response_data = json.loads(response["choices"][0]["message"]["content"])
            else:
                # If there's no 'choices', assume response data is directly in response
                response_data = response
        else:
            logging.error("Invalid response structure; response does not contain expected data.")
            return ReviewResponse(confidence_score=ConfidenceScore.LOW, explanation="Invalid response format or data not found.")

        # Extract the confidence score and explanation from the parsed data
        confidence_score_value = response_data.get("confidence_score", 0)
        explanation = response_data.get("explanation", "No explanation provided")

        # Map the integer confidence_score_value to the ConfidenceScore enum
        confidence_score = ConfidenceScore(confidence_score_value)

        return ReviewResponse(confidence_score=confidence_score, explanation=explanation)

    except Exception as e:
        logging.error(f"Validation error for {reviewer_name}: {str(e)}")
        return ReviewResponse(confidence_score=ConfidenceScore.LOW, explanation=str(e))

# Main function to start prompt validation with a single reviewer
async def start_prompt_validation(prompt: Optional[str] = None):
    if not prompt:
        prompt = (
            "Your role is to analyze the Azure environment for cost savings based on activity and usage. "
            "The prompt should be clear, with goals and objectives related to cost optimization."
        )

    print(f"Starting validation with prompt: {prompt}")
    try:
        # Run validation with one reviewer and 3 retries
        validation_response = await asyncio.to_thread(validate_prompt_with_instructor, prompt, "Reviewer")

        # Check if the validation response is valid
        if validation_response and isinstance(validation_response, ReviewResponse):
            confidence_score = validation_response.confidence_score
            explanation = validation_response.explanation

            # Display results and handle response based on confidence score
            icon = "✅" if confidence_score in [ConfidenceScore.HIGH, ConfidenceScore.EXCELLENT] else "⚠️" if confidence_score == ConfidenceScore.MEDIUM else "❌"
            print(f"{icon} Confidence Score: {confidence_score.name} - {explanation}")

            if confidence_score in [ConfidenceScore.HIGH, ConfidenceScore.EXCELLENT]:
                print(f"✅ FinOps Governing Board Approved - Confidence Score: {confidence_score.name}")
                # Return success response and stop further error handling
                return {"confidence_score": confidence_score, "explanation": explanation}
            else:
                print(f"❌ FinOps Governing Board Rejected - Confidence Score: {confidence_score.name}")
                return {"confidence_score": confidence_score, "explanation": explanation}
        else:
            # If the response is invalid, log and handle it accordingly
            logging.error("Validation failed: No valid response received.")
            return {"confidence_score": ConfidenceScore.LOW, "explanation": "No valid response received from validation."}

    except Exception as e:
        logging.error(f"Error during validation: {e}")
        return {"confidence_score": ConfidenceScore.LOW, "explanation": str(e)}
