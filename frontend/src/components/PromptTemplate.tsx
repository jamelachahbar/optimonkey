import React from 'react';
import { Box, SimpleGrid, Text, Icon } from '@chakra-ui/react';
import { FaServer, FaDatabase, FaHdd, FaNetworkWired, FaInfinity } from 'react-icons/fa'; // Import some icons for illustration

// const workspace_id = "fdd39622-ae5a-4eb8-987b-14ae8aad63dd"

interface PromptTemplateProps {
  onSelectPrompt: (prompt: string) => void;
  
}

const prompts = [
  {
    title: 'Optimize Virtual Machines Cost',
    description: 'Find opportunities to optimize Virtual Machines usage and save costs.',
    prompt: `You are a professional Azure consultant.
        Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage.
        
        # Objective:
        # Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations 
        and by providing advice on what to do with the information.
        
        # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs.

        # Scenario:
        You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
        # Planner: Plans the tasks and makes sure everything is on track.
        # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
        # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
        # User Proxy: Executes the code and interacts with the system.
        
        The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access
        to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, 
        extracting resource IDs, querying usage metrics, and saving results to a CSV file.
        The Critic will evaluate the quality of the code and provide a score from 1 to 10.
        The User Proxy will execute the code and interact with the system. He will provide the results to the user.

        # Task:
        Your task is to analyze the Azure environment and find opportunities to save money on Virtual Machines on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.
        You need to provide a top 5 of Virtual Machines that are underutilized and suggest ways to save costs.
        
        Example Output:
        vm_name,cpu_usage,network_usage,disk_usage,recommendation
        VM-LINUX-01,1.3%,Moderate,Moderate,Downgrade VM size or reduce provisioning.
        vmwithhibernationmode,38.97%,High,High,Review VM size and performance needs.
        vm-forcedetachdemo1-1,0%,None,None,Consider deactivating unused VMs.
        vm-forcedetachdemo1-2,0%,None,None,Consider deactivating unused VMs.`,
    icon: FaServer, // Adding an icon for each prompt

  },
  {
    title: 'Analyze Storage Accounts',
    description: 'Look for unused Storage Accounts and suggest ways to save costs',
    prompt: `You are a professional Azure consultant.
        Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage.
        
        # Objective:
        # Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations 
        and by providing advice on what to do with the information.
        
        # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs, Bash, Azure CLI.

        # Scenario:
        You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
        # Planner: Plans the tasks and makes sure everything is on track.
        # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
        # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
        # User Proxy: Executes the code and interacts with the system.
        
        The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access
        to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, 
        querying usage metrics, and saving results to a CSV file.
        The Critic will evaluate the quality of the code and provide a score from 1 to 10.
        The User Proxy will execute the code and interact with the system. He will provide the results to the user.

        # Task:
        Please analyze my Azure environment and find unused Storage Accounts to reduce costs on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.
        You need to provide a list of Storage Accounts that are underutilized and suggest ways to save costs.
        Make sure it is only 5 recommendations.
        #EXAMPLE OUTPUT 1:
        storage_account,used_capacity,transactions,ingress,egress,lastAccessDateTime,recommendation
        czoiuoiuoiuoiuoui,910973.0,688.0,4754574.91,592695.95,2024-09-22 12:24:22,Downgrade performance tier or consolidate.
        finopshub0275wqmmubtdx2s,3440610024216.0,313.0,9994452.5,25520874.67,2024-09-22 12:24:22,Review data retention policies.
        mgmtbadc,146695832668.0,716.0,5070592.38,615573.99,2024-09-20 02:24:22,Consider decommissioning.
        mgmtbdaa,6395518333247.0,720.0,2427408.17,3740955.29,2024-09-10 18:24:22,Move infrequently accessed data to cooler tiers.
        stgaccttest123654,43706232.0,720.0,465675.77,593185.56,2024-09-18 12:04:22,Merge accounts or downgrade.
        
        EXAMPLE OUTPUT 2:
        Resource Name,Usage Metrics,Recommendation,Justification,Advice
        czoiuoiuoiuoiuoui,"UsedCapacity: 912240.0, Transactions: 711.0",Consider downgrading or consolidating data if not mission-critical.,Low transactions with significant storage.,Review stored data for redundancy.
        finopshub0275wqmmubtdx2s,"UsedCapacity: 3452545608015.0, Transactions: 316.0",Evaluate retention policy for data.,Moderate transactions but high use of premium storage tier.,Move less accessed data to cheaper storage options.
        mgmtbadc,"UsedCapacity: 146679634924.0, Transactions: 717.0",Optimize ingress and cleanup infrequently accessed data.,High ingress vs. egress disparity.,Conduct regular audits to manage storage efficiently.
        mgmtbdaa,"UsedCapacity: 6409680069847.0, Transactions: 720.0",Consider tiering or archive options for unused data.,Large capacity use with minimal access.,Balance data availability needs with storage costs.
        stgaccttest123654,"UsedCapacity: 44113307.0, Transactions: 720.0",Evaluate data lifecycle management.,Consistent low transactions suggest potential over-allocation.,Identify stale data and set rules for automatic deletion.`,
    icon: FaDatabase,
  },
  {
    title: 'Optimize Disk Usage',
    description: 'Look for ways to optimize disk usage and save on costs.',
    prompt: `
    You are a professional Azure consultant.
        Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage.
        
        # Objective:
        # Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations 
        and by providing advice on what to do with the information.
        
        # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs.

        # Scenario:
        You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
        # Planner: Plans the tasks and makes sure everything is on track.
        # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
        # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
        # User Proxy: Executes the code and interacts with the system.
        
        The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access
        to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, 
        querying usage metrics, and saving results to a CSV file.
        The Critic will evaluate the quality of the code and provide a score from 1 to 10.
        The User Proxy will execute the code and interact with the system. He will provide the results to the user.
        #Task: 
        Please analyze my Azure environment and find opportunities to optimize disk usage on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.
        
        #Example Output 1:
        disk_resource_id,disk_state,disk_type,disk_size,used_capacity,read_iops,write_iops,read_throughput,write_throughput,recommendation
        /subscriptions/38c26c07-ccce-4839-b504-cddac8e5b09d/resourceGroups/acodemos/providers/Microsoft.Compute/disks/hackatonunuseddisk,Unattached,,,0,0,0,0,0,Consider decommissioning.
        /subscriptions/38c26c07-ccce-4839-b504-cddac8e5b09d/resourceGroups/MGMT/providers/Microsoft.Compute/disks/VM-LINUX-01_OsDisk_1_765c8e478e9148afa4ba3d2dc370d52e,Reserved,,,13821,57087,0,13821,57087,Consider removing unattached disks.
        `,
        icon: FaHdd,
  },
  {
    title: 'Optimize Network Usage Cost',
    description: 'Find ways to optimize network usage and save on costs.',
    prompt: `You are a professional Azure consultant. Your role is to analyze the Azure environment and find opportunities to save money based on activity and usage. 
    # Objective: Your goal is to provide the user with a smooth, efficient and friendly experience by either providing proof data and metrics to justify the list of recommendations and by providing advice on what to do with the information.
    # Tools: Azure Resource Graph, Azure Monitor, Azure SDKs.
    # Scenario: You have a team of assistants to help you with the task. The agents are: Planner, Coder, Critic, and User Proxy.
    # Planner: Plans the tasks and makes sure everything is on track.
    # Coder: Writes the code to analyze the Azure environment and save the results to a CSV file.
    # Critic: Evaluates the quality of the code and provides a score from 1 to 10.
    # User Proxy: Executes the code and interacts with the system.
    The Coder will write the code to analyze the Azure environment and save the results to a CSV file. He has access to the Azure SDKs and can execute the code based on functions provided by the Planner. These functions include running a Kusto query, querying usage metrics, and saving results to a CSV file.
    The Critic will evaluate the quality of the code and provide a score from 1 to 10.
    The User Proxy will execute the code and interact with the system. He will provide the results to the user.
    # Task: Please analyze my Azure environment and find opportunities to optimize network usage on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.
    #Example Output 1:
    network_resource_id,network_type,ingress,ingress_rate,egress,egress_rate,used_capacity,recommendation
    /subscriptions/38c26c07-ccce-4839-b504-cddac8e5b09d/resourceGroups/MGMT/providers/Microsoft.Network/networkInterfaces/VM-LINUX-01_NetworkInterface_1,Public,0,0,0,0,0,Consider removing unused network interfaces.
    /subscriptions/38c26c07-ccce-4839-b504-cddac8e5b09d/resourceGroups/MGMT/providers/Microsoft.Network/networkSecurityGroups/VM-LINUX-01_NSG,Private,0,0,0,0,0,Review network security rules for optimization.
    
    `,
    icon: FaNetworkWired,

  },
  {
    title: 'Generate New Insights from my environment',
    description: 'Find new insights from my environment.',
    prompt: `You are a team of azure experts and your job is to generate new insights from the Azure environment. 
    Use the functions you have access to.
    My subscription ID is 38c26c07-ccce-4839-b504-cddac8e5b09d.
    `,
    icon: FaInfinity,

  }
];

const PromptTemplate: React.FC<PromptTemplateProps> = ({ onSelectPrompt }) => {
  return (
    <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 4 }} spacing={6} p={4}>
      {prompts.map((template, index) => (
        <Box
          key={index}
          p={6}
          shadow="lg"
          borderWidth="1px"
          borderRadius="md"
          onClick={() => onSelectPrompt(template.prompt)}
          cursor="pointer"
          transition="all 0.3s ease"
          _hover={{
            bg: 'teal.400',
            transform: 'scale(1.05)',
            shadow: 'xl',
            color: 'white',
          }}
          display="flex"
          flexDirection="column"
          alignItems="center"
          textAlign="center"
        >
          <Icon as={template.icon} w={10} h={10} mb={4} color="teal.600" />
          <Text fontSize="md" fontWeight="bold" mb={2}>
            {template.title}
          </Text>
          <Text fontSize="sm">
            {template.description}
          </Text>
        </Box>
      ))}
    </SimpleGrid>
  );
};

export default PromptTemplate;