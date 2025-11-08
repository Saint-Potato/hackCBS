import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Button,
  Container,
  Paper,
  Stack,
  Chip,
  Avatar,
  useTheme,
  useMediaQuery,
  IconButton,
  Divider,
} from '@mui/material';
import {
  Storage as StorageIcon,
  Schema as SchemaIcon,
  Psychology as BrainIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingIcon,
  Speed as SpeedIcon,
  ArrowForward as ArrowIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useApi } from '../contexts/ApiContext';

const Dashboard = ({ onViewChange }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { connections, ragOverview, healthData } = useApi();

  const connectionCount = Object.keys(connections).length;
  const documentCount = ragOverview.total_documents || 0;
  const databaseCount = Object.keys(ragOverview.databases || {}).length;

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'warning': return 'warning';
      case 'error': return 'error';
      default: return 'info';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckIcon />;
      case 'warning': return <WarningIcon />;
      case 'error': return <ErrorIcon />;
      default: return <CheckIcon />;
    }
  };

  const StatCard = ({ title, value, subtitle, icon, color, action }) => (
    <Card
      elevation={3}
      sx={{
        borderRadius: 3,
        height: '100%',
        background: `linear-gradient(135deg, ${theme.palette[color].main}15, ${theme.palette[color].main}05)`,
        border: `1px solid ${theme.palette[color].main}20`,
        '&:hover': {
          boxShadow: theme.shadows[8],
          transform: 'translateY(-2px)',
        },
        transition: 'all 0.3s ease-in-out',
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Stack direction="row" spacing={2} alignItems="flex-start">
          <Avatar
            sx={{
              backgroundColor: theme.palette[color].main,
              width: 56,
              height: 56,
            }}
          >
            {icon}
          </Avatar>

          <Box sx={{ flex: 1 }}>
            <Typography variant="h3" sx={{ fontWeight: 700, mb: 0.5 }}>
              {value}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
              {title}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {subtitle}
            </Typography>

            {action && (
              <Button
                variant="outlined"
                size="small"
                onClick={action.onClick}
                sx={{ mt: 2 }}
                endIcon={<ArrowIcon />}
              >
                {action.label}
              </Button>
            )}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="xl" sx={{ py: { xs: 2, md: 4 } }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Stack
          direction={isMobile ? 'column' : 'row'}
          spacing={2}
          alignItems={isMobile ? 'flex-start' : 'center'}
          justifyContent="space-between"
        >
          <Box>
            <Typography
              variant="h2"
              gutterBottom
              sx={{
                fontWeight: 800,
                fontSize: { xs: '2.5rem', md: '3.75rem' },
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              🚀 Dashboard
            </Typography>
            <Typography variant="h6" color="textSecondary">
              AI-Driven Database RAG & Analytics Platform
            </Typography>
          </Box>

          <Stack direction="row" spacing={1}>
            <IconButton
              onClick={() => window.location.reload()}
              sx={{
                backgroundColor: theme.palette.action.hover,
                '&:hover': { backgroundColor: theme.palette.action.selected }
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Stack>
        </Stack>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={{ xs: 2, md: 3 }} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="System Health"
            value={healthData?.status === 'healthy' ? '✅' : '❌'}
            subtitle="Backend API Status"
            icon={getStatusIcon(healthData?.status)}
            color={getStatusColor(healthData?.status)}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Connections"
            value={connectionCount}
            subtitle="Active database connections"
            icon={<StorageIcon />}
            color="primary"
            action={connectionCount === 0 ? {
              label: "Connect Now",
              onClick: () => onViewChange('databases')
            } : null}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="RAG Documents"
            value={documentCount}
            subtitle="Schema documents indexed"
            icon={<BrainIcon />}
            color="secondary"
          />
        </Grid>
      </Grid>

      <Grid container spacing={{ xs: 2, md: 3 }}>
        {/* Quick Actions */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={3}
            sx={{
              borderRadius: 3,
              height: '100%',
              '&:hover': { boxShadow: theme.shadows[8] }
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                🚀 Quick Actions
              </Typography>

              <Stack spacing={2}>
                {[
                  {
                    icon: <StorageIcon />,
                    primary: "Connect to Database",
                    secondary: connectionCount > 0 ?
                      `${connectionCount} database${connectionCount !== 1 ? 's' : ''} connected` :
                      "Connect to MySQL, PostgreSQL, or MongoDB",
                    action: () => onViewChange('databases'),
                    disabled: false,
                    color: connectionCount > 0 ? 'success' : 'primary'
                  },
                  {
                    icon: <SchemaIcon />,
                    primary: "Discover Schema",
                    secondary: documentCount > 0 ?
                      `${documentCount} documents indexed` :
                      "Index your database schema for RAG",
                    action: null,
                    disabled: connectionCount === 0,
                    color: documentCount > 0 ? 'success' : 'action'
                  },
                  {
                    icon: <BrainIcon />,
                    primary: "Ask Questions",
                    secondary: documentCount > 0 ?
                      "Query your data with natural language" :
                      "Requires schema discovery first",
                    action: () => onViewChange('chat'),
                    disabled: documentCount === 0,
                    color: documentCount > 0 ? 'primary' : 'action'
                  }
                ].map((item, index) => (
                  <Paper
                    key={index}
                    elevation={1}
                    sx={{
                      p: 2,
                      borderRadius: 2,
                      cursor: item.action ? 'pointer' : 'default',
                      opacity: item.disabled ? 0.6 : 1,
                      '&:hover': item.action && !item.disabled ? {
                        boxShadow: theme.shadows[4],
                        transform: 'translateY(-1px)',
                      } : {},
                      transition: 'all 0.2s ease-in-out',
                    }}
                    onClick={item.action && !item.disabled ? item.action : undefined}
                  >
                    <Stack direction="row" spacing={2} alignItems="center">
                      <Avatar
                        sx={{
                          backgroundColor: theme.palette[item.color].main + '20',
                          color: theme.palette[item.color].main,
                        }}
                      >
                        {item.icon}
                      </Avatar>
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {item.primary}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {item.secondary}
                        </Typography>
                      </Box>
                      {item.action && !item.disabled && <ArrowIcon />}
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        {/* Database Overview */}
        <Grid item xs={12} md={6}>
          <Card
            elevation={3}
            sx={{
              borderRadius: 3,
              height: '100%',
              '&:hover': { boxShadow: theme.shadows[8] }
            }}
          >
            <CardContent sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                📊 Database Overview
              </Typography>

              {databaseCount === 0 ? (
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
                  <SchemaIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                  <Typography variant="h6" color="textSecondary" gutterBottom>
                    No Databases Indexed
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Connect to a database and discover its schema to get started
                  </Typography>
                </Paper>
              ) : (
                <Stack spacing={2}>
                  {Object.entries(ragOverview.databases || {}).map(([dbName, dbInfo]) => (
                    <Paper
                      key={dbName}
                      elevation={1}
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        border: `1px solid ${theme.palette.primary.main}20`,
                      }}
                    >
                      <Stack direction="row" spacing={2} alignItems="center">
                        <Avatar
                          sx={{
                            backgroundColor: theme.palette.info.main,
                            width: 40,
                            height: 40,
                          }}
                        >
                          <StorageIcon />
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {dbName}
                          </Typography>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <Chip
                              label={dbInfo.type}
                              size="small"
                              color="primary"
                              variant="outlined"
                            />
                            <Typography variant="body2" color="textSecondary">
                              {dbInfo.tables?.length || 0} tables
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              •
                            </Typography>
                            <Typography variant="body2" color="textSecondary">
                              {dbInfo.document_count} docs
                            </Typography>
                          </Stack>
                        </Box>
                      </Stack>
                    </Paper>
                  ))}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Getting Started Guide */}
        {connectionCount === 0 && (
          <Grid item xs={12}>
            <Card
              elevation={3}
              sx={{
                borderRadius: 3,
                background: `linear-gradient(135deg, ${theme.palette.primary.main}10, ${theme.palette.secondary.main}10)`,
                border: `1px solid ${theme.palette.primary.main}20`,
              }}
            >
              <CardContent sx={{ p: 4 }}>
                <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
                  🎯 Welcome to DB RAG Analytics!
                </Typography>
                <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
                  Get started with AI-powered database analytics in just a few simple steps:
                </Typography>

                <Grid container spacing={3} sx={{ mt: 2 }}>
                  {[
                    {
                      step: "1",
                      title: "Connect to your database",
                      description: "Add your MySQL, PostgreSQL, or MongoDB connection details",
                      color: theme.palette.primary.main,
                    },
                    {
                      step: "2",
                      title: "Discover your schema",
                      description: "Let the system analyze and index your database structure",
                      color: theme.palette.secondary.main,
                    },
                    {
                      step: "3",
                      title: "Ask questions",
                      description: "Use natural language to query your data and understand your schema",
                      color: theme.palette.success.main,
                    },
                  ].map((item) => (
                    <Grid item xs={12} md={4} key={item.step}>
                      <Paper
                        elevation={2}
                        sx={{
                          p: 3,
                          borderRadius: 2,
                          textAlign: 'center',
                          border: `2px solid ${item.color}20`,
                        }}
                      >
                        <Avatar
                          sx={{
                            backgroundColor: item.color,
                            width: 48,
                            height: 48,
                            mx: 'auto',
                            mb: 2,
                            fontSize: '1.5rem',
                            fontWeight: 700,
                          }}
                        >
                          {item.step}
                        </Avatar>
                        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                          {item.title}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                          {item.description}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>

                <Box sx={{ textAlign: 'center', mt: 4 }}>
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => onViewChange('databases')}
                    sx={{
                      px: 4,
                      py: 1.5,
                      fontSize: '1.1rem',
                      fontWeight: 600,
                      borderRadius: 2,
                    }}
                    endIcon={<ArrowIcon />}
                  >
                    Get Started Now
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default Dashboard;