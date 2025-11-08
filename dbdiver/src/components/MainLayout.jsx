import React, { useState } from 'react';
import { Box } from '@mui/material';
import Sidebar from './Sidebar';
import DatabaseTreePanel from './DatabaseTreePanel';
import ChatInterface from './ChatInterface';
import Dashboard from './Dashboard';
import DatabaseConnection from './DatabaseConnection';

const MainLayout = () => {
  const [activeView, setActiveView] = useState('chat');
  const [isPanelOpen, setIsPanelOpen] = useState(true);

  const renderMainContent = () => {
    switch (activeView) {
      case 'dashboard':
        return <Dashboard onViewChange={setActiveView} />; // Pass the function
      case 'databases':
        return <DatabaseConnection />;
      case 'chat':
        return <ChatInterface />;
      default:
        return <ChatInterface />;
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        minHeight: '100vh', // Changed from height: '100vh' to minHeight
        // Removed overflow: 'hidden' to allow scrolling
      }}
    >
      {/* Left Sidebar */}
      <Sidebar activeView={activeView} onViewChange={setActiveView} />

      {/* Database Tree Panel */}
      {activeView !== 'dashboard' && (
        <DatabaseTreePanel
          isOpen={isPanelOpen}
          onClose={() => setIsPanelOpen(false)}
        />
      )}

      {/* Main Content Area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto', // Changed from 'hidden' to 'auto' to enable scrolling
          maxHeight: '100vh', // Add max height to prevent infinite growth
        }}
      >
        {renderMainContent()}
      </Box>
    </Box>
  );
};

export default MainLayout;