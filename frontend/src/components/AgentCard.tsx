import React from 'react';
import { Box, Text, VStack } from '@chakra-ui/react';

interface AgentCardProps {
  name: string;
  description: string;
}

const AgentCard: React.FC<AgentCardProps> = ({ name, description }) => (
  <Box p={4} borderWidth="1px" borderRadius="md" shadow="sm">
    <VStack>
      <Text fontSize="lg" fontWeight="bold">{name}</Text>
      <Text fontSize="sm" color="gray.600">{description}</Text>
    </VStack>
  </Box>
);

export default AgentCard;
