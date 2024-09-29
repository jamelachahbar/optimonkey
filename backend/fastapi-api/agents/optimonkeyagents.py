from typing import Literal, Optional, List, Dict
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
from azure.mgmt.monitor import MonitorManagementClient
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

# Fetch the Bing API key from the environment variables, only if we use web search
bing_api_key = os.getenv("BING_API_KEY")

# if not bing_api_key:
#     raise ValueError("Error: Missing Bing API key.")
# else:
#     print(f"Bing API Key Loaded Successfully: {bing_api_key}")

# Define the configuration for the LLM model
config_list = autogen.config_list_from_json("./agents/OAI_CONFIG_LIST.json")
llm_config = {
    "config_list": config_list, 
    "cache_seed": 42,
    "timeout": 180
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


# Initialize the Planner assistant
planner = autogen.AssistantAgent(
    name="Planner",
    system_message="""You are a helpful AI Assistant. You are the planner of this team of assistants. 
    You plan the tasks and make sure everything is on track. Suggest a plan. 
    Revise the plan if needed. When the plan is solid and ready to be executed, pass it to the Coder. 
    Also make sure the plan includes the functions the Coder can call and the order in which they should be called.
    The run_kusto_query function should be called first, then the query_usage_metrics function, also use get_log_tables_and_query and finally the save_results_to_csv function. 
    """,
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
    system_message="You are a helpful AI Assistant. You are the user proxy. You can execute the code and interact with the system.",
    description="""User Proxy is a user who can execute the code and interact with the system. 
    I also check if the plan was applied and the output we have is according to the instructions. 
    If not, I will ask the planner to revise the plan. Make sure all the functions are called in the right order and the code is well structured and easy to understand. Also make sure there is an output and 
    the output is according to the instructions. Make sure there sis a CSV file with the results.""",
    max_consecutive_auto_reply=3,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": "python:3.10"
    }
)

# Initialize the Code_Guru assistant for coding tasks
coder = autogen.AssistantAgent(
    name="Code_Guru",
    system_message="""You are a helpful AI assistant. You are a highly experienced programmer specialized in Azure. 
    Follow the approved plan and save the code to disk. Always use functions you have access to and start with run_kusto_query, 
    then the next function which is query_usage_metrics, and so on.
    The user cannot provide any other feedback or perform any other action beyond executing the code you suggest. 
    If the result indicates there is an error, fix the error and output the code again.
    Always use functions you have access to and start with run_kusto_query, 
    then the next function which is query_usage_metrics, and then query_log_analytics and in the END use the save_results_to_csv function.
    TERMINATE the conversation when the task is complete.""", 
    description="I'm a highly experienced programmer specialized in Python, bash. I am **ONLY** allowed to speak **immediately** after `Planner` and before `UserProxy`.",
    llm_config={
        "config_list": config_list,
        "temperature": 0
    },
    human_input_mode="TERMINATE"
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
    human_input_mode="NEVER"
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
        metric_names = metric_names or ['Composite Disk Read Bytes/sec', 'Composite Disk Write Bytes/sec']
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
    executor=user_proxy,
    name="query_usage_metrics",
    description="This function allows the agent to Query Azure Monitor metrics for the specified resource and metrics."
)



from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient
from typing import Optional, List, Dict
from datetime import timedelta
import logging

# Initialize Logs Query Client with default Azure credentials
credential = DefaultAzureCredential()
logs_client = LogsQueryClient(credential)

# Function to dynamically retrieve log tables and allow the agent to figure out the query
def get_log_tables_and_query(
    workspace_id: str,
    resource_type: str,
    metric: Optional[str] = None,
    operation_name: Optional[str] = None
) -> List[Dict]:
    """
    Retrieves log tables from Log Analytics and allows the agent to dynamically figure out the correct query based on the
    available tables and resource type. After receiving the tables, the agent determines the correct KQL query to run.

    Args:
        workspace_id (str): The Log Analytics Workspace ID.
        resource_type (str): The type of resource (e.g., 'storage_account', 'virtual_machine').
        metric (Optional[str]): The specific metric to query (e.g., 'LastAccessTime'). Default is None.
        operation_name (Optional[str]): The operation name to filter the query (e.g., 'GetBlob'). Default is None.

    Returns:
        List[Dict]: A list of results after querying the logs based on the agent's decision.
    """

    # Step 1: Query log tables from Log Analytics workspace
    kusto_query_tables = """
    union *
    | summarize by Type
    | where Type contains 'Logs'
    | summarize by Type
    """

    try:
        # Execute the query to get log tables
        response_tables = logs_client.query_workspace(
            workspace_id="fdd39622-ae5a-4eb8-987b-14ae8aad63dd",
            query=kusto_query_tables,
            timespan=(None, timedelta(days=30))  # Query logs for the last 30 days
        )

        if response_tables.status == 'Success':
            available_tables = []
            table = response_tables.tables[0]
            for row in table.rows:
                available_tables.append({"table_name": row[0]})  # Return all log tables

            if not available_tables:
                raise ValueError(f"No log tables available for resource type: {resource_type}")

            # Step 2: Provide the available tables to the agent
            logging.info(f"Available tables for {resource_type}: {available_tables}")

            # At this point, the agent is expected to decide on the correct table and the query.
            # This means the agent can choose from the list of tables and create a query based on the resource_type and the available tables.

            # The agent will now construct the correct Kusto query for the required resource and metric based on the available tables.
            return {"available_tables": available_tables}  # Let the agent decide the next step

        else:
            logging.error(f"Failed to retrieve log tables: {response_tables.error}")
            return []

    except Exception as e:
        logging.error(f"Error retrieving log tables: {e}")
        return []

# Register the function that returns the available log tables for the agent to work with
register_function(
    get_log_tables_and_query,
    caller=coder,
    executor=user_proxy,
    name="get_log_tables_and_query",
    description="This function retrieves available log tables from Log Analytics and allows the agent to decide on the query."
)

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
# Define the function to start the agent conversation
def start_agent_conversation(prompt: Optional[str] = None):
    """
    Starts the agent conversation with the option to use a custom prompt.
    """
    # Use default prompt if none is provided
    if not prompt:
        prompt = f"""
        You are a professional Azure consultant.
        Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage.
        
        # Objective:
        # Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations 
        and by providing advice on what to do with the information.
        
        # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs.
        You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
        # Planner: Plans the tasks and makes sure everything is on track.
        # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
        # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
        # User Proxy: Executes the code and interacts with the system.

        The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access
        to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, 
        extracting resource IDs, querying usage metrics, and saving results to a CSV file.
        The Critic will evaluate the quality of the code and provide a score from 1 to 10.

        # Task:
        Please analyze my Azure environment and find top 5 opportunities to save money based on activity and/or usage. 
        Provide proof data and metrics to justify this list. Give me only 5 recommendations to work with. 
        Do not run the analyze resources and query metrics function first. 
        You should start with run kusto query then extract resource id then query metrics,... 
        Look for Storage Accounts on these subscriptions or one of these {subscription_id} and save it to a CSV file.
        Provide advice on what to do with this information and output it along with the results in the CSV file.
        Make sure you assert these resources are not being used much or not at all based on usage over the last {days} days.
        Make sure you use the functions in the right order and the code is well structured and easy to understand.
        Make sure there is a CSV file with the results.
        Make sure we only have top 5 recommendations.
        """
    
    # Start the conversation with the user proxy
    user_proxy.initiate_chat(
        manager,
        message=prompt  # Use the provided prompt
    )
    
    # Collect the conversation messages
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

