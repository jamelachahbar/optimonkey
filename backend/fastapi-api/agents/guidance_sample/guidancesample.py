import re

from guidance import assistant, gen, models, system, user
from pydantic import BaseModel

from autogen import Agent, AssistantAgent, UserProxyAgent, config_list_from_json

llm_config = config_list_from_json("OAI_CONFIG_LIST.json")[3]  # use the first config


def is_valid_code_block(code):
    pattern = r"```[\w\s]*\n([\s\S]*?)\n```"
    match = re.search(pattern, code)
    if match:
        return True
    else:
        return False

    # gpt = models._azure_openai.AzureOpenAI(

    #     azure_endpoint="https://aoai-jml.openai.azure.com",
    #     version="2024-07-18",
    #     model="gpt-4o-mini",
    #     api_key=llm_config.get("api_key"),
    #     echo=False

    # )

def generate_structured_response(recipient, messages, sender, config):
    gpt = models._openai.OpenAI(
        api_key=llm_config.get("api_key"),
        model="gpt-4o-mini",
        echo=False,
    )

    # Populate the recipient with the messages from the history
    with system():
        lm = gpt + recipient.system_message

    for message in messages:
        if message.get("role") == "user":
            with user():
                lm += message.get("content")
        else:
            with assistant():
                lm += message.get("content")

    # Generate the initial response
    with assistant():
        lm += gen(name="initial_response")

    # Check if the response contains code
    with user():
        lm += "Does the very last response from you contain code? Respond with yes or no."
    with assistant():
        lm += gen(name="contains_code")

    if "yes" in lm["contains_code"].lower():
        with user():
            lm += "Respond with a single block containing valid code. Valid code blocks start with ```"
        with assistant():
            lm += "```" + gen(name="code")
            response = "```" + lm["code"]

            is_valid = is_valid_code_block(response)
            if not is_valid:
                # Log the invalid code block and continue
                print(f"Warning: Failed to generate a valid code block\n{response}")
                response = lm["initial_response"]
    else:
        response = lm["initial_response"]

    # Log the response for debugging
    print(f"Generated Response: {response}")
    
    return True, response

guidance_agent = AssistantAgent("guidance_coder", llm_config=llm_config)
guidance_agent.register_reply(Agent, generate_structured_response, 1)
user_proxy = UserProxyAgent(
    "user",
    human_input_mode="TERMINATE",
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    is_termination_msg=lambda msg: "TERMINATE" in msg.get("content"),
)
user_proxy.initiate_chat(
    guidance_agent, 
    message="Plot and save a chart of nvidia and tsla stock price change YTD.",
    config=llm_config,
    max_turns=5
    )