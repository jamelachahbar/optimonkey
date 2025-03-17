import { Box, Button, Heading, Text, Image, Center } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box height="100vh" display="flex" flexDirection="column" justifyContent="center" alignItems="center" p={5}>
      {/* Dark Mode Toggle - Keeping only the one on the right */}
      {/* <Button 
        onClick={toggleColorMode}
        position="absolute"
        top="1rem"
        right="1rem"
        colorScheme="teal"
        size="sm"
      >
        {colorMode === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      </Button> */}

      {/* Centered Content */}
      <Center flexDirection="column">
        <Image src="optimonkeylogo-1.png" alt="OptiMonkey Logo" boxSize="200px" mb={5} />
        <Heading as="h1" size="2xl" mb={4}>
          Welcome to OptiMonkey
        </Heading>
        <Text fontSize="lg" textAlign="center" mb={6}>
          Optimize your cloud and financial resources with ease and intelligence. Let OptiMonkey do the heavy lifting for you.
        </Text>
        <Button colorScheme="teal" size="lg" onClick={() => navigate('/dashboard')}>
          Get Started
        </Button>
      </Center>
    </Box>
  );
};

export default LandingPage;
