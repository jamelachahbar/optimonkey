import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  useToast,
} from '@chakra-ui/react';

const EnvironmentSetup: React.FC = () => {
  const [openAIKey, setOpenAIKey] = useState('');
  const [otherVariable, setOtherVariable] = useState('');
  const toast = useToast();

  const handleSave = () => {
    // Save keys and variables to localStorage or send to backend
    localStorage.setItem('openai_key', openAIKey);
    localStorage.setItem('other_variable', otherVariable);

    toast({
      title: 'Environment Variables Saved',
      description: 'Your environment variables have been saved successfully.',
      status: 'success',
      duration: 3000,
      isClosable: true,
    });
  };

  return (
    <Box p={5}>
      <Heading as="h2" size="xl" mb={6}>
        Environment Setup
      </Heading>
      <VStack spacing={4} align="stretch">
        <FormControl id="openai-key">
          <FormLabel>OpenAI API Key</FormLabel>
          <Input
            type="password"
            value={openAIKey}
            onChange={(e) => setOpenAIKey(e.target.value)}
            placeholder="Enter OpenAI API Key"
          />
        </FormControl>

        <FormControl id="other-variable">
          <FormLabel>Other Variable</FormLabel>
          <Input
            type="text"
            value={otherVariable}
            onChange={(e) => setOtherVariable(e.target.value)}
            placeholder="Enter other variable"
          />
        </FormControl>

        <Button colorScheme="teal" onClick={handleSave}>
          Save
        </Button>
      </VStack>
    </Box>
  );
};

export default EnvironmentSetup;
