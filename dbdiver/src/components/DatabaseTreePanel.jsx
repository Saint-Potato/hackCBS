import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Collapse,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  styled,
  Divider,
  Tooltip,
  TextField,
  InputAdornment,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ChevronRight as ChevronRightIcon,
  Storage as DatabaseIcon,
  Folder as FolderIcon,
  TableChart as TableIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useApi } from '../contexts/ApiContext';

const PanelContainer = styled(Box)(({ theme }) => ({
  width: 300,
  height: '100vh',
  backgroundColor: theme.palette.background.paper,
  borderRight: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
}));

const PanelHeader = styled(Box)(({ theme }) => ({
  padding: '8px 12px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  borderBottom: `1px solid ${theme.palette.divider}`,
  minHeight: 35,
}));

const TreeListItem = styled(ListItemButton)(({ theme, depth = 0 }) => ({
  paddingLeft: theme.spacing(1 + depth * 2),
  paddingTop: 2,
  paddingBottom: 2,
  minHeight: 28,
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  '&.Mui-selected': {
    backgroundColor: 'rgba(55, 148, 255, 0.15)',
    '&:hover': {
      backgroundColor: 'rgba(55, 148, 255, 0.2)',
    },
  },
}));

const DatabaseTreePanel = ({ isOpen, onClose }) => {
  const { connections, ragOverview, discoverSchema, isDiscoveringSchema } = useApi();
  const [expandedConnections, setExpandedConnections] = useState({});
  const [expandedDatabases, setExpandedDatabases] = useState({});
  const [selectedItem, setSelectedItem] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const toggleConnection = (connectionId) => {
    setExpandedConnections(prev => ({
      ...prev,
      [connectionId]: !prev[connectionId],
    }));
  };

  const toggleDatabase = (dbName) => {
    setExpandedDatabases(prev => ({
      ...prev,
      [dbName]: !prev[dbName],
    }));
  };

  const handleSelectItem = (item) => {
    setSelectedItem(item);
  };

  const databases = ragOverview?.databases || {};

  if (!isOpen) return null;

  return (
    <PanelContainer>
      {/* Header */}
      <PanelHeader>
        <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: 11, textTransform: 'uppercase', color: 'text.secondary' }}>
          Databases
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <Tooltip title="Add Connection">
            <IconButton size="small" sx={{ padding: '2px' }}>
              <AddIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Refresh">
            <IconButton size="small" sx={{ padding: '2px' }}>
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Close Panel">
            <IconButton size="small" sx={{ padding: '2px' }} onClick={onClose}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </PanelHeader>

      {/* Search Bar */}
      <Box sx={{ p: 1 }}>
        <TextField
          size="small"
          fullWidth
          placeholder="Search databases..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" sx={{ color: 'text.secondary' }} />
              </InputAdornment>
            ),
            sx: { fontSize: 13, height: 28 }
          }}
        />
      </Box>

      <Divider />

      {/* Tree View */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <List dense disablePadding>
          {Object.keys(connections).length === 0 ? (
            <Box sx={{ p: 2, textAlign: 'center' }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: 12 }}>
                No connections available
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: 11 }}>
                Add a database connection to get started
              </Typography>
            </Box>
          ) : (
            Object.entries(connections).map(([connKey, conn]) => {
              const dbInfo = databases[conn.database];
              const isExpanded = expandedConnections[connKey];

              return (
                <React.Fragment key={connKey}>
                  {/* Connection Level */}
                  <TreeListItem
                    depth={0}
                    onClick={() => toggleConnection(connKey)}
                    selected={selectedItem === connKey}
                  >
                    <ListItemIcon sx={{ minWidth: 24 }}>
                      {isExpanded ? (
                        <ExpandMoreIcon fontSize="small" sx={{ fontSize: 16 }} />
                      ) : (
                        <ChevronRightIcon fontSize="small" sx={{ fontSize: 16 }} />
                      )}
                    </ListItemIcon>
                    <ListItemIcon sx={{ minWidth: 28 }}>
                      <DatabaseIcon fontSize="small" sx={{ fontSize: 16, color: '#3794ff' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={conn.database}
                      secondary={`${conn.type} • ${conn.host}:${conn.port}`}
                      primaryTypographyProps={{ fontSize: 13, fontWeight: 500 }}
                      secondaryTypographyProps={{ fontSize: 11 }}
                    />
                  </TreeListItem>

                  {/* Database Level */}
                  <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                    {dbInfo && dbInfo.tables && dbInfo.tables.length > 0 ? (
                      <>
                        {/* Tables Folder */}
                        <TreeListItem
                          depth={1}
                          onClick={() => toggleDatabase(conn.database)}
                        >
                          <ListItemIcon sx={{ minWidth: 24 }}>
                            {expandedDatabases[conn.database] ? (
                              <ExpandMoreIcon fontSize="small" sx={{ fontSize: 16 }} />
                            ) : (
                              <ChevronRightIcon fontSize="small" sx={{ fontSize: 16 }} />
                            )}
                          </ListItemIcon>
                          <ListItemIcon sx={{ minWidth: 28 }}>
                            <FolderIcon fontSize="small" sx={{ fontSize: 16, color: '#dcdcaa' }} />
                          </ListItemIcon>
                          <ListItemText
                            primary={`Tables (${dbInfo.tables.length})`}
                            primaryTypographyProps={{ fontSize: 13 }}
                          />
                        </TreeListItem>

                        {/* Tables List */}
                        <Collapse in={expandedDatabases[conn.database]} timeout="auto" unmountOnExit>
                          <List dense disablePadding>
                            {dbInfo.tables.map((table) => (
                              <TreeListItem
                                key={table}
                                depth={2}
                                selected={selectedItem === `${conn.database}.${table}`}
                                onClick={() => handleSelectItem(`${conn.database}.${table}`)}
                              >
                                <ListItemIcon sx={{ minWidth: 28, ml: 3 }}>
                                  <TableIcon fontSize="small" sx={{ fontSize: 16, color: '#4ec9b0' }} />
                                </ListItemIcon>
                                <ListItemText
                                  primary={table}
                                  primaryTypographyProps={{ fontSize: 13 }}
                                />
                              </TreeListItem>
                            ))}
                          </List>
                        </Collapse>
                      </>
                    ) : (
                      <TreeListItem depth={1}>
                        <ListItemText
                          primary="No schema discovered"
                          secondary="Click to discover schema"
                          primaryTypographyProps={{ fontSize: 12, color: 'text.secondary' }}
                          secondaryTypographyProps={{ fontSize: 11 }}
                          sx={{ pl: 4 }}
                        />
                      </TreeListItem>
                    )}
                  </Collapse>
                </React.Fragment>
              );
            })
          )}
        </List>
      </Box>

      {/* Footer */}
      <Box sx={{ p: 1, borderTop: `1px solid ${theme => theme.palette.divider}` }}>
        <Typography variant="caption" sx={{ fontSize: 10, color: 'text.secondary', display: 'block', textAlign: 'center' }}>
          {Object.keys(connections).length} connection(s) • {Object.keys(databases).length} database(s)
        </Typography>
      </Box>
    </PanelContainer>
  );
};

export default DatabaseTreePanel;