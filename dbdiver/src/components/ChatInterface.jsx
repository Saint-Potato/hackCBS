import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Button,
  CircularProgress,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { api } from '../services/apiClient.js'; // Add .js extension

const MessageBubble = ({ role, children }) => {
  const isUser = role === 'user';
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 1.5,
        maxWidth: '85%',
        marginLeft: isUser ? 'auto' : '0',
      }}
    >
      <Paper
        elevation={0}
        sx={{
          width: '100%',
          p: 1.5,
          borderRadius: 2,
          bgcolor: isUser ? 'rgba(255,255,255,0.06)' : 'rgba(255,255,255,0.03)',
          border: '1px solid',
          borderColor: 'rgba(255,255,255,0.08)',
        }}
      >
        {children}
      </Paper>
    </Box>
  );
};

const CodeBlock = ({ code, language = 'sql' }) => {
  const onCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch {}
  };
  return (
    <Box sx={{ position: 'relative', mt: 1, mb: 1 }}>
      <Paper
        variant="outlined"
        sx={{
          bgcolor: 'rgba(0,0,0,0.4)',
          p: 1.5,
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
          fontSize: 13,
          overflowX: 'auto',
        }}
      >
        <Typography
          component="pre"
          sx={{ m: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}
        >
          {code}
        </Typography>
      </Paper>
      <IconButton
        size="small"
        onClick={onCopy}
        sx={{ position: 'absolute', top: 8, right: 8 }}
        aria-label="Copy code"
      >
        <ContentCopyIcon fontSize="inherit" />
      </IconButton>
    </Box>
  );
};

