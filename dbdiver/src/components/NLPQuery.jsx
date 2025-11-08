import React, { useState, useEffect } from 'react';
import {
  Box,
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
  Alert,
  CircularProgress,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import {
  Psychology as BrainIcon,
  Send as SendIcon,
  ExpandMore as ExpandMoreIcon,
  Code as CodeIcon,
  PlayArrow as PlayIcon,
  TableChart as TableIcon,
  Schema as SchemaIcon,
} from '@mui/icons-material';
import { useApi } from '../contexts/ApiContext';

const NLPQuery = () => {
  const {
    connections,
    ragOverview,
    selectedDatabase,
    setSelectedDatabase,
    askQuestion,
    executeSQL,
    isAskingQuestion,
    isExecutingSQL,
    questionResult,
    sqlResult,
    questionError,
    sqlError,
  } = useApi();

  const [query, setQuery] = useState('');
  const [generatedSQL, setGeneratedSQL] = useState('');
  const [showSQLExecution, setShowSQLExecution] = useState(false);

  const databases = ragOverview.databases || {};
  const hasConnections = Object.keys(connections).length > 0;
  const hasSchemas = Object.keys(databases).length > 0;

  // Example queries
  const exampleQueries = {
    schema: [
      'How many tables are there?',
      'What tables store user information?',
      'Show me all foreign key relationships',
      'Which columns can store null values?',
    ],
    data: [
      'How many students are there?',
      'Show me the top 5 users by registration date',
      'What is the average age of students?',
      'Find all users with gmail addresses',
    ],
  };

  // Auto-select first available database
  useEffect(() => {
    if (!selectedDatabase && Object.keys(databases).length > 0) {
      setSelectedDatabase(Object.keys(databases)[0]);
    }
  }, [databases, selectedDatabase, setSelectedDatabase]);

  // Handle question result
  useEffect(() => {
    if (questionResult?.data) {
      const result = questionResult.data;
      if (result.type === 'data' && result.sql_query) {
        setGeneratedSQL(result.sql_query);
        setShowSQLExecution(true);
      }
    }
  }, [questionResult]);

  const handleSubmitQuery = () => {
    if (!query.trim()) return;
    askQuestion({ query: query.trim(), database: selectedDatabase });
  };

  const handleExecuteSQL = () => {
    if (!generatedSQL.trim() || !selectedDatabase) return;
    executeSQL({ sqlQuery: generatedSQL, database: selectedDatabase });
  };

  const renderSchemaResults = (results) => {
    if (!results || results.length === 0) return null;

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SchemaIcon />
          Schema Information
        </Typography>
        {results.map((result, index) => (
          <Card key={index} variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Chip
                  label={result.metadata?.type || 'Schema'}
                  size="small"
                  color="primary"
                />
                <Chip
                  label={`${(result.similarity_score * 100).toFixed(1)}% match`}
                  size="small"
                  color={result.relevance === 'high' ? 'success' : result.relevance === 'medium' ? 'warning' : 'default'}
                />
              </Box>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'grey.100', p: 1, borderRadius: 1 }}>
                {result.content}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
    );
  };

  const renderDataResults = (results) => {
    if (!results || results.length === 0) return null;

    return (
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {Object.keys(results[0]).map((column) => (
                <TableCell key={column} sx={{ fontWeight: 'bold' }}>
                  {column}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {results.slice(0, 10).map((row, index) => (
              <TableRow key={index}>
                {Object.values(row).map((value, cellIndex) => (
                  <TableCell key={cellIndex}>
                    {value !== null ? String(value) : 'NULL'}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        {results.length > 10 && (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              ... and {results.length - 10} more rows
            </Typography>
          </Box>
        )}
      </TableContainer>
    );
  };

  if (!hasConnections) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="warning" sx={{ mb: 2 }}>
          No database connections found. Please connect to a database first.
        </Alert>
        <Button variant="contained" onClick={() => window.location.href = '/connections'}>
          Go to Connections
        </Button>
      </Box>
    );
  }

  if (!hasSchemas) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Alert severity="info" sx={{ mb: 2 }}>
          No database schemas found. Please discover and store schemas first.
        </Alert>
        <Typography variant="body2" color="textSecondary">
          Use the CLI or add schema discovery to the UI to get started.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BrainIcon />
        Natural Language Query Interface
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardHeader title="Ask Questions About Your Data" />
        <CardContent>
          {/* Database Selection */}
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Select Database</InputLabel>
            <Select
              value={selectedDatabase || ''}
              label="Select Database"
              onChange={(e) => setSelectedDatabase(e.target.value)}
            >
              {Object.keys(databases).map((dbName) => (
                <MenuItem key={dbName} value={dbName}>
                  {dbName} ({databases[dbName].type})
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Query Input */}
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Ask a question about your database..."
            placeholder="Examples: 'How many users are there?' or 'Show me all tables with foreign keys'"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            sx={{ mb: 2 }}
          />

          {/* Submit Button */}
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={handleSubmitQuery}
            disabled={!query.trim() || !selectedDatabase || isAskingQuestion}
            sx={{ mb: 2 }}
          >
            {isAskingQuestion ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                Analyzing...
              </>
            ) : (
              'Ask Question'
            )}
          </Button>

          {/* Example Questions */}
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>💡 Example Questions</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    📊 Schema Questions:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {exampleQueries.schema.map((example, index) => (
                      <Chip
                        key={index}
                        label={example}
                        variant="outlined"
                        clickable
                        onClick={() => setQuery(example)}
                        size="small"
                      />
                    ))}
                  </Box>
                </Box>
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    🔍 Data Questions:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {exampleQueries.data.map((example, index) => (
                      <Chip
                        key={index}
                        label={example}
                        variant="outlined"
                        clickable
                        onClick={() => setQuery(example)}
                        size="small"
                      />
                    ))}
                  </Box>
                </Box>
              </Box>
            </AccordionDetails>
          </Accordion>
        </CardContent>
      </Card>

      {/* Error Display */}
      {(questionError || sqlError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {questionError?.message || sqlError?.message || 'An error occurred'}
        </Alert>
      )}

      {/* Question Results */}
      {questionResult?.data && (
        <Card sx={{ mb: 3 }}>
          <CardHeader title="Analysis Result" />
          <CardContent>
            <Box sx={{ mb: 2 }}>
              <Chip
                label={questionResult.data.type === 'schema' ? 'Schema Query' : 'Data Query'}
                color={questionResult.data.type === 'schema' ? 'primary' : 'secondary'}
              />
            </Box>

            {questionResult.data.type === 'schema' ? (
              renderSchemaResults(questionResult.data.results)
            ) : (
              <Box>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CodeIcon />
                  Generated SQL
                </Typography>
                <Box sx={{ bgcolor: 'grey.900', color: 'white', p: 2, borderRadius: 1, mb: 2 }}>
                  <code>{questionResult.data.sql_query}</code>
                </Box>
                
                {questionResult.data.explanation && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <strong>Explanation:</strong> {questionResult.data.explanation}
                  </Alert>
                )}

                {questionResult.data.warnings && questionResult.data.warnings.length > 0 && (
                  <Alert severity="warning" sx={{ mb: 2 }}>
                    <strong>Warnings:</strong>
                    <ul>
                      {questionResult.data.warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </Alert>
                )}

                <Button
                  variant="contained"
                  startIcon={<PlayIcon />}
                  onClick={handleExecuteSQL}
                  disabled={isExecutingSQL}
                  color="success"
                >
                  {isExecutingSQL ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Executing...
                    </>
                  ) : (
                    'Execute SQL'
                  )}
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* SQL Execution Results */}
      {sqlResult?.data && (
        <Card>
          <CardHeader
            title={
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TableIcon />
                Query Results ({sqlResult.data.count} rows)
              </Box>
            }
          />
          <CardContent>
            {renderDataResults(sqlResult.data.results)}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default NLPQuery;