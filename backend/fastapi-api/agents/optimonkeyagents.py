
from typing import Optional, List, Dict
import logging
import autogen
from typing_extensions import Annotated
from azure.identity import DefaultAzureCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest
from typing import List, Dict
from datetime import datetime
from autogen import register_function
import csv
import os
from azure.mgmt.monitor import MonitorManagementClient
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Fetch the Bing API key from the environment variables, only if we use web search
# bing_api_key = os.getenv("BING_API_KEY")

# if not bing_api_key:
#     raise ValueError("Error: Missing Bing API key.")
# else:
#     print(f"Bing API Key Loaded Successfully: {bing_api_key}")

# Define the configuration for the LLM model
config_list = autogen.config_list_from_json("./agents/OAI_CONFIG_LIST.json")
llm_config = {
    "config_list": config_list, 
    "cache_seed": 0,
    "timeout": 180
    
}

subscription_id = ("38c26c07-ccce-4839-b504-cddac8e5b09d")
threshold = 3
days = 30
workspace_id = "fdd39622-ae5a-4eb8-987b-14ae8aad63dd"
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

# Initialize the Admin
user_proxy = autogen.UserProxyAgent(
    name="admin",
    human_input_mode='NEVER',
    system_message='Give the task and send instruction to the critic to evaluate and refine the code.',
    code_execution_config=False,
    # llm_config=llm_config
)

# Initialize the Planner assistant
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""
    Given a task, please determine what information is needed to complete the task, how to obtain that information, and what steps are required to complete the task.
    Please note that the information will all be retrieved using Python and Azure SDKs.
    Please only suggest information that is relevant to the task and ensure that the information is accurate and up-to-date.
    Make sure the information can be retrieved using the functions provided and Python code.
    After each step is completed by others, check the progress and make sure the next step is executed correctly.
    If a step fails, try to identify the issue and suggest a solution or a workaround.
    """,
    description=""" 
    Given a task, please determine what information is needed to complete the task, how to obtain that information, 
    and what steps are required to complete the task. After each step is completed by others, 
    check the progress and make sure the next step is executed correctly.
    """,
    llm_config=llm_config
    )


# Initialize the Code_Guru assistant for coding tasks
coder = autogen.AssistantAgent(
    name="Code_Guru",
    system_message="""You are a helpful AI Assistant. You are a highly experienced programmer specialized in Azure. 
    Follow the approved plan and save the code to disk. Always use functions you have access to and start with run_kusto_query
    When using code, you must indicate the script type in the code block. 
    The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. 
    The user can't change your code. 
    So do not suggest incomplete code which requires users to modify. 
    Don't use a code block if it's not intended to be executed by the user.
    If the result indicates there is an error, fix the error and output the code again. Suggest the 
    full code instead of partial code or code changes. If the error can't be fixed or if the task is 
    not solved even after the code is executed successfully, analyze the problem, revisit your 
    assumption, collect additional info you need, and think of a different approach to try.
    When you find an answer, verify the answer carefully. Include verifiable evidence in your response 
    if possible.
    Reply "TERMINATE" in the end when everything is done""", 
    description="I'm a highly experienced programmer specialized in Python, bash. I am **ONLY** allowed to speak **immediately** after `Planner`.",
    llm_config={
        "cache_seed": 0,  # Seed for caching and reproducibility was 42
        "config_list": config_list,  # List of OpenAI API configurations
        "temperature": 0  # Temperature for sampling
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
    llm_config=llm_config
    )

code_executor = autogen.UserProxyAgent(
    name="Executor",
    description="Execute the code provided by the coder and provide the results.",
    human_input_mode="NEVER",
    code_execution_config={
        "last_n_messages": 5,
        "work_dir": "coding",
        "use_docker": "python:3.10",
    },
    llm_config=llm_config
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
    executor=code_executor,
    name="run_kusto_query",
    description="This function generates the code to run a Kusto Query Language (KQL) query using Azure Resource Graph."
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
        Dict[str, Any]: Total usage for each queried metric.
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
        metric_names = metric_names or ['Composite Disk Readdre Bytes/sec', 'Composite Disk Write Bytes/sec','Composite Disk Read Operations/sec','Composite Disk Write Operations/sec']
        interval = interval or 'P1D'  # Use daily intervals for disks
    else:
        raise ValueError(f"Unsupported resource type: {resource_type}")

    # Initialize the MonitorManagementClient
    monitor_client = MonitorManagementClient(
        credential=DefaultAzureCredential(),
        subscription_id=subscription_id  # Replace with your actual subscription ID
    )

    # Use `resource_id` as the `resource_uri` in the metrics.list call
    metrics_data = monitor_client.metrics.list(
        resource_uri=resource_id,
        timespan=timespan,
        interval=interval,
        metricnames=','.join(metric_names),
        aggregation=aggregation
    )
    resource_usage = {"resource_id": resource_id}

    # Calculate average usage for each metric and append to resource usage
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

        resource_usage[metric_name] = average
    return resource_usage
# Register the query usage metrics function
register_function(
    query_usage_metrics,
    caller=coder,
    executor=code_executor,
    name="query_usage_metrics",
    description="This function allows the agent to Query Azure Monitor metrics for the specified resource and metrics."
)

# import requests

# # Fetch Azure Retail Prices for Virtual Machines
# # use annotation to specify the return type
# def fetch_vm_pricing(location: str) -> List[Dict]:
#     """
#     Fetch Azure retail prices for Virtual Machines filtered by location.

