import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApiProvider } from './contexts/ApiContext';
import { darkTheme } from './theme/darkTheme';
import MainLayout from './components/MainLayout';

// Create query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <ApiProvider>
          <MainLayout />
        </ApiProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
