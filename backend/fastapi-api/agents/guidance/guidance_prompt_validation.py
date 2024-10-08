import guidance
from guidance import select, gen
from autogen import Agent, AssistantAgent, UserProxyAgent, config_list_from_json
from guidance import models

# Load LLM configuration from the specified JSON file
llm_config = config_list_from_json("./agents/OAI_CONFIG_LIST.json")[1]

# Step 1: Define the PromptValidationAgent using guidance
class PromptValidationAgent:
    def __init__(self, guidance_model):
        # Initialize the PromptValidationAgent with a given guidance model
        self.guidance_model = guidance_model
        print(f"Initialized PromptValidationAgent with guidance model: {guidance_model}")
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validates the prompt using the guidance model.
        """
        # Define the guidance task that will be used to validate the prompt
        validation_task = self.define_guidance_task()
        print(f"Validation task defined for prompt: {prompt}")

        # Execute the guidance model for prompt validation
        try:
            # Run the validation task with the provided prompt and get the result
            print(f"Running validation task with prompt: {prompt}")
            result = validation_task(prompt=prompt)
            print(f"Guidance Validation Result: {result}")

            # Extract the user's choice from the result and determine if the prompt is valid
            choice = result["choice"]
            print(f"Guidance Validation Choice: {choice}")

            # If the model selects "yes," the prompt is valid
            is_valid = choice.lower() == "yes"
            print(f"Is the prompt valid? {is_valid}")
            return is_valid
        except Exception as e:
            # Handle any errors that occur during validation
            print(f"Validation error: {e}")
            return False

    def define_guidance_task(self):
        """
        Define the guidance task that performs prompt validation.
        """
        @guidance
        def task(prompt):
            """
            Help validate Azure cost optimization prompt. You need to determine
            whether this prompt is asking for Azure cost savings advice.
            """
            # Generate the result based on the prompt
            # The model is asked if the task involves Azure cost optimization
            print(f"Generating result for prompt: {prompt}")
            result = gen(
                f"Does this task involve Azure cost optimization? The task is: '{prompt}' Answer with yes or no."
            )
            print(f"Generated result: {result}")

            # Use `select` to help decide if the task involves cost optimization
            choice = select(["yes", "no"], name="choice")
            print(f"User's choice: {choice}")

            # Return only the choice made by the model
            return {"choice": choice}
        
        # Return the task to be used for validation
        print("Guidance task defined.")
        return task

# Step 2: Initialize the Guidance Model
def initialize_guidance_model():
    """
    Initialize the guidance model with Azure OpenAI or another model provider.
    """
    # Create and return an instance of Azure OpenAI model with the given configuration
    print("Initializing guidance model with Azure OpenAI...")
    model = models._azure_openai.AzureOpenAI(
        model="gpt-4o-mini",
        azure_endpoint="https://oai-jml.openai.azure.com",
        api_key=llm_config.get("api_key"),
        version="2024-07-18",
        echo=False
    )
    print(f"Guidance model initialized: {model}")
    return model

# Step 3: Factory function to create a validation agent
def create_validation_agent():
    """
    Creates and returns a PromptValidationAgent with a pre-configured guidance model.
    """
    # Initialize the guidance model
    print("Creating validation agent...")
    guidance_model = initialize_guidance_model()
    # Create and return the PromptValidationAgent with the initialized model
    validation_agent = PromptValidationAgent(guidance_model)
    print("Validation agent created.")
    return validation_agent