#     Args:
#         location (str): The location to filter pricing data.

#     Returns:
#         List[Dict]: A list of pricing details for Virtual Machines filtered by the specified location.
#     """
#     # Update the API URL to include location filter
#     url = f"https://prices.azure.com/api/retail/prices?$filter=serviceName eq 'Virtual Machines' and location eq '{location}'"
    
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         return response.json().get('Items', [
#             {"productName": "No data available", "meterName": "No data available", "unitPrice": "No data available", "currencyCode": "No data available", "location": location}
#         ])
#     else:
#         return []

# # Register the function to fetch VM pricing
# register_function(
#     fetch_vm_pricing,
#     caller=coder,
#     executor=user_proxy,
#     name="fetch_vm_pricing",
#     description="This function fetches Azure retail prices for Virtual Machines."
# )
# # Function to fetch actual VM usage data from Azure Monitor
# def fetch_vm_usage_data() -> List[Dict]:
#     """
#     Fetch actual VM usage data from Azure Monitor.

#     Returns:
#         List[Dict]: A list of VM usage data.
#     """
#     # Replace with actual Azure Monitor API endpoint and logic
#     url = "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines?api-version=2021-07-01"
#     headers = {
#         "Authorization": "Bearer {access_token}",  # Replace with your token
#         "Content-Type": "application/json"
#     }

#     response = requests.get(url, headers=headers)
    
#     if response.status_code == 200:
#         # Extract relevant VM data
#         vm_data = response.json().get('value', [])
#         return [
#             {"name": vm['name'], "usage": get_vm_usage(vm['id']), "region": vm['location']}
#             for vm in vm_data
#         ]
#     else:
#         return []

# register_function(
#     fetch_vm_usage_data,
#     caller=coder,
#     executor=user_proxy,
#     name="fetch_vm_usage_data",
#     description="This function fetches actual VM usage data from Azure Monitor."
# )

# def get_vm_usage(vm_id: str) -> int:
#     """
#     Fetch usage data for a specific VM.

#     Args:
#         vm_id (str): The ID of the VM.

#     Returns:
#         int: Usage value.
#     """
#     # Call your existing metrics query function
#     usage_data = query_usage_metrics(vm_id)
    
#     # Assuming query_metrics returns a dictionary with a key 'usage'
#     return usage_data.get('usage', 0)  # Return 0 if 'usage' key is not found

# # Register the function to get VM usage data
# register_function(
#     get_vm_usage,
#     caller=coder,
#     executor=user_proxy,
#     name="get_vm_usage",
#     description="This function fetches usage data for a specific VM."
# )
# # Analyze and Compare VM usage data and use annotation to specify the return type
# # Function to analyze and compare VM usage data with pricing data
# def analyze_and_compare(vm_usage_data: List[Dict], pricing_data: List[Dict]) -> List[Dict]:
#     """
#     Analyze and compare VM usage data with pricing data to generate recommendations.

#     Args:
#         vm_usage_data (List[Dict]): VM usage data from Azure Monitor.
#         pricing_data (List[Dict]): Pricing data for Virtual Machines.

#     Returns:
#         List[Dict]: A list of recommendations based on the analysis.
#     """
#     recommendations = []
    
#     for vm in vm_usage_data:
#         vm_name = vm['name']
#         region = vm['region']  # Assuming the region is part of the VM usage data
#         # Find the corresponding pricing for the specific VM in that region
#         pricing_for_vm = [p for p in pricing_data if p['location'] == region]
        
#         # Implement your logic to create recommendations based on pricing data
#         recommendation = f"Pricing details for {vm_name} in {region}: {pricing_for_vm}"  # Customize this as needed
        
#         recommendations.append({'vm_name': vm_name, 'recommendation': recommendation})

#     return recommendations


# # Register the function to analyze and compare VM usage data
# register_function(
#     analyze_and_compare,
#     caller=coder,
#     executor=user_proxy,
#     name="analyze_and_compare",
#     description="This function analyzes and compares VM usage data with pricing data to generate recommendations."
# )

# from azure.identity import DefaultAzureCredential
# from azure.monitor.query import LogsQueryClient
# from typing import Optional, List, Dict
# from datetime import timedelta
# import logging

# # Initialize Logs Query Client with default Azure credentials
# credential = DefaultAzureCredential()
# logs_client = LogsQueryClient(credential)

# # Function to dynamically retrieve log tables and allow the agent to figure out the query
# def get_log_tables(workspace_id: str) -> List[str]:
#     """
#     Retrieves log tables from Log Analytics workspace.

#     Args:
#         workspace_id (str): The Log Analytics Workspace ID.

#     Returns:
#         List[str]: A list of available log table names.
#     """
#     kusto_query_tables = """
#     union *
#     | summarize by Type
#     | where Type contains 'Logs'
#     | summarize by Type
#     """

#     try:
#         # Execute the query to get log tables
#         response_tables = logs_client.query_workspace(
#             workspace_id=workspace_id,
#             query=kusto_query_tables,
#             timespan=(None, timedelta(days=30))  # Query logs for the last 30 days
#         )

#         if response_tables.status == 'Success':
#             available_tables = [row[0] for row in response_tables.tables[0].rows]
#             logging.info(f"Available tables for workspace {workspace_id}: {available_tables}")
#             return available_tables  # Return only the names of the tables

#         else:
#             logging.error(f"Failed to retrieve log tables: {response_tables.error}")
#             return []

#     except Exception as e:
#         logging.error(f"Error retrieving log tables: {e}")
#         return []

# # Register the function that returns the available log tables for the agent to work with
# register_function(
#     get_log_tables,  
#     caller=coder,
#     executor=user_proxy,
#     name="get_log_tables",
#     description="This function retrieves available log tables from Log Analytics and allows the agent to decide on the query."
# )
# def query_logs(workspace_id: str, table_name: str, query: str) -> List[Dict]:
#     """
#     Queries logs from a specific log table in Log Analytics.

#     Args:
#         workspace_id (str): The Log Analytics Workspace ID.
#         table_name (str): The specific log table to query.
#         query (str): The KQL query to execute.

#     Returns:
#         List[Dict]: A list of results from the log query.
#     """
#     try:
#         response_logs = logs_client.query_workspace(
#             workspace_id=workspace_id,
#             query=query,
#             timespan=(None, timedelta(days=30))  # Query logs for the last 30 days
#         )

#         if response_logs.status == 'Success':
#             logging.info(f"Successfully queried logs from table {table_name}")
#             return response_logs.tables[0].rows  # Assuming rows are returned as a list of dictionaries

#         else:
#             logging.error(f"Failed to query logs: {response_logs.error}")
#             return []

#     except Exception as e:
#         logging.error(f"Error querying logs: {e}")
#         return []

# register_function(
#     query_logs,
#     caller=coder,
#     executor=user_proxy,
#     name="query_logs",
#     description="This function queries logs from a specific log table in Log Analytics."
# )

# Define the function to save the results to a CSV file
def save_results_to_csv(results: List[Dict], filename: str = "azure_analysis_results.csv") -> str:
    """
    Saves the analysis results to a CSV file with better error handling and validation.

    Args:
        results (List[Dict]): The data to save to the CSV. Each dict represents a row in the CSV.
        filename (str): The name of the CSV file (default: "azure_analysis_results.csv").

    Returns:
        str: A message indicating the results were saved successfully or an error occurred.
    """
    # Step 1: Ensure results are valid
    if not results or len(results) == 0:
        return "No results to save."

    # Step 2: Ensure that all rows have consistent keys
    keys = results[0].keys()
    for result in results:
        if result.keys() != keys:
            logging.error(f"Inconsistent keys found in result: {result}")
            return "Error: Inconsistent data structure in results."

    try:
        # Step 3: Write the results to a CSV file
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)

        logging.info(f"Results successfully saved to {filename}")
        return f"Results successfully saved to {filename}"

    except Exception as e:
        # Step 4: Handle any errors that occur during file writing
        logging.error(f"Failed to save results to CSV: {e}")
        return f"Error saving results to CSV: {str(e)}"

# Register the save to CSV function
register_function(
    save_results_to_csv,
    caller=coder,
    executor=code_executor,
    name="save_results_to_csv",
    description="A tool to save results to CSV."
)





# Set up logging configuration
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# Initialize the LLM model using guidance
# import tiktoken

# enc = tiktoken.encoding_for_model("gpt-4o-mini")
# lm = guidance.models._azure_openai.AzureOpenAI(
#     model="gpt-4o-mini",
#     azure_endpoint="https://oai-jml.openai.azure.com",
#     api_key="5060bfdd7cbf48789d6ab72e350dc40f",
#     version="2024-07-18",
#     tokenizer=enc
    

# )


# Initialize GroupChat with the agents
groupchat = autogen.GroupChat(
    agents=[planner, coder, critic, user_proxy, code_executor], 
    messages=[],  
    max_round=50,
    speaker_selection_method="round_robin",
    select_speaker_prompt_template="Please select the next speaker from the list: {speaker_list}"
    )


# Start the conversation among the agents
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

import time
import asyncio
import json
from typing import List, Dict, Optional
from .guidance_validator.optimonkeyvalidator import start_prompt_validation
# Define the function to start the agent conversation
# async def start_agent_conversation_stream(prompt: Optional[str] = None):
#     """
#     Starts the agent conversation with the option to use a custom prompt.
#     """
#     global chat_status
#     chat_status = "Chat ongoing"

#     # Use default prompt if none is provided
#     if not prompt:
#         prompt = f"""
#         You are a professional Azure consultant.
#         Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage.
        
#         # Objective:
#         # Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations 
#         and by providing advice on what to do with the information.
        
#         # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs.
#         You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
#         # Planner: Plans the tasks and makes sure everything is on track.
#         # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
#         # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
#         # User Proxy: Executes the code and interacts with the system.

#         The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access
#         to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, 
#         querying usage metrics, getting log tables and querying these tables and saving results to a CSV file.
#         The Critic will evaluate the quality of the code and provide a score from 1 to 10.

#         # Task:
#         Please analyze my Azure environment and find top 5 opportunities to save money based on activity and/or usage. 
#         Provide proof data and metrics to justify this list. Give me only 5 recommendations to work with. 
#         You should start with run kusto query then, query metrics,... 
#         Look for Storage Accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
#         Provide advice on what to do with this information and output it along with the results in the CSV file.
#         Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
#         Make sure you use the functions in the right order and the code is well structured and easy to understand.
#         Make sure there is a CSV file with the results.
#         Make sure we only have top 5 recommendations.
#         """

#     # Run prompt validation and await it
#     validation_responses = await start_prompt_validation(prompt)

#     # Check overall validation based on confidence scores
#     avg_confidence = sum(response.get("confidence_score", 0) for response in validation_responses) / len(validation_responses)

#     if avg_confidence >= 3:
#         print("Prompt validation passed. Proceeding with conversation...")
#         time.sleep(5)
#         try:
#             # Start the conversation with the user proxy
#             user_proxy.initiate_chat(
#                 manager,
#                 message=prompt,  # Use the provided prompt
#                 max_round=50,
#                 clear_history=True
#             )
#             # Stream messages live as they are generated
#             last_message_count = 0
            
#             while True:

#                 current_message_count = len(manager.groupchat.messages)
#                 if current_message_count > last_message_count:
#                 # Collect the conversation messages to be streamed live as they are generated
#                     for message in manager.groupchat.messages:
#                         print(f"Streaming message: {message}")  # Log each message
#                         msg_content = {
#                             "content": message.get("content"),  # Extract the message content from the message dict
#                             "role": message.get("role"),
#                             "name": message.get("name"),
#                             "timestamp": datetime.now().strftime("%H:%M:%S"),
#                         }
#                         yield json.dumps(msg_content)
#                     last_message_count = current_message_count

#                 await asyncio.sleep(1)
#         except Exception as e:
#             error_message = {
#                 "content": f"An error occurred: {str(e)}",
#                 "role": "system",
#                 "name": "Error",
#                 "timestamp": datetime.now().strftime("%H:%M:%S"),
#             }
#             print(f"Error during agent conversation: {e}")
#             yield json.dumps(error_message)
#     else:
#         print("Prompt validation failed. Please correct the prompt and try again.")





async def start_agent_conversation_stream(prompt: Optional[str] = None):
    global chat_status
    chat_status = "Chat ongoing"
    print(f"Starting conversation with prompt: {prompt}")  # Add a debug log here

    # Use default prompt if none is provided
    if not prompt:
        prompt = "You are a professional Azure consultant. Analyze Azure environment..."

    try:
        # Log before starting validation
        print("Running prompt validation...")
        validation_responses = await start_prompt_validation(prompt)
 
        avg_confidence = sum(response.get("confidence_score", 0) for response in validation_responses) / len(validation_responses)
        print(f"Validation confidence score: {avg_confidence}")
        if avg_confidence < 3:
            print("Prompt validation failed. Please correct the prompt and try again.")
            for response in validation_responses:
                yield response
        elif avg_confidence >= 3:
            print("Prompt validation passed. Proceeding with conversation...")
            chat_result = user_proxy.initiate_chat(
                manager,
                message=prompt, 
                max_turns=2, 
                clear_history=True,
                summary_method="reflection_with_llm"
            )
            validation_responses.append(chat_result)
            summary = chat_result.summary
            # Safely access the summary key from the chat_result object
            if isinstance(summary, dict) and 'summary' in summary:
                summary_text = summary['summary']
            else:
                summary_text = str(summary)  # If it's not a dictionary, treat it as a string
            
            # Extract agent messages for recommendations
            recommendations = ""
            for message in manager.groupchat.messages:
                if "recommendation" in message.get("content", "").lower():
                    recommendations += f"\n{message.get('content')}"

            # Generate a smart summary using LLM
            # llm_summarization_prompt = f"""
            # Given the conversation details below, generate a comprehensive summary that includes key points, recommendations, and actionable insights:
            
            # Conversation Summary: {summary_text}
            # Recommendations: {recommendations}

            # Refine this summary to make it more insightful and include any missing information from the discussion.
            # """
            # # Have the coder agent summarize the conversation (example flow)
            # chat_result = user_proxy.initiate_chat(
            #     coder,
            #     message=llm_summarization_prompt,
            #     max_turns=2,
            #     summary_method="reflection_with_llm"
            # )
            # refined_summary = chat_result.summary # Use the LLM (coder) to refine the summary

            # Finalize the summary with recommendations
            final_summary = f"{summary_text}\n\nHere are the Recommendations:\n{recommendations}"

            # Return the final summary
            yield final_summary
        else:
            print("Prompt validation failed. Please correct the prompt and try again.")
    except Exception as e:
        yield f"An error occurred: {str(e)}"
        print(f"Error during agent conversation: {e}")
