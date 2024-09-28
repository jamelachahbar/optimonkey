// PromptTemplates component: smaller cards
import React from 'react';
import { Box, Button, VStack, useColorModeValue, Flex, Heading } from '@chakra-ui/react';

interface PromptTemplatesProps {
  onSelectPrompt: (prompt: string) => void;
}

const PromptTemplates: React.FC<PromptTemplatesProps> = ({ onSelectPrompt }) => {
  const prompts = [
    { title: 'Cost Optimization', prompt: 'Analyze Azure costs' },
    { title: 'Storage Utilization', prompt: 'Analyze Storage utilization' },
  ];

  return (
    <Flex justify="center">
      <VStack spacing={4} align="center">
        {prompts.map((template, index) => (
          <Box
            key={index}
            p={3}
            borderWidth="1px"
            borderRadius="lg"
            bg={useColorModeValue('white', 'gray.700')}
            width="100%"
          >
            <Heading as="h3" size="sm" mb={2} textAlign="center">{template.title}</Heading>
            <Button size="sm" colorScheme="teal" onClick={() => onSelectPrompt(template.prompt)}>Use this prompt</Button>
          </Box>
        ))}
      </VStack>
    </Flex>
  );
};

export default PromptTemplates;