const ResultTable = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return (
      <Typography variant="body2" sx={{ opacity: 0.8 }}>
        No results.
      </Typography>
    );
  }

  // Normalize rows to array of objects
  const norm = rows.map((r) => {
    if (Array.isArray(r)) {
      // convert tuple/array rows into object with generic keys
      const obj = {};
      r.forEach((v, idx) => (obj[`col_${idx + 1}`] = v));
      return obj;
    }
    if (r && typeof r === 'object') return r;
    return { value: r };
  });

  const columns = Object.keys(norm[0] || {});
  return (
    <Box sx={{ mt: 1, overflowX: 'auto' }}>
      <Box
        component="table"
        sx={{
          borderCollapse: 'collapse',
          width: '100%',
          minWidth: 420,
          '& th, & td': {
            border: '1px solid rgba(255,255,255,0.12)',
            p: 0.75,
            textAlign: 'left',
            fontSize: 13,
          },
          '& th': {
            bgcolor: 'rgba(255,255,255,0.04)',
            fontWeight: 600,
          },
        }}
      >
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {norm.slice(0, 50).map((row, i) => (
            <tr key={i}>
              {columns.map((c) => (
                <td key={c}>{String(row[c] ?? '')}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </Box>
      {norm.length > 50 && (
        <Typography variant="caption" sx={{ opacity: 0.7 }}>
          Showing first 50 rows of {norm.length}.
        </Typography>
      )}
    </Box>
  );
};

const ChatMessage = ({ message }) => {
  const { role, content, sql, sqlResults, explanation, warnings, assumptions } = message;
  
  // For assistant messages that have SQL or results
  if (role === 'assistant' && (sql || sqlResults)) {
    return (
      <MessageBubble role={role}>
        {/* Natural language response first */}
        <Typography variant="body1" sx={{ mb: 2, color: '#fff' }}>
          {content}
        </Typography>

        {/* Results table in accordion */}
        <Accordion
          defaultExpanded={false}
          sx={{
            bgcolor: 'transparent',
            '&:before': { display: 'none' },
            boxShadow: 'none',
          }}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              p: 0,
              minHeight: 36,
              '& .MuiAccordionSummary-content': { margin: 0 }
            }}
          >
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              View Details
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ p: 0, pt: 1 }}>
            {sqlResults && <ResultTable rows={sqlResults} />}
          </AccordionDetails>
        {/* </Accordion> */}

        {/* Query details in separate accordion */}
        {/* <Accordion */}
          {/* sx={{
            bgcolor: 'transparent',
            '&:before': { display: 'none' },
            boxShadow: 'none',
            mt: 1
          }}
        > */}
          {/* <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            sx={{
              p: 0,
              minHeight: 36,
              '& .MuiAccordionSummary-content': { margin: 0 }
            }}
          >
            <Typography variant="body2" sx={{ color: 'text.secondary' }}>
              View Query Details
            </Typography>
          </AccordionSummary> */}
          <AccordionDetails sx={{ p: 0, pt: 1 }}>
            {sql && (
              <>
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                  SQL Query
                </Typography>
                <CodeBlock code={sql} />
              </>
            )}
            {explanation && (
              <>
                <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>
                  Explanation
                </Typography>
                <Typography variant="body2">{explanation}</Typography>
              </>
            )}
            {warnings?.length > 0 && (
              <>
                <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>
                  Warnings
                </Typography>
                <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                  {warnings.map((w, i) => (
                    <li key={i}>
                      <Typography variant="body2">{w}</Typography>
                    </li>
                  ))}
                </ul>
              </>
            )}
            {assumptions?.length > 0 && (
              <>
                <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>
                  Assumptions
                </Typography>
                <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                  {assumptions.map((a, i) => (
                    <li key={i}>
                      <Typography variant="body2">{a}</Typography>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </AccordionDetails>
        </Accordion>
      </MessageBubble>
    );
  }

  // Simple text message for user or other assistant messages
  return (
    <MessageBubble role={role}>
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
        {content}
      </Typography>
    </MessageBubble>
  );
};

const ChatInterface = () => {
  const [messages, setMessages] = useState(() => {
    // Restore last session
    try {
      const raw = localStorage.getItem('dbdiver_chat');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [executingSqlId, setExecutingSqlId] = useState(null);
  const [databases, setDatabases] = useState([]); // ['db1', 'db2']
  const [selectedDb, setSelectedDb] = useState(() => localStorage.getItem('dbdiver_selected_db') || '');
  const [loadingBootstrap, setLoadingBootstrap] = useState(true);

  const scrollRef = useRef(null);

  useEffect(() => {
    // bootstrap RAG overview to populate database list
    const boot = async () => {
      try {
        const overview = await api.getRagOverview();
        const dbNames = Object.keys(overview?.data?.databases || {});
        setDatabases(dbNames);
        if (!selectedDb && dbNames.length > 0) {
          setSelectedDb(dbNames[0]);
        }
      } catch {
        // ignore
      } finally {
        setLoadingBootstrap(false);
      }
    };
    boot();
  }, []);

  useEffect(() => {
    localStorage.setItem('dbdiver_selected_db', selectedDb || '');
  }, [selectedDb]);

  useEffect(() => {
    localStorage.setItem('dbdiver_chat', JSON.stringify(messages));
    // scroll to bottom when messages change
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const canSend = useMemo(() => input.trim().length > 0 && !sending, [input, sending]);

  const pushMessage = (msg) => setMessages((prev) => [...prev, { id: crypto.randomUUID(), ...msg }]);

  const handleSubmit = async () => {
    if (!canSend) return;
    const text = input.trim();
    setInput('');
    pushMessage({ role: 'user', content: text });

    setSending(true);
    try {
      const payload = { query: text };
      if (selectedDb) payload.database = selectedDb;

      const res = await api.askQuery(payload);

      if (!res?.success) {
        pushMessage({
          role: 'assistant',
          content: res?.message || 'Request failed.',
        });
        return;
      }

      const data = res.data || {};
      if (data.type === 'schema') {
        // For schema questions, format response directly from the query results
        const schemaResponse = renderSchemaSummary(text, selectedDb || data.database, data.results);
        pushMessage({
          role: 'assistant',
          content: schemaResponse,
        });
      } else if (data.type === 'data') {
        try {
          // Try executing SQL if provided
          const sqlRes = await api.executeSql({
            sql_query: data.sql_query,
            database: selectedDb || data.database,
          });

          // Process results through Gemini
          const processedRes = await api.processQueryResults({
            query: text,
            results: sqlRes.data?.results || [],
            sql: data.sql_query
          });

          pushMessage({
            role: 'assistant',
            content: processedRes.data?.natural_response || data.explanation || 'Here are your results:',
            sql: data.sql_query,
            sqlResults: sqlRes.data?.results || [],
            explanation: data.explanation,
            warnings: data.warnings || [],
            assumptions: data.assumptions || [],
          });
        } catch (sqlError) {
          // If SQL execution fails but we have metadata/explanation, use that
          pushMessage({
            role: 'assistant',
            content: data.explanation || 'Based on the database structure:',
            sql: data.sql_query,
            warnings: data.warnings || [],
            assumptions: data.assumptions || [],
          });
        }
      }
    } catch (e) {
      pushMessage({
        role: 'assistant',
        content: `Error: ${e?.message || 'Something went wrong.'}`,
      });
    } finally {
      setSending(false);
    }
  };

  const handleExecuteSql = async (msgId, sql, database) => {
    setExecutingSqlId(msgId);
    try {
      const res = await api.executeSql({ sql_query: sql, database });
      if (!res?.success) {
        pushMessage({
          role: 'assistant',
          content: res?.message || 'Failed to execute SQL.',
        });
        return;
      }

      pushMessage({
        role: 'assistant',
        content: `Query executed successfully.`,
        sqlResults: res.data?.results || [],
        sqlQuery: res.data?.sql_query || sql,
        count: res.data?.count,
      });
    } catch (e) {
      pushMessage({
        role: 'assistant',
        content: `Execution error: ${e?.message || 'Unknown error.'}`,
      });
    } finally {
      setExecutingSqlId(null);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '100%' }}>
      {/* Header: database selector */}
      <Box
        sx={{
          position: 'sticky',
          top: 0,
          zIndex: 1,
          p: 1,
          borderBottom: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.default',
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel id="db-label">Database</InputLabel>
          <Select
            labelId="db-label"
            label="Database"
            value={selectedDb}
            onChange={(e) => setSelectedDb(e.target.value)}
            disabled={loadingBootstrap || databases.length === 0}
          >
            {databases.map((db) => (
              <MenuItem key={db} value={db}>
                {db}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Typography variant="body2" sx={{ opacity: 0.7 }}>
          Ask about schema or data. Press Enter to send, Shift+Enter for new line.
        </Typography>
      </Box>

      {/* Messages */}
      <Box
        ref={scrollRef}
        sx={{
          flex: 1,
          overflowY: 'auto',
          p: 2,
          pt: 1.5,
        }}
      >
        {messages.length === 0 && (
          <Paper
            variant="outlined"
            sx={{
              p: 2,
              borderStyle: 'dashed',
              bgcolor: 'transparent',
              mb: 2,
            }}
          >
            <Typography variant="body1" sx={{ mb: 1 }}>
              Start by asking a question.
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              Examples:
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              • How many tables are there?
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              • Show me foreign key relationships.
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              • Top 5 customers by orders.
            </Typography>
          </Paper>
        )}

        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} />
        ))}
      </Box>

      {/* Composer */}
      <Box
        sx={{
          p: 1,
          borderTop: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.default',
          display: 'flex',
          gap: 1,
        }}
      >
        <TextField
          placeholder="Ask a question..."
          size="small"
          fullWidth
          multiline
          maxRows={6}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
        />
        <IconButton
          color="primary"
          onClick={handleSubmit}
          disabled={!canSend}
          aria-label="Send"
          sx={{ alignSelf: 'flex-end' }}
        >
          {sending ? <CircularProgress size={20} /> : <SendIcon />}
        </IconButton>
      </Box>
    </Box>
  );
};

function renderSchemaSummary(query, database, results) {
  if (!results || results.length === 0) {
    return `I couldn't find relevant schema information for "${query}".`;
  }

  const lines = [];
  lines.push(`Schema results for "${query}"${database ? ` in ${database}` : ''}:`);

  results.slice(0, 5).forEach((r, idx) => {
    const md = r.metadata || {};
    const type = (md.type || 'item').toString();
    let label = type;

    if (type === 'table' && md.table_name) label = `table ${md.table_name}`;
    else if (type === 'column' && md.table_name && md.column_name) label = `column ${md.table_name}.${md.column_name}`;
    else if (type === 'collection' && md.collection_name) label = `collection ${md.collection_name}`;
    else if (type === 'relationship' && md.from_table && md.to_table) label = `relationship ${md.from_table} -> ${md.to_table}`;

    const preview = (r.content || '').slice(0, 140).replace(/\s+/g, ' ');
    lines.push(`• ${label}${preview ? ` — ${preview}${r.content?.length > 140 ? '…' : ''}` : ''}`);
  });

  return lines.join('\n');
}

export default ChatInterface;