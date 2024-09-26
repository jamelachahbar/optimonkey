from typing import Literal
import logging
import autogen
from typing_extensions import Annotated
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
from autogen import register_function
import csv
import os
from azure.monitor.query import MetricsQueryClient

# Load environment variables
from dotenv import load_dotenv
# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

bing_api_key = os.getenv("BING_API_KEY")

if not bing_api_key:
    raise ValueError("Error: Missing Bing API key.")
else:
    print(f"Bing API Key Loaded Successfully: {bing_api_key}")

# Define the configuration for the LLM model
config_list = autogen.config_list_from_json("./agents/OAI_CONFIG_LIST.json")
llm_config = {
    "config_list": config_list, 
    "cache_seed": 42,
    "timeout": 30
}

subscription_id = "e9b4640d-1f1f-45fe-a543-c0ea45ac34c1", "38c26c07-ccce-4839-b504-cddac8e5b09d"
threshold = 3
days = 30

bing_api_key = os.getenv("BING_API_KEY")

resources = ["Microsoft.Compute/disks", "Microsoft.Compute/virtualMachines", 
             "Microsoft.Network/publicIPAddresses", "Microsoft.Network/networkInterfaces",
             "Microsoft.CognitiveServices", "Microsoft.DataFactory", "Microsoft.Databricks"]

# prompt = f"""
# Please analyze my Azure environment and find top 10 opportunities to save money. Give me only 10 recommendations to work with. 
# Look for these types of resources {resources} on these subscriptions or one of these {subscription_id} and save it to a CSV file. 
# Provide advice on what to do with this information and output it along with the results in the CSV file. 
# Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
# """


prompt = f"""
Please analyze my Azure environment and find top 5 opportunities to save money based on activity and or usage. Provide proof data and metrics to justify this list.
Give me only 5 recommendations to work with.
Look for disks and storage accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
Provide advice on what to do with this information and output it along with the results in the CSV file.
Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
"""
# from autogen.agentchat.contrib.web_surfer import WebSurferAgent
# from autogen.browser_utils import SimpleTextBrowser

# summarizer_llm_config = {
#     "timeout": 600,
#     "cache_seed": 42,
#     "config_list": config_list,
#     "temperature": 0
# }

# # Initialize WebSurferAgent
# web_surfer = WebSurferAgent(
#     name="web_surfer",
#     system_message="""You are a helpful AI Assistant. You are the web surfer of this team of assistants. 
#     You can search the web for information and summarize it for the team, especially when an execution fails or a task cannot be completed. 
#     You assist the Planner.""",
#     description="I am a web surfer who can search the web for information and summarize it for the team.",
#     llm_config=llm_config, 
#     summarizer_llm_config=summarizer_llm_config
# )

