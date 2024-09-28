import React, { Component, ReactNode } from 'react';
import { Box, Heading, Text } from '@chakra-ui/react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.error("Error caught by ErrorBoundary:", error);
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Detailed error information:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box textAlign="center" py={10} px={6}>
          <Heading as="h1" size="xl" mb={4}>
            Something went wrong.
          </Heading>
          <Text color="gray.500">
            Please try again later or contact support if the issue persists.
          </Text>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
