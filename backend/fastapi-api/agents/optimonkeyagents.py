import json
from typing import Literal, Optional, List, Dict
import logging
import autogen
from fastapi import WebSocket
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
from azure.mgmt.monitor import MonitorManagementClient
# Load environment variables
from dotenv import load_dotenv
import websocket

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
    "timeout": 60
}

subscription_id = ("38c26c07-ccce-4839-b504-cddac8e5b09d")
threshold = 3
days = 30

resources = ["Microsoft.Compute/disks", "Microsoft.Compute/virtualMachines", 
             "Microsoft.Network/publicIPAddresses", "Microsoft.Network/networkInterfaces",
             "Microsoft.CognitiveServices", "Microsoft.DataFactory", "Microsoft.Databricks"]

# Define the task prompt for the assistant
# prompt = f"""
# Please analyze my Azure environment and find top 5 opportunities to save money based on activity and or usage. Provide proof data and metrics to justify this list.
# Give me only 5 recommendations to work with.
# Look for disks and storage accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
# Provide advice on what to do with this information and output it along with the results in the CSV file.
# Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
# """


# prompt = f"""
# Please analyze my Azure environment and find top 5 opportunities to save money based on activity and/or usage. Provide proof data and metrics to justify this list.
# Give me only 5 recommendations to work with.
# Look for Virtual Machines on these subscriptions or one of these {subscription_id} and save it to a CSV file.
# Provide advise on what to do with this information and output it along with the results in the CSV file.
# Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
# """



prompt = f"""
Please analyze my Azure environment and find top 5 opportunities to save money based on activity and/or usage. Provide proof data and metrics to justify this list.
Give me only 5 recommendations to work with.
Look for Storage Accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
Provide advise on what to do with this information and output it along with the results in the CSV file.
Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
"""
# Initialize the Planner assistant
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""You are a helpful AI Assistant. You are the planner of this team of assistants. 
    You plan the tasks and make sure everything is on track. Suggest a plan. Revise the plan if needed. When the plan is solid and
    ready to be executed, pass it to the Coder. Also make sure the plan includes the functions the Coder can call and the order in which they should be called.""",
    description="I am the planner of the team. I plan the tasks and make sure everything is on track. If needed, we should reassess the initial collection of metrics to confirm accuracy and completeness. Let’s make sure each function is executed as planned. ",
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
    system_message="You are a helpful AI assistant. You are the user proxy. You execute code.",
    # description="""User Proxy is a user who can execute the code and interact with the system. 
    # I also check if the plan was applied and the output we have is according to the instructions. 
    # If not, I will ask the planner to revise the plan. Make sure all the functions are called in the right order and the code is well structured and easy to understand. Also make sure there is an output and 
    # the output is according to the instructions. Make sure there sis a CSV file with the results.""",
    max_consecutive_auto_reply=3,
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
    Always use functions you have access to and start with run_kusto_query, 
    then the next function which is extract_resource_ids, and then in the END use the analyze_resources_and_query_metrics function, followed by the save_results_to_csv function.
    TERMINATE the conversation when the task is complete.""", 
    description="I'm a highly experienced programmer specialized in Python, bash. I am **ONLY** allowed to speak **immediately** after `Planner` and before `UserProxy`.",
    llm_config={
        "config_list": config_list,
        "temperature": 0
    },
    human_input_mode="NEVER"
)

# Initialize the Critic assistant for code evaluation
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
Do not come up with a plan or suggest a code. You can only critique the code.
Make sure the Coder uses the functions in the right order and the code is well structured and easy to understand.""",
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
    # pass this as a parameter to the next function

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
    # resource_ids = extract_resource_ids(kusto_results)
    return resource_ids



# Register the resource ID extraction function
register_function(
    extract_resource_ids,
    caller=coder,
    executor=user_proxy,
    name="extract_resource_ids",
    description="This function extracts the resourceId field from Kusto query results."
)