# Initialize the Planner
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""You are a helpful AI Assistant. You are the planner of this team of assistants. 
    You plan the tasks and make sure everything is on track. Suggest a plan. Revise the plan if needed. When the plan is solid and
    ready to be executed, pass it to the Coder.""",
    llm_config=llm_config,
    human_input_mode="TERMINATE"
)

def ask_planner(message):
    logging.info(f"Planner received the following message: {message}")
    return f"Planner response to: {message}"

# Create UserProxyAgent
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    system_message="You are a helpful AI Assistant. You are the user proxy. You can execute the code and interact with the system.",
    description="""User Proxy is a user who can execute the code and interact with the system. 
    I also check if the plan was applied and the output we have is according to the instructions. 
    If not, I will ask the planner to revise the plan.""",
    max_consecutive_auto_reply=10,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": "python:3.10"
    }
)

# Create an AssistantAgent for coding with external KQL handling
coder = autogen.AssistantAgent(
    name="Code_Guru",
    system_message="""You are a helpful AI Assistant. You are a highly experienced programmer specialized in Azure. 
    Follow the approved plan and save the code to disk. Always use functions you have access to and start with run_kusto_query, 
    then the next function which is extract_resource_ids, and so on.
    The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. 
    If the result indicates there is an error, fix the error and output the code again.
    TERMINATE the conversation when the task is complete.""", 
    description="I'm a highly experienced programmer specialized in Python, bash. I am **ONLY** allowed to speak **immediately** after `Planner` and before `UserProxy`.",
    llm_config={
        "cache_seed": 0,
        "config_list": config_list,
        "temperature": 0
    },
    human_input_mode="TERMINATE"
)

critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. You are a helpful AI assistant. You are highly skilled in evaluating the quality of a given code by providing a score from 1 (bad) - 10 (good) while providing clear rationale. YOU MUST CONSIDER VISUALIZATION BEST PRACTICES for each evaluation. Specifically, you can carefully evaluate the code across the following dimensions:
- bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
- Data transformation (transformation): Is the data transformed appropriately for the type? E.g., is the dataset appropriated filtered, aggregated, or grouped if needed? If a date field is used, is the date field first converted to a date object etc?
- Goal compliance (compliance): how well the code meets the specified goals?
- Visualization type (type): CONSIDERING BEST PRACTICES, is the type appropriate for the data and intent? Is there a type that would be more effective in conveying insights? If a different type is more appropriate, the score MUST BE LESS THAN 5.
- Data encoding (encoding): Is the data encoded appropriately for the type?
- Aesthetics (aesthetics): Are the aesthetics of the appropriate for the type and the data?
YOU MUST PROVIDE A SCORE for each of the above dimensions.
{bugs: 0, transformation: 0, compliance: 0, type: 0, encoding: 0, aesthetics: 0}
Do not suggest code.
Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
Do not come up with a plan or suggest a code. You can only critique the code.""",
    llm_config=llm_config,
    human_input_mode="TERMINATE"
)

# Define Kusto Query Function
def run_kusto_query(query: Annotated[str, "The KQL query"], subscriptions: Annotated[List[str], "List of subscription IDs"]) -> List[Dict]:
    credential = DefaultAzureCredential()
    resourcegraph_client = ResourceGraphClient(credential)
    query_request = QueryRequest(query=query, subscriptions=subscriptions)
    query_response = resourcegraph_client.resources(query_request)
    return query_response.data

# Register Kusto Query Function
register_function(
    run_kusto_query,
    caller=coder,
    executor=user_proxy,
    name="run_kusto_query",
    description="This function generates the code to run a Kusto Query Language (KQL) query using Azure Resource Graph."
)

# 2. Function to extract resourceId from Kusto query results
def extract_resource_ids(kusto_results: List[Dict]) -> List[str]:
    """
    Extracts the resourceId field from Kusto query results. This comes after running the Kusto query to get resource details.
    """
    print(f"Extracting resource IDs from: {kusto_results}")  # Add a print to debug
    resource_ids = []
    for result in kusto_results:
        resource_id = result.get("resourceId")  # Assuming "resourceId" is the field in the Kusto result
        if resource_id:
            resource_ids.append(resource_id)
    return resource_ids

# Define a function that does not include custom types in the function signature
from azure.identity import DefaultAzureCredential
from azure.mgmt.monitor import MonitorManagementClient

