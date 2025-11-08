import React, { useState } from 'react';
import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  Tooltip,
  styled,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Storage as DatabaseIcon,
  Psychology as ChatIcon,
  Settings as SettingsIcon,
  Extension as ExtensionsIcon,
} from '@mui/icons-material';

const SidebarContainer = styled(Box)(({ theme }) => ({
  width: 48,
  height: '100vh',
  backgroundColor: '#333333',
  display: 'flex',
  flexDirection: 'column',
  borderRight: `1px solid ${theme.palette.divider}`,
  overflow: 'hidden',
}));

const StyledListItemButton = styled(ListItemButton)(({ theme, selected }) => ({
  height: 48,
  padding: 0,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  color: selected ? '#ffffff' : '#858585',
  borderLeft: selected ? '2px solid #3794ff' : '2px solid transparent',
  backgroundColor: selected ? 'rgba(55, 148, 255, 0.1)' : 'transparent',
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    color: '#ffffff',
  },
}));

const Sidebar = ({ activeView, onViewChange }) => {
  const views = [
    { id: 'dashboard', icon: <DashboardIcon />, label: 'Dashboard' },
    { id: 'databases', icon: <DatabaseIcon />, label: 'Databases' },
    { id: 'chat', icon: <ChatIcon />, label: 'AI Chat' },
  ];

  return (
    <SidebarContainer>
      <List sx={{ flex: 1, p: 0 }}>
        {views.map((view) => (
          <Tooltip key={view.id} title={view.label} placement="right">
            <StyledListItemButton
              selected={activeView === view.id}
              onClick={() => onViewChange(view.id)}
            >
              <ListItemIcon
                sx={{
                  minWidth: 'auto',
                  color: 'inherit',
                }}
              >
                {view.icon}
              </ListItemIcon>
            </StyledListItemButton>
          </Tooltip>
        ))}
      </List>

      {/* Bottom icons */}
      <List sx={{ p: 0 }}>
        <Tooltip title="Settings" placement="right">
          <StyledListItemButton>
            <ListItemIcon sx={{ minWidth: 'auto', color: 'inherit' }}>
              <SettingsIcon />
            </ListItemIcon>
          </StyledListItemButton>
        </Tooltip>
      </List>
    </SidebarContainer>
  );
};

export default Sidebar;