import React, { useState, useRef, useEffect } from 'react';
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
  // width is now dynamic via sx
  height: '100vh',
  backgroundColor: '#333333',
  display: 'flex',
  flexDirection: 'column',
  borderRight: `1px solid ${theme.palette.divider}`,
  overflow: 'hidden',
  position: 'relative', // needed for the resize handle
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

const ResizeHandle = styled('div')(({ active }) => ({
  position: 'absolute',
  right: 0,
  top: 0,
  width: 6,
  height: '100%',
  cursor: 'col-resize',
  backgroundColor: active ? 'rgba(55, 148, 255, 0.25)' : 'transparent',
  transition: 'background-color 120ms ease',
  '&:hover': {
    backgroundColor: 'rgba(255,255,255,0.08)',
  },
}));

const Sidebar = ({ activeView, onViewChange }) => {
  const MIN_WIDTH = 48;   // VS Code activity bar-like minimum
  const MAX_WIDTH = 320;  // sane maximum
  const DEFAULT_WIDTH = 48;

  const containerRef = useRef(null);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const persisted = Number(localStorage.getItem('sidebarWidth'));
    return Number.isFinite(persisted) && persisted >= MIN_WIDTH && persisted <= MAX_WIDTH
      ? persisted
      : DEFAULT_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    if (!isResizing) return;

    const handleMove = (e) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const raw = e.clientX - rect.left; // distance from left edge of sidebar
      const next = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, raw));
      setSidebarWidth(next);
    };

    const handleUp = () => {
      setIsResizing(false);
      localStorage.setItem('sidebarWidth', String(sidebarWidth));
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing, sidebarWidth]);

  const views = [
    { id: 'dashboard', icon: <DashboardIcon />, label: 'Dashboard' },
    { id: 'databases', icon: <DatabaseIcon />, label: 'Databases' },
    { id: 'chat', icon: <ChatIcon />, label: 'AI Chat' },
  ];

  return (
    <SidebarContainer
      ref={containerRef}
      sx={{ width: sidebarWidth, userSelect: isResizing ? 'none' : undefined }}
    >
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

      {/* Drag handle */}
      <ResizeHandle
        active={isResizing ? 1 : 0}
        onMouseDown={(e) => {
          e.preventDefault();
          setIsResizing(true);
        }}
      />
    </SidebarContainer>
  );
};

export default Sidebar;