# Define function to query usage metrics based on resource type
def query_usage_metrics(
    resource_id: str,
    resource_type: str,  # The Azure resource type
    metric_names: Optional[List[str]] = None,  # Use optional metric_names based on resource type
    aggregation: str = 'Average',  # Default to Average for percentage metrics
    timespan: str = 'P30D',
    interval: Optional[str] = None  # Dynamically set based on resource type
) -> Dict[str, float]:
    """
    Query usage metrics for a given Azure resource, adjusting time grain based on the resource type.

    Args:
        resource_id (str): The Azure resource ID.
        resource_type (str): The type of the Azure resource (e.g., 'Microsoft.Compute/virtualMachines').
        metric_names (List[str], optional): List of metric names to query. Defaults will be used based on resource type.
        aggregation (str): The type of aggregation to use (e.g., 'Average' for percentage metrics).
        timespan (str): The timespan to query over (e.g., 'P30D' for 30 days).
        interval (str, optional): The granularity of the data (e.g., 'P1D' for daily or 'P1H' for hourly).

    Returns:
        Dict[str, float]: Total usage for each queried metric.
    """

    # Normalize the resource_type to lowercase for case-insensitive comparison
    resource_type_normalized = resource_type.lower()

    # Define default metrics based on the resource type
    if resource_type_normalized == "microsoft.compute/virtualmachines":
        metric_names = metric_names or ['Percentage CPU', 'Network In', 'Network Out', 'Disk Read Bytes', 'Disk Write Bytes']
        interval = interval or 'P1D'  # Use daily intervals for VMs
    elif resource_type_normalized == "microsoft.storage/storageaccounts":
        metric_names = metric_names or ['UsedCapacity', 'Transactions', 'Ingress', 'Egress', 'Availability']
        interval = 'PT1H'  # Use hourly intervals for storage accounts
    elif resource_type_normalized == "microsoft.compute/disks":
        metric_names = metric_names or ['Composite Disk Read Bytes/sec', 'Composite Disk Write Bytes/sec']
        interval = interval or 'P1D'  # Use daily intervals for disks
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")

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

    # Calculate average usage for each metric
    for metric in metrics_data.value:
        metric_name = metric.name.value
        average = sum(
            [
                data.average  # Use the average aggregation for percentage metrics like CPU
                for timeseries in metric.timeseries
                for data in timeseries.data
                if data.average is not None
            ]
        ) / len(metric.timeseries) if metric.timeseries else 0
        total_usage[metric_name] = average

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
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Define a Pydantic model to encapsulate the resource metrics results
class ResourceMetricsResult(BaseModel):
    resource_id: str = Field(..., description="The Azure resource ID.")
    metrics: Dict[str, float] = Field(..., description="The metrics data for the resource.")

class AnalyzeResourcesResponse(BaseModel):
    resources_analyzed: int = Field(..., description="The number of resources analyzed.")
    results: List[ResourceMetricsResult] = Field(..., description="A list of resources and their associated metrics.")
    message: Optional[str] = Field(None, description="Optional message regarding the analysis.")

# Modify the analyze_resources_and_query_metrics function to return a BaseModel
def analyze_resources_and_query_metrics(kusto_query: str, subscriptions: List[str]) -> AnalyzeResourcesResponse:
    """
    This function runs a Kusto query, extracts resource IDs, and queries usage metrics for each resource.

    Args:
        kusto_query (str): The KQL query to execute.
        subscriptions (List[str]): List of Azure subscription IDs.

    Returns:
        AnalyzeResourcesResponse: A pydantic BaseModel containing the results of the analysis and the metrics for each resource.
    """
    # Step 1: Run the Kusto query to get resource details
    kusto_results = run_kusto_query(kusto_query, subscriptions)

    if not kusto_results:
        return AnalyzeResourcesResponse(
            resources_analyzed=0,
            results=[],
            message="No resources found in the Kusto query results."
        )
    else:
        print(f"Kusto results: {kusto_results}")

    # Step 2: Extract resource IDs from the Kusto query results
    resource_ids = extract_resource_ids(kusto_results)

    # Step 3: Query usage metrics for each resource ID
    resource_metrics_results = []
    for resource_id in resource_ids:
        metrics = query_usage_metrics(resource_id)
        resource_metrics_results.append(
            ResourceMetricsResult(
                resource_id=resource_id,
                metrics=metrics
            )
        )

    # Return a structured response encapsulating the resource metrics results
    return AnalyzeResourcesResponse(
        resources_analyzed=len(resource_ids),
        results=resource_metrics_results,
        message="Analysis completed successfully."
    )

# Register the higher-level function with return type annotation
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
    max_round=100,
    speaker_selection_method="round_robin"
)

# Start the conversation among the agents
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

import json
from datetime import datetime
from fastapi import WebSocket
import logging

async def start_agent_conversation(user_message: str, websocket: WebSocket):
    """
    Initiates a dynamic agent conversation and streams responses through WebSocket.
    """

    # Clear the previous messages in the chat
    manager.groupchat.messages.clear()

    # Start the conversation by passing the initial user message to the user_proxy agent
    user_proxy.initiate_chat(manager, message=user_message, max_round=50)

    # Collect the messages from the conversation
    conversation = []

    try:
        for message in manager.groupchat.messages:
            # Dynamically construct the message content and agent's status
            msg_content = {
                "content": message.get("content", ""),
                "role": message.get("role", ""),
                "name": message.get("name", ""),
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
            conversation.append(msg_content)

            # Construct dynamic agent status update
            agent_status = {
                "agent": message.get("name"),
                "status": "active" if "error" not in message.get("content", "").lower() else "error",
                "task": message.get("content"),
                "time": message.get("timestamp")
            }

            # Send the response back via WebSocket
            await websocket.send_text(json.dumps(agent_status))

    except Exception as e:
        logging.error(f"Error during conversation: {str(e)}")
        await websocket.send_text(json.dumps({
            "error": "An error occurred during the conversation. Please try again.",
            "details": str(e)
        }))

    # Yield each message for further asynchronous processing or logging
    for msg in conversation:
        yield msg
