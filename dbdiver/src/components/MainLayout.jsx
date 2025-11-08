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
        return <Dashboard />;
      case 'databases':
        return <DatabaseConnection />;
      case 'chat':
        return <ChatInterface />;
      default:
        return <ChatInterface />;
    }
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
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
      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {renderMainContent()}
      </Box>
    </Box>
  );
};

export default MainLayout;