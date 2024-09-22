import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import { useColorMode, Button, Box } from '@chakra-ui/react';
import Dashboard from './components/Dashboard';
const App: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode();
  return (
    <Box>
      {/* Dark Mode Toggle - Keeping only the one on the right */}
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
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </Router>
    </Box>

  );
};

export default App;
