import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
  Grid,
  Container,
  Paper,
  Divider,
  Chip,
  Stack,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Add as AddIcon,
  CheckCircle as ConnectedIcon,
  Cancel as DisconnectIcon,
  Computer as ServerIcon,
} from '@mui/icons-material';
import { useApi } from '../contexts/ApiContext';

const DatabaseConnection = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const {
    connections,
    connectDatabase,
    disconnectDatabase,
    isConnecting,
    connectionError,
  } = useApi();

  const [formData, setFormData] = useState({
    db_type: 'mysql',
    host: 'localhost',
    port: 3306,
    username: 'root',
    password: '',
    database: '',
  });

  const dbTypes = [
    {
      value: 'mysql',
      label: 'MySQL',
      defaultPort: 3306,
      color: '#00758f',
      description: 'Popular open-source relational database'
    },
    {
      value: 'postgresql',
      label: 'PostgreSQL',
      defaultPort: 5432,
      color: '#336791',
      description: 'Advanced open-source relational database'
    },
    {
      value: 'mongodb',
      label: 'MongoDB',
      defaultPort: 27017,
      color: '#4db33d',
      description: 'Document-oriented NoSQL database'
    },
  ];

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: field === 'port' ? parseInt(value) || 0 : value,
    }));

    // Auto-set default port when database type changes
    if (field === 'db_type') {
      const dbType = dbTypes.find(db => db.value === value);
      setFormData(prev => ({
        ...prev,
        port: dbType?.defaultPort || 3306,
      }));
    }
  };

  const handleConnect = () => {
    connectDatabase(formData);
  };

  const handleDisconnect = (dbType) => {
    disconnectDatabase(dbType);
  };


  const selectedDbType = dbTypes.find(db => db.value === formData.db_type);

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Header Section */}
      <Box sx={{ mb: 4 }}>
        <Stack
          direction={isMobile ? 'column' : 'row'}
          spacing={2}
          alignItems={isMobile ? 'flex-start' : 'center'}
          justifyContent="space-between"
        >
          <Box>
            <Typography
              variant="h3"
              gutterBottom
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 2,
                fontSize: { xs: '2rem', md: '3rem' }
              }}
            >
              <StorageIcon sx={{ fontSize: 'inherit' }} />
              Database Connections
            </Typography>
            <Typography variant="body1" color="textSecondary">
              Connect to your MySQL, PostgreSQL, or MongoDB databases
            </Typography>
          </Box>

          <Chip
            icon={<ConnectedIcon />}
            label={`${Object.keys(connections).length} Active Connection${Object.keys(connections).length !== 1 ? 's' : ''}`}
            color={Object.keys(connections).length > 0 ? 'success' : 'default'}
            variant={Object.keys(connections).length > 0 ? 'filled' : 'outlined'}
            size="medium"
          />
        </Stack>
      </Box>

      <Grid container spacing={{ xs: 2, md: 3 }}>
        {/* Connection Form */}
        <Grid item xs={12} lg={6}>
          <Card
            elevation={3}
            sx={{
              height: 'fit-content',
              borderRadius: 2,
              '&:hover': {
                boxShadow: theme.shadows[8]
              }
            }}
          >
            <CardHeader
              avatar={
                <Box
                  sx={{
                    backgroundColor: selectedDbType?.color || theme.palette.primary.main,
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <AddIcon sx={{ color: 'white' }} />
                </Box>
              }
              title="Add New Connection"
              subheader={selectedDbType?.description}
              sx={{ pb: 1 }}
            />
            <Divider />
            <CardContent sx={{ p: { xs: 2, md: 3 } }}>
              <Stack spacing={3}>
                {/* Database Type Selection */}
                <FormControl fullWidth>
                  <InputLabel>Database Type</InputLabel>
                  <Select
                    value={formData.db_type}
                    label="Database Type"
                    onChange={handleChange('db_type')}
                  >
                    {dbTypes.map((db) => (
                      <MenuItem key={db.value} value={db.value}>
                        <Stack direction="row" spacing={2} alignItems="center">
                          <Box
                            sx={{
                              width: 12,
                              height: 12,
                              borderRadius: '50%',
                              backgroundColor: db.color,
                            }}
                          />
                          <Typography>{db.label}</Typography>
                          <Chip
                            label={`Port ${db.defaultPort}`}
                            size="small"
                            variant="outlined"
                          />
                        </Stack>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                {/* Connection Details */}
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={8}>
                    <TextField
                      label="Host"
                      value={formData.host}
                      onChange={handleChange('host')}
                      fullWidth
                      placeholder="localhost or IP address"
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      label="Port"
                      type="number"
                      value={formData.port}
                      onChange={handleChange('port')}
                      fullWidth
                    />
                  </Grid>
                </Grid>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Username"
                      value={formData.username}
                      onChange={handleChange('username')}
                      fullWidth
                      placeholder="Database username"
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      label="Password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange('password')}
                      fullWidth
                      placeholder="Database password"
                    />
                  </Grid>
                </Grid>

                <TextField
                  label="Database Name"
                  value={formData.database}
                  onChange={handleChange('database')}
                  fullWidth
                  placeholder="Name of the database to connect to"
                  required
                />

                {/* Error and Test Results */}
                {connectionError && (
                  <Alert severity="error" sx={{ borderRadius: 2 }}>
                    <strong>Connection Error:</strong> {connectionError.message || 'Connection failed'}
                  </Alert>
                )}


                {/* Action Buttons */}
                <Stack
                  direction={isMobile ? 'column' : 'row'}
                  spacing={2}
                >


                  <Button
                    variant="contained"
                    onClick={handleConnect}
                    disabled={isConnecting || !formData.database}
                    sx={{
                      flex: { xs: 'none', sm: 1 },
                      minHeight: 42,
                      fontWeight: 600
                    }}
                  >
                    {isConnecting ? (
                      <>
                        <CircularProgress size={20} sx={{ mr: 1 }} />
                        Connecting...
                      </>
                    ) : (
                      'Connect Database'
                    )}
                  </Button>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Connections */}
        <Grid item xs={12} lg={6}>
          <Card
            elevation={3}
            sx={{
              borderRadius: 2,
              '&:hover': {
                boxShadow: theme.shadows[8]
              }
            }}
          >
            <CardHeader
              avatar={
                <Box
                  sx={{
                    backgroundColor: theme.palette.success.main,
                    borderRadius: '50%',
                    p: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <ServerIcon sx={{ color: 'white' }} />
                </Box>
              }
              title="Active Connections"
              subheader={`${Object.keys(connections).length} database${Object.keys(connections).length !== 1 ? 's' : ''} connected`}
              sx={{ pb: 1 }}
            />
            <Divider />
            <CardContent sx={{ p: { xs: 2, md: 3 } }}>
              {Object.keys(connections).length === 0 ? (
                <Paper
                  variant="outlined"
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    borderStyle: 'dashed',
                    borderColor: 'grey.300',
                    backgroundColor: 'grey.50',
                    borderRadius: 2,
                  }}
                >
                  <StorageIcon
                    sx={{
                      fontSize: 48,
                      color: 'grey.400',
                      mb: 2
                    }}
                  />
                  <Typography variant="h6" color="textSecondary" gutterBottom>
                    No Active Connections
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Connect to a database to get started with data analysis
                  </Typography>
                </Paper>
              ) : (
                <Stack spacing={2}>
                  {Object.entries(connections).map(([dbType, conn]) => {
                    const dbTypeInfo = dbTypes.find(db => db.value === conn.type);

                    return (
                      <Paper
                        key={dbType}
                        elevation={2}
                        sx={{
                          p: 2,
                          borderRadius: 2,
                          border: `2px solid ${dbTypeInfo?.color || theme.palette.primary.main}20`,
                          '&:hover': {
                            boxShadow: theme.shadows[4],
                            transform: 'translateY(-1px)',
                          },
                          transition: 'all 0.2s ease-in-out',
                        }}
                      >
                        <Stack
                          direction={{ xs: 'column', sm: 'row' }}
                          spacing={2}
                          alignItems={{ xs: 'stretch', sm: 'center' }}
                          justifyContent="space-between"
                        >
                          <Box sx={{ flex: 1 }}>
                            <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 1 }}>
                              <Box
                                sx={{
                                  width: 12,
                                  height: 12,
                                  borderRadius: '50%',
                                  backgroundColor: dbTypeInfo?.color || theme.palette.primary.main,
                                }}
                              />
                              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                                {dbTypeInfo?.label || conn.type.toUpperCase()}
                              </Typography>
                              <Chip
                                icon={<ConnectedIcon />}
                                label="Connected"
                                size="small"
                                color="success"
                                variant="outlined"
                              />
                            </Stack>

                            <Typography
                              variant="body2"
                              color="textSecondary"
                              sx={{ fontFamily: 'monospace' }}
                            >
                              📍 {conn.host}:{conn.port}
                            </Typography>
                            <Typography
                              variant="body2"
                              color="textSecondary"
                              sx={{ fontFamily: 'monospace' }}
                            >
                              🗄️ {conn.database}
                            </Typography>
                          </Box>

                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            startIcon={<DisconnectIcon />}
                            onClick={() => handleDisconnect(dbType)}
                            sx={{
                              minWidth: { xs: '100%', sm: '120px' },
                              fontWeight: 500
                            }}
                          >
                            Disconnect
                          </Button>
                        </Stack>
                      </Paper>
                    );
                  })}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default DatabaseConnection;