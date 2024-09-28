import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import { useColorMode, Button, Box } from '@chakra-ui/react';
import Dashboard from './components/Dashboard';
import ErrorBoundary from './components/ErrorBoundary';  // Import the ErrorBoundary component
import EnvironmentSetup from './components/EnvironmentSetup'; // Import the EnvironmentSetup component

const App: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode();
  
  return (
    <Box>
      {/* Dark Mode Toggle */}
      <Button 
        onClick={toggleColorMode}
        position="absolute"
        top="1rem"
        right="1rem"
        colorScheme="teal"
        size="sm"
      >
        {colorMode === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
      </Button>

      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route 
            path="/dashboard" 
            element={
              <ErrorBoundary>
                <Dashboard />
              </ErrorBoundary>
            }
          />
          {/* Add the new route for environment setup */}
          <Route path="/environment-setup" element={<EnvironmentSetup />} />
          <Route path='/error' element={<h1>Oops! Something went wrong.</h1>} />
        </Routes>
      </Router>
    </Box>
  );
};

export default App;
