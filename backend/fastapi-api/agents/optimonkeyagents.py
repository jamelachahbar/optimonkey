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

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Fetch the Bing API key from the environment variables
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

subscription_id = ("e9b4640d-1f1f-45fe-a543-c0ea45ac34c1", "38c26c07-ccce-4839-b504-cddac8e5b09d")
threshold = 3
days = 30

resources = ["Microsoft.Compute/disks", "Microsoft.Compute/virtualMachines", 
             "Microsoft.Network/publicIPAddresses", "Microsoft.Network/networkInterfaces",
             "Microsoft.CognitiveServices", "Microsoft.DataFactory", "Microsoft.Databricks"]

# Define the task prompt for the assistant
prompt = f"""
Please analyze my Azure environment and find top 5 opportunities to save money based on activity and or usage. Provide proof data and metrics to justify this list.
Give me only 5 recommendations to work with.
Look for disks and storage accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
Provide advice on what to do with this information and output it along with the results in the CSV file.
Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
"""

# Initialize the Planner assistant
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""You are a helpful AI Assistant. You are the planner of this team of assistants. 
    You plan the tasks and make sure everything is on track. Suggest a plan. Revise the plan if needed. When the plan is solid and
    ready to be executed, pass it to the Coder.""",
    llm_config=llm_config,
    human_input_mode="TERMINATE"
)

def ask_planner(message):
    """
    Logs the message received from the planner agent.

    Args:
        message (str): Message to be logged.

    Returns:
        str: Response message from the planner.
    """
    logging.info(f"Planner received the following message: {message}")
    return f"Planner response to: {message}"

# Initialize the UserProxyAgent responsible for code execution
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

# Initialize the Code_Guru assistant for coding tasks
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

# Initialize the Critic assistant for code evaluation
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. You are a helpful AI assistant. You are highly skilled in evaluating the quality of a given code by providing a score from 1 (bad) - 10 (good) while providing clear rationale.""",
    llm_config=llm_config,
    human_input_mode="TERMINATE"
)

# Define the Kusto Query Function
def run_kusto_query(query: Annotated[str, "The KQL query"], subscriptions: Annotated[List[str], "List of subscription IDs"]) -> List[Dict]:
    """
    Run a Kusto query using Azure Resource Graph to get resource details from specified subscriptions.

    Args:
        query (str): The KQL query to execute.
        subscriptions (List[str]): List of subscription IDs.

    Returns:
        List[Dict]: Results from the query.
    """
    credential = DefaultAzureCredential()
    resourcegraph_client = ResourceGraphClient(credential)
    query_request = QueryRequest(query=query, subscriptions=subscriptions)
    query_response = resourcegraph_client.resources(query_request)
    return query_response.data

# Register Kusto Query Function with the system
register_function(
    run_kusto_query,
    caller=coder,
    executor=user_proxy,
    name="run_kusto_query",
    description="This function generates the code to run a Kusto Query Language (KQL) query using Azure Resource Graph."
)

# Define a function to extract resource IDs from the Kusto query results
def extract_resource_ids(kusto_results: List[Dict]) -> List[str]:
    """
    Extracts the resourceId field from Kusto query results.

    Args:
        kusto_results (List[Dict]): The results of a Kusto query.

    Returns:
        List[str]: List of resource IDs extracted from the query results.
    """
    print(f"Extracting resource IDs from: {kusto_results}")  # Debugging output
    resource_ids = []
    for result in kusto_results:
        resource_id = result.get("resourceId")  # Assuming "resourceId" is the field in the Kusto result
        if resource_id:
            resource_ids.append(resource_id)
    return resource_ids

# Register the resource ID extraction function
register_function(
    extract_resource_ids,
    caller=coder,
    executor=user_proxy,
    name="extract_resource_ids",
    description="This function extracts the resourceId field from Kusto query results."
)

# Define the function to query usage metrics for a given Azure resource
def query_usage_metrics(
    resource_id: Annotated[str, "The Azure resource ID"],
    metric_names: Annotated[List[str], "List of metric names to query"] = ['Percentage CPU', 'Network In', 'Network Out', 'Disk Read Bytes', 'Disk Write Bytes', 'Disk Read Operations', 'Disk Write Operations'],
    aggregation: str = 'Total',
    timespan: str = 'P30D',
    interval: str = 'P1D'
) -> Dict[str, float]:
    """
    Query usage metrics for a given Azure resource.

    Args:
        resource_id (str): The Azure resource ID.
        metric_names (List[str]): List of metric names to query.
        aggregation (str): The type of aggregation to use (e.g., 'Total').
        timespan (str): The timespan to query over (e.g., 'P30D' for 30 days).
        interval (str): The granularity of the data (e.g., 'P1D' for daily).

    Returns:
        Dict[str, float]: Total usage for each queried metric.
    """
    # Initialize the MonitorManagementClient
    monitor_client = MonitorManagementClient(
        credential=DefaultAzureCredential(), 
        subscription_id='<Your-Subscription-ID>'  # Replace with your actual subscription ID
    )

    # Use `resource_id` as the `resource_uri` in the metrics.list call
    metrics_data = monitor_client.metrics.list(
        resource_uri=resource_id,
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

# Register the query usage metrics function
register_function(
    query_usage_metrics,
    caller=coder,
    executor=user_proxy,
    name="query_usage_metrics",
    description="This function allows the agent to Query Azure Monitor metrics for the specified resource and metrics."
)

# Define a function to tie together running a Kusto query and querying usage metrics
def analyze_resources_and_query_metrics(kusto_query: str, subscriptions: List[str]):
    """
    This function runs a Kusto query, extracts resource IDs, and queries usage metrics for each resource.

    Args:
        kusto_query (str): The KQL query to execute.
        subscriptions (List[str]): List of Azure subscription IDs.
    """
    # Step 1: Run the Kusto query to get resource details
    kusto_results = run_kusto_query(kusto_query, subscriptions)

    # Step 2: Extract resource IDs from the Kusto query results
    if kusto_results:
        resource_ids = extract_resource_ids(kusto_results)
    
        # Step 3: Query usage metrics for each resource ID
        for resource_id in resource_ids:
            metrics = query_usage_metrics(resource_id)
            print(f"Metrics for {resource_id}: {metrics}")
    else:
        print("No resources found in the Kusto query results.")

# Register the higher-level function
register_function(
    analyze_resources_and_query_metrics,
    caller=coder,
    executor=user_proxy,
    name="analyze_resources_and_query_metrics",
    description="This function analyzes Azure resources, extracts resource IDs, and queries usage metrics for each resource."
)

# Define the function to save the results to a CSV file
def save_results_to_csv(results: List[Dict], filename: str = "azure_analysis_results.csv") -> str:
    """
    Saves the analysis results to a CSV file.

    Args:
        results (List[Dict]): The data to save to the CSV.
        filename (str): The name of the CSV file.

    Returns:
        str: A message indicating the results were saved successfully.
    """
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

# Register the save to CSV function
register_function(
    save_results_to_csv,
    caller=coder,
    executor=user_proxy,
    name="save_results_to_csv",
    description="A tool to save results to CSV."
)

# Initialize GroupChat with the agents
groupchat = autogen.GroupChat(
    agents=[planner, coder, critic, user_proxy], 
    messages=[],  
    max_round=50,
    speaker_selection_method="round_robin"
)

# Start the conversation among the agents
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Define the function to start the agent conversation
def start_agent_conversation():
    """
    Starts the agent conversation and logs messages in a conversation list.
    """
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
