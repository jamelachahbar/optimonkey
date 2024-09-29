import React from 'react';
import { Box, SimpleGrid, Text } from '@chakra-ui/react';

interface PromptTemplateProps {
  onSelectPrompt: (prompt: string) => void;
}

const prompts = [
  {
    title: 'Optimize Virtual Machines',
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
        # Your task is to analyze the Azure environment and find opportunities to save money on Virtual Machines on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.
        # You need to provide a list of Virtual Machines that are underutilized and suggest ways to save costs.`,
  },
  {
    title: 'Analyze Storage Accounts',
    description: 'Look for unused Storage Accounts and suggest ways to save costs',
    prompt: `Please analyze my Azure environment and find unused Storage Accounts to reduce costs on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.`,
  },
  {
    title: 'Optimize Disk Usage',
    description: 'Look for ways to optimize disk usage and save on costs.',
    prompt: `Please analyze my Azure environment and find opportunities to optimize disk usage on this subscription:38c26c07-ccce-4839-b504-cddac8e5b09d.`,
  },
];

const PromptTemplate: React.FC<PromptTemplateProps> = ({ onSelectPrompt }) => {
  return (
    <SimpleGrid columns={[1, 2, 3, 4]} spacing={6}>
      {prompts.map((template, index) => (
        <Box
          key={index}
          p={5}
          shadow="md"
          borderWidth="1px"
          borderRadius="md"
          onClick={() => onSelectPrompt(template.prompt)} // Trigger the onSelectPrompt handler on click
          cursor="pointer"
          _hover={{ bg: 'teal.200' }}
        >
          <Text fontSize="xl" fontWeight="bold">
            {template.title}
          </Text>
          <Text mt={2}>{template.description}</Text>
        </Box>
      ))}
    </SimpleGrid>
  );
};

export default PromptTemplate;
