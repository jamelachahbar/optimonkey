import { Box, Flex, Text, Button } from "@chakra-ui/react";

const OptiMonkeyLayout = () => {
  return (
    <Flex h="100vh">
      {/* Sidebar */}
      <Box w="20%" bg="gray.800" p="4" color="white">
        <Text fontSize="xl">OptiMonkey</Text>
        <Button variant="link" colorScheme="whiteAlpha">New Chat</Button>
        <Button variant="link" colorScheme="whiteAlpha">Reconciliation</Button>
        <Button variant="link" colorScheme="whiteAlpha">Welcome</Button>
      </Box>

      {/* Main Content */}
      <Box flex="1" p="4">
        <Text fontSize="2xl">Optimization Chat</Text>
        <Box h="80%" bg="gray.100" p="4" borderRadius="md">
          {/* Placeholder for WebSocket Chat */}
        </Box>
      </Box>

      {/* Agent Info Panel */}
      <Box w="20%" bg="gray.50" p="4">
        <Text fontSize="lg">Agent Details</Text>
        <Text fontSize="sm">Description: Optimizing Azure resources...</Text>
      </Box>
    </Flex>
  );
};

export default OptiMonkeyLayout;
