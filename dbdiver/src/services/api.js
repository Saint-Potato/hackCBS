import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', error.response?.data || error.message);

    // Handle common error responses
    if (error.response?.status === 404) {
      throw new Error('Endpoint not found');
    } else if (error.response?.status === 500) {
      throw new Error('Server error occurred');
    } else if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }

    return Promise.reject(error);
  }
);

// API Service Class
class ApiService {
  
  // Health & System
  async healthCheck() {
    const response = await api.get('/api/health');
    return response.data;
  }

  async getSystemStats() {
    const response = await api.get('/api/stats');
    return response.data;
  }

  async getSupportedDatabaseTypes() {
    const response = await api.get('/api/database-types');
    return response.data;
  }

  // Database Connections
  async getConnections() {
    const response = await api.get('/api/connections');
    return response.data;
  }

  async connectDatabase(connectionData) {
    const response = await api.post('/api/connect', connectionData);
    return response.data;
  }

  async disconnectDatabase(dbType) {
    const response = await api.delete(`/api/disconnect/${dbType}`);
    return response.data;
  }

  async testConnection(connectionData) {
    const response = await api.post('/api/test-connection', connectionData);
    return response.data;
  }

  // Schema Management
  async discoverSchema(dbType) {
    const response = await api.post(`/api/discover-schema/${dbType}`);
    return response.data;
  }

  async getSchemasSummary(dbType) {
    const response = await api.get(`/api/schema-summary/${dbType}`);
    return response.data;
  }

  async searchSchema(query, database = null) {
    const response = await api.post('/api/search-schema', { query, database });
    return response.data;
  }

  // RAG System
  async getRagOverview() {
    const response = await api.get('/api/rag-overview');
    return response.data;
  }

  async resetRagCollection() {
    const response = await api.delete('/api/rag-reset');
    return response.data;
  }

  // Query Processing
  async askQuestion(query, database = null) {
    const response = await api.post('/api/query', { query, database });
    return response.data;
  }

  async executeSQL(sqlQuery, database) {
    const response = await api.post('/api/execute-sql', { 
      sql_query: sqlQuery, 
      database 
    });
    return response.data;
  }
}

export default new ApiService();