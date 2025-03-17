import json
from typing import Optional, Any
import re
import asyncio
import logging
from enum import Enum
from pydantic import BaseModel, Field, validator
import os
import sys
import dotenv
import instructor
from openai import AzureOpenAI
from typing import List, Optional

# Load environment variables
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper function to check environment variables
def check_environment_variables():
    # Check for API key (either old or new variable name)
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    if not api_key:
        logger.error("Missing API key - ensure AZURE_OPENAI_API_KEY or AZURE_OPENAI_KEY is set")
    else:
        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "****"
        logger.info(f"Azure OpenAI API Key: {masked_key}")
    
    # Check for endpoint (either old or new variable name)
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_API_BASE")
    if not azure_endpoint:
        logger.error("Missing endpoint - ensure AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_BASE is set")
    else:
        logger.info(f"Azure OpenAI Endpoint: {azure_endpoint}")
    
    # Log API version
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    logger.info(f"Azure OpenAI API Version: {api_version}")
    
    # Log deployment name
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    logger.info(f"Azure OpenAI Deployment Name: {deployment_name}")

# Run environment check
check_environment_variables()

# Get environment variables with error handling
def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        logger.error(f"Missing required environment variable: {name}")
        raise ValueError(f"Missing required environment variable: {name}")
    return value

# Initialize the Azure client for use with instructor
try:
    # Initialize AzureOpenAI client
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("AZURE_OPENAI_API_BASE")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    if not api_key:
        logger.error("Missing API key - ensure AZURE_OPENAI_API_KEY or AZURE_OPENAI_KEY is set")
        raise ValueError("Missing required API key")
    
    if not azure_endpoint:
        logger.error("Missing endpoint - ensure AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_BASE is set")
        raise ValueError("Missing required endpoint")
    
    logger.info(f"Initializing AzureOpenAI client with endpoint: {azure_endpoint}")
    
    # Initialize the AzureOpenAI client
    azure_client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=azure_endpoint
    )
    
    # Then wrap it with instructor - use simple initialization
    try:
        client = instructor.from_openai(azure_client)
        logger.info("AzureOpenAI client initialized successfully with instructor wrapper")
    except Exception as e:
        logger.warning(f"Failed to initialize instructor wrapper: {e}")
        client = azure_client
        logger.info("Using raw AzureOpenAI client without instructor wrapper")
    
