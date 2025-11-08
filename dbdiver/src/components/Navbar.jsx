import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  useTheme,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  QuestionAnswer as QueryIcon,
  Psychology as BrainIcon,
  Refresh as RefreshIcon,
  Menu as MenuIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useApi } from '../contexts/ApiContext';

const Navbar = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();
  const { connections, ragOverview, healthData } = useApi();

  const [mobileOpen, setMobileOpen] = React.useState(false);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: <DashboardIcon /> },
    { path: '/connections', label: 'Connections', icon: <StorageIcon /> },
    { path: '/query', label: 'NLP Query', icon: <QueryIcon /> },
  ];

  const connectionCount = Object.keys(connections).length;
  const documentCount = ragOverview.total_documents || 0;
  const isHealthy = healthData?.status === 'healthy';

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box sx={{ width: 250, mt: 2 }}>
      <List>
        {navItems.map((item) => (
          <ListItem
            button
            key={item.path}
            onClick={() => {
              navigate(item.path);
              setMobileOpen(false);
            }}
            selected={location.pathname === item.path}
            sx={{
              mx: 1,
              borderRadius: 2,
              '&.Mui-selected': {
                backgroundColor: theme.palette.primary.main + '20',
                '&:hover': {
                  backgroundColor: theme.palette.primary.main + '30',
                },
              },
            }}
          >
            <ListItemIcon sx={{ color: location.pathname === item.path ? theme.palette.primary.main : 'inherit' }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText 
              primary={item.label}
              sx={{ 
                '& .MuiListItemText-primary': { 
                  fontWeight: location.pathname === item.path ? 600 : 400 
                }
              }}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar 
        position="static" 
        elevation={4}
        sx={{
          background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 64, md: 70 } }}>
          {isMobile && (
            <IconButton
              color="inherit"
              aria-label="open drawer"
              edge="start"
              onClick={handleDrawerToggle}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}

          <BrainIcon sx={{ mr: 2, fontSize: { xs: 28, md: 32 } }} />
          <Typography 
            variant="h5" 
            component="div" 
            sx={{ 
              flexGrow: 1,
              fontWeight: 700,
              fontSize: { xs: '1.2rem', md: '1.5rem' }
            }}
          >
            DB RAG Analytics
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, md: 2 } }}>
            {/* Status indicators */}
            {!isMobile && (
              <>
                <Chip
                  icon={<StorageIcon fontSize="small" />}
                  label={`${connectionCount} DB${connectionCount !== 1 ? 's' : ''}`}
                  color={connectionCount > 0 ? 'success' : 'default'}
                  size="small"
                  sx={{ 
                    backgroundColor: connectionCount > 0 ? 'success.main' : 'rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: 600,
                  }}
                />
                
                <Chip
                  label={`${documentCount} docs`}
                  color={documentCount > 0 ? 'secondary' : 'default'}
                  size="small"
                  sx={{ 
                    backgroundColor: documentCount > 0 ? 'secondary.main' : 'rgba(255,255,255,0.2)',
                    color: 'white',
                    fontWeight: 600,
                  }}
                />

                <Chip
                  label={isHealthy ? 'Healthy' : 'Offline'}
                  color={isHealthy ? 'success' : 'error'}
                  size="small"
                  sx={{ 
                    backgroundColor: isHealthy ? 'success.main' : 'error.main',
                    color: 'white',
                    fontWeight: 600,
                  }}
                />
              </>
            )}

            {/* Navigation buttons - Desktop only */}
            {!isMobile && navItems.map((item) => (
              <Button
                key={item.path}
                color="inherit"
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                variant={location.pathname === item.path ? 'outlined' : 'text'}
                sx={{
                  borderColor: location.pathname === item.path ? 'white' : 'transparent',
                  fontWeight: location.pathname === item.path ? 600 : 400,
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.1)',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}

            <IconButton
              color="inherit"
              onClick={() => window.location.reload()}
              title="Refresh"
              sx={{
                '&:hover': {
                  backgroundColor: 'rgba(255,255,255,0.1)',
                },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        anchor="left"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { 
            boxSizing: 'border-box', 
            width: 250,
          },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
};

export default Navbar;