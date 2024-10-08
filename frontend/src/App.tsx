import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'; // Import React Query components
import LandingPage from './components/LandingPage';
import { useColorMode, Button, Box } from '@chakra-ui/react';
import Dashboard from './components/Dashboard';
import OptiMonkeyLayout from './components/OptiMonkeyLayout';
import { MoonIcon, SunIcon } from '@chakra-ui/icons'; // Importing icons for color mode

// Create a new QueryClient instance
const queryClient = new QueryClient();

const App: React.FC = () => {
  const { colorMode, toggleColorMode } = useColorMode();

  return (
    <QueryClientProvider client={queryClient}>
      <Box>
              {/* Color Mode Toggle */}
              <Button onClick={toggleColorMode}               
              >
                {colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
              </Button>

        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/optimonkeylayout" element={<OptiMonkeyLayout />} />

          </Routes>
        </Router>
      </Box>
    </QueryClientProvider>
  );
};

export default App;
