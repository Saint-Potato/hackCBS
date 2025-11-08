import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../services/api';

const ApiContext = createContext();

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

export const ApiProvider = ({ children }) => {
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [schemaDiscovered, setSchemaDiscovered] = useState(false);
  const queryClient = useQueryClient();

  // Health check query
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: apiService.healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 1,
  });

  // Get connections
  const { data: connections, isLoading: connectionsLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: apiService.getConnections,
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Get RAG overview
  const { data: ragOverview, isLoading: ragLoading } = useQuery({
    queryKey: ['rag-overview'],
    queryFn: apiService.getRagOverview,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  // Connect database function
  const connectDatabase = async (connectionData) => {
    setIsConnecting(true);
    setConnectionError(null);

    try {
      console.log('🔗 Connecting to database...');

      // Step 1: Connect to database
      const connectionResult = await apiService.connectDatabase(connectionData);

      if (connectionResult.success) {
        console.log('✅ Database connected successfully');

        // Step 2: AUTO-DISCOVER SCHEMA
        console.log('🔍 Auto-discovering schema...');

        try {
          const schemaResult = await apiService.discoverSchema(connectionData.db_type);

          if (schemaResult.success) {
            console.log('✅ Schema discovered and stored in RAG system');
            console.log('Schema result:', schemaResult);

            // Optionally store schema discovery status
            setSchemaDiscovered(true);
          } else {
            console.warn('⚠️ Schema discovery failed:', schemaResult.message);
            // Still proceed with connection, but warn user
          }

        } catch (schemaError) {
          console.error('❌ Schema discovery error:', schemaError);
          // Don't fail the whole connection for schema issues
        }

        // Update connections state
        queryClient.invalidateQueries(['connections']);

        return connectionResult;
      } else {
        throw new Error(connectionResult.message || 'Connection failed');
      }

    } catch (error) {
      console.error('❌ Database connection error:', error);
      setConnectionError(error);
      throw error;
    } finally {
      setIsConnecting(false);
    }
  };

  // Disconnect database mutation
  const disconnectMutation = useMutation({
    mutationFn: apiService.disconnectDatabase,
    onSuccess: () => {
      queryClient.invalidateQueries(['connections']);
      setConnectionStatus('disconnected');
    }
  });

  // Discover schema mutation
  const discoverSchemaMutation = useMutation({
    mutationFn: apiService.discoverSchema,
    onSuccess: () => {
      queryClient.invalidateQueries(['rag-overview']);
    }
  });

  // Ask question mutation
  const askQuestionMutation = useMutation({
    mutationFn: ({ query, database }) => apiService.askQuestion(query, database),
  });

  // Execute SQL mutation
  const executeSQLMutation = useMutation({
    mutationFn: ({ sqlQuery, database }) => apiService.executeSQL(sqlQuery, database),
  });

  const value = {
    // Data
    healthData,
    connections: connections?.data?.connections || {},
    ragOverview: ragOverview?.data || {},
    selectedDatabase,
    connectionStatus,

    // Loading states
    connectionsLoading,
    ragLoading,
    isConnecting,

    // Actions
    setSelectedDatabase,
    connectDatabase,
    disconnectDatabase: disconnectMutation.mutate,
    discoverSchema: discoverSchemaMutation.mutate,
    askQuestion: askQuestionMutation.mutate,
    executeSQL: executeSQLMutation.mutate,

    // Mutation states
    isDisconnecting: disconnectMutation.isPending,
    isDiscoveringSchema: discoverSchemaMutation.isPending,
    isAskingQuestion: askQuestionMutation.isPending,
    isExecutingSQL: executeSQLMutation.isPending,

    // Results
    questionResult: askQuestionMutation.data,
    sqlResult: executeSQLMutation.data,

    // Errors
    connectionError,
    questionError: askQuestionMutation.error,
    sqlError: executeSQLMutation.error,

    // Schema discovery status
    schemaDiscovered,
  };

  return (
    <ApiContext.Provider value={value}>
      {children}
    </ApiContext.Provider>
  );
};