except Exception as e:
    logger.error(f"Failed to initialize AzureOpenAI client: {str(e)}")
    azure_client = None
    client = None
    logger.warning("Will use fallback validation without AI")

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

    # Add a validator to handle string inputs for confidence_score
    @validator('confidence_score', pre=True)
    def parse_confidence_score_input(cls, value: Any) -> ConfidenceScore:
        """Parse and convert the confidence score to the correct enum type."""
        if isinstance(value, str):
            try:
                # Try to convert string to int
                value_as_int = int(value)
                if 1 <= value_as_int <= 4:
                    return ConfidenceScore(value_as_int)
            except (ValueError, TypeError):
                # Try to match string names
                value_upper = value.upper()
                for enum_val in ConfidenceScore:
                    if enum_val.name == value_upper:
                        return enum_val
                # Try aliases
                value_map = {
                    "VERY_HIGH": ConfidenceScore.EXCELLENT,
                }
                if value_upper in value_map:
                    return value_map[value_upper]
                
        # If it's already a ConfidenceScore enum, return as is
        if isinstance(value, ConfidenceScore):
            return value
            
        # If it's an integer, convert to enum
        if isinstance(value, int) and 1 <= value <= 4:
            return ConfidenceScore(value)
            
        # Default to LOW for unrecognized values
        return ConfidenceScore.LOW

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
        logger.info(f"Task sent to {reviewer_name}: {prompt}")
        
        # Check if we have a client available
        if not 'client' in globals() or client is None:
            logger.warning("No OpenAI client available. Using fallback validation.")
            # Fall back to basic validation based on subscription IDs
            found_subscription_ids = search_subscription_id(prompt)
            if found_subscription_ids:
                confidence = ConfidenceScore.MEDIUM if len(found_subscription_ids) == 1 else ConfidenceScore.HIGH
                explanation = f"Found {len(found_subscription_ids)} subscription ID(s): {', '.join(found_subscription_ids)}. Basic validation only (no AI client available)."
            else:
                confidence = ConfidenceScore.LOW
                explanation = "No subscription IDs found in prompt. Basic validation only (no AI client available)."
            
            return ReviewResponse(
                confidence_score=confidence,
                explanation=explanation
            )
        
        # Otherwise, proceed with normal AI-based validation
        # Search for all subscription IDs in the prompt
        found_subscription_ids = search_subscription_id(prompt)
        
        # Try to get a structured response
        try:
            # Attempt to use instructor with the ResponseModel
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
            
            # If we get here with a ReviewResponse, we're good
            if isinstance(response, ReviewResponse):
                logger.info(f"Received a valid ReviewResponse object: {response}")
                return response
                
        except Exception as instructor_error:
            # If instructor-specific usage fails, fall back to raw completion
            logger.warning(f"Error using instructor with response_model: {instructor_error}")
            logger.info("Falling back to raw completion API")
            
            # Use raw completion API without instructor
            try:
                raw_response = azure_client.chat.completions.create(
                    model="gpt-4o-mini",
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
                
                if hasattr(raw_response, 'choices') and raw_response.choices:
                    raw_content = raw_response.choices[0].message.content
                    logger.info(f"Raw completion content: {raw_content}")
                    
                    # Try to parse the raw JSON
                    try:
                        data = json.loads(raw_content)
                        # Create ReviewResponse manually
                        return ReviewResponse(
                            confidence_score=data.get("confidence_score", 1),
                            explanation=data.get("explanation", "No explanation provided")
                        )
                    except (json.JSONDecodeError, Exception) as e:
                        logger.error(f"Error parsing raw response: {e}")
                        
            except Exception as raw_error:
                logger.error(f"Error with raw completion: {raw_error}")
        
        # If we're still here, manually handle any response we received
        # This is a fallback for any response format
        
        # Check if response is a dict
        if isinstance(response, dict):
            logger.info("Response is a dictionary, attempting to extract values")
            
            # Try to extract confidence_score and explanation directly
            if "confidence_score" in response and "explanation" in response:
                try:
                    return ReviewResponse(
                        confidence_score=response["confidence_score"],
                        explanation=response["explanation"]
                    )
                except Exception as e:
                    logger.error(f"Error creating ReviewResponse from dict: {e}")
            
            # Check if it has the OpenAI API structure
            if "choices" in response and response["choices"]:
                try:
                    choices_content = response["choices"][0]
                    if isinstance(choices_content, dict) and "message" in choices_content:
                        message_content = choices_content["message"]
                        
                        if isinstance(message_content, dict) and "content" in message_content:
                            content_str = message_content["content"]
                            
                            try:
                                content_json = json.loads(content_str)
                                return ReviewResponse(
                                    confidence_score=content_json.get("confidence_score", 1),
                                    explanation=content_json.get("explanation", "No explanation provided")
                                )
                            except json.JSONDecodeError:
                                logger.error(f"Failed to parse message content as JSON: {content_str}")
                except Exception as e:
                    logger.error(f"Error parsing choices: {e}")
        
        # Final fallback
        logger.error("All parsing attempts failed, returning LOW confidence")
        return ReviewResponse(
            confidence_score=ConfidenceScore.LOW,
            explanation="Failed to parse response properly"
        )

    except Exception as e:
        logger.error(f"Validation error for {reviewer_name}: {str(e)}")
        return ReviewResponse(confidence_score=ConfidenceScore.LOW, explanation=str(e))

# Main function to start prompt validation with a single reviewer
async def start_prompt_validation(prompt=None):
    """
    Validate a prompt and provide a confidence score and board decision.
    
    Parameters:
    - prompt: The prompt text to validate. If None, a default prompt is used.
    
    Returns:
    A dictionary containing:
    - confidence_score: Integer from 1-4 
    - explanation: Detailed explanation of the validation result
    - board_decision: String indicating if the prompt passed or failed review ("PASS" or "FAIL")
    - score_name: String representation of the confidence score (LOW, MEDIUM, HIGH, EXCELLENT)
    
    Note:
    - Prompts with confidence scores of MEDIUM (2) or higher will PASS
    - Prompts with confidence scores of LOW (1) will FAIL
    """
    if prompt is None:
        prompt = "Please provide a valid subscription ID to estimate costs."
    
    try:
        # Run validation with a single reviewer
        try:
            # Try async approach first
            review_result = await asyncio.to_thread(validate_prompt_with_instructor, prompt, "Security Reviewer")
        except Exception as async_error:
            # Fall back to direct call if asyncio fails
            logger.warning(f"Async execution failed: {async_error}. Trying synchronous call.")
            review_result = validate_prompt_with_instructor(prompt, "Security Reviewer")
        
        # Extract the confidence score value
        if isinstance(review_result.confidence_score, ConfidenceScore):
            confidence_score_value = review_result.confidence_score.value
        else:
            # Parse the value if it's not already an enum
            confidence_score_value = parse_confidence_score(review_result.confidence_score).value
        
        # Get the enum name
        score_name = ConfidenceScore(confidence_score_value).name
        
        # Determine board decision based on confidence score
        board_decision = "PASS" if confidence_score_value >= ConfidenceScore.MEDIUM.value else "FAIL"
        
        # Add more specific decision text for better UI display
        decision_text = f"FinOps Governing Board {board_decision} - Confidence Score: {score_name}"
        
        # Select appropriate icon
        icon = "✅" if confidence_score_value >= ConfidenceScore.HIGH.value else "⚠️" if confidence_score_value == ConfidenceScore.MEDIUM.value else "❌"
        
        # Format the result message
        result_message = f"{icon} Confidence Score: {confidence_score_value}/4 ({score_name})\n"
        result_message += f"Board Decision: {board_decision}\n"
        result_message += f"Explanation: {review_result.explanation}"
        
        print(result_message)
        
        # Return clean dictionary
        return {
            "confidence_score": confidence_score_value,
            "explanation": review_result.explanation,
            "board_decision": decision_text,  # Use the more specific text
            "score_name": score_name
        }
    except Exception as e:
        # Handle any errors
        logger.error(f"Validation failed: {e}")
        return {
            "confidence_score": 1,
            "explanation": f"Validation error: {str(e)}",
            "board_decision": "FinOps Governing Board FAIL - Validation Error",
            "score_name": "LOW"
        }

# Function to convert string values to proper enum integers - uses the validator logic
def parse_confidence_score(value):
    """Parse confidence score values to the correct enum type using the validator logic."""
    return ReviewResponse.parse_confidence_score_input(None, value)