def query_usage_metrics(
    resource_id: Annotated[str, "The Azure resource ID"],
    metric_names: Annotated[List[str], "List of metric names to query"] = ['Percentage CPU', 'Network In', 'Network Out', 'Disk Read Bytes', 'Disk Write Bytes', 'Disk Read Operations', 'Disk Write Operations'],
    aggregation: str = 'Total',
    timespan: str = 'P30D',
    interval: str = 'P1D'
) -> Dict[str, float]:
    """
    Query usage metrics for a given Azure resource. The MonitorManagementClient is initialized within the function 
    to avoid passing it through Pydantic validation. This function does not include custom types in the function signature.
    This comes after extracting the resourceId field from Kusto query results.
    """
    # Initialize the MonitorManagementClient inside the function
    monitor_client = MonitorManagementClient(
        credential=DefaultAzureCredential(), 
        subscription_id='<Your-Subscription-ID>'  # Replace with your actual subscription ID
    )

    # Use `resource_id` as the `resource_uri` in the metrics.list call
    metrics_data = monitor_client.metrics.list(
        resource_uri=resource_id,  # `resource_id` corresponds to `resource_uri`
        timespan=timespan,
        interval=interval,
        metricnames=','.join(metric_names),
        aggregation=aggregation
    )
    
    total_usage = {}
    
    # Calculate total usage for each metric
    for metric in metrics_data.value:
        metric_name = metric.name.value
        total = sum([data.total for timeseries in metric.timeseries for data in timeseries.data if data.total is not None])
        total_usage[metric_name] = total
    
    return total_usage

# Now, register the function without the custom type in the signature
register_function(
    query_usage_metrics,
    caller=coder,
    executor=user_proxy,
    name="query_usage_metrics",
    description="This function allows the agent to Query Azure Monitor metrics for the specified resource and metrics."
)

register_function(
    extract_resource_ids,
    caller=coder,
    executor=user_proxy,
    name="extract_resource_ids",
    description="This function extracts the resourceId field from Kusto query results."
)

# 4. Combine everything into a higher-level function that ties the steps together
def analyze_resources_and_query_metrics(kusto_query: str, subscriptions: List[str]):
    """
    This function analyzes Azure resources, extracts resource IDs, and queries usage metrics for each resource.
    This ties together the steps of running a Kusto query, extracting resource IDs, and querying usage metrics.
    """

    # Step 1: Run the Kusto query to get resource details
    kusto_results = run_kusto_query(kusto_query, subscriptions)  # Ensure kusto_results are returned here

    # Step 2: Extract resource IDs from the Kusto query results
    if kusto_results:  # Ensure kusto_results are not empty before proceeding
        resource_ids = extract_resource_ids(kusto_results)  # Pass the Kusto results here
    
        # Step 3: Query usage metrics for each resource ID
        for resource_id in resource_ids:
            metrics = query_usage_metrics(resource_id)
            print(f"Metrics for {resource_id}: {metrics}")
    else:
        print("No resources found in the Kusto query results.")

register_function(
    analyze_resources_and_query_metrics,
    caller=coder,
    executor=user_proxy,
    name="analyze_resources_and_query_metrics",
    description="This function analyzes Azure resources, extracts resource IDs, and queries usage metrics for each resource."
)



# Define the function to save results to CSV
def save_results_to_csv(results: List[Dict], filename: str = "azure_analysis_results.csv") -> str:
    if not results:
        return "No results to save."

    # Extract keys from the first result to use as column headers
    keys = results[0].keys() if results else []
    
    # Save results to a CSV file
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)
    
    return f"Results successfully saved to {filename}"

# Register Save to CSV Function
register_function(
    save_results_to_csv,
    caller=coder,
    executor=user_proxy,
    name="save_results_to_csv",
    description="A tool to save results to CSV.",
)
# Initialize GroupChat
groupchat = autogen.GroupChat(
    agents=[planner, coder, critic, user_proxy], 
    messages=[],  
    max_round=50,
    speaker_selection_method="round_robin"
    # select_speaker_prompt_template="Please select the next speaker from the list: {speaker_list}",
)

# Initiate chat between the user_proxy and assistant
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Start the conversation
def start_agent_conversation():
    user_proxy.initiate_chat(
        manager,
        message=prompt,
        summary_method="reflection_with_llm"
    )
    conversation = []
    for message in manager.groupchat.messages:
        msg_content = {
            "content": message.get("content", ""),
            "role": message.get("role", ""),
            "name": message.get("name", ""),
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        conversation.append(msg_content)
    return conversation
