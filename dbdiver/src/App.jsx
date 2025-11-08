import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ApiProvider } from './contexts/ApiContext';
import { darkTheme } from './theme/darkTheme';
import MainLayout from './components/MainLayout';
import Dashboard from './components/Dashboard'; // Assuming Dashboard is a component

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
    <Router>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={darkTheme}>
          <CssBaseline />
          <ApiProvider>
            <MainLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                {/* Other routes */}
              </Routes>
            </MainLayout>
          </ApiProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </Router>
  );
}

export default App;
