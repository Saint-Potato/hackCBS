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
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import { api } from '../services/apiClient.js'; // Add .js extension

const MessageBubble = ({ role, children }) => {
  const isUser = role === 'user';
  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 1.5,
      }}
    >
      <Paper
        elevation={0}
        sx={{
          maxWidth: 'min(800px, 90%)',
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
        // Render concise list of relevant schema results
        const results = data.results || [];
        pushMessage({
          role: 'assistant',
          content: renderSchemaSummary(text, selectedDb || data.database, results),
        });
      } else if (data.type === 'data') {
        // Show proposed SQL and explanation, allow execution
        pushMessage({
          role: 'assistant',
          content: `I generated a SQL query for your request.`,
          sql: data.sql_query,
          database: selectedDb || data.database,
          explanation: data.explanation,
          warnings: data.warnings || [],
          assumptions: data.assumptions || [],
          canExecute: true,
        });
      } else {
        pushMessage({
          role: 'assistant',
          content: res?.message || 'No data returned.',
        });
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
          <MessageBubble key={m.id} role={m.role}>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
              {m.content}
            </Typography>

            {/* Assistant details */}
            {m.sql && (
              <>
                <Divider sx={{ my: 1.25 }} />
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                  Proposed SQL
                </Typography>
                <CodeBlock code={m.sql} language="sql" />
                {m.explanation && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 1 }}>
                      Explanation
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                      {m.explanation}
                    </Typography>
                  </>
                )}
                {m.warnings && m.warnings.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 1 }}>
                      Warnings
                    </Typography>
                    <ul style={{ marginTop: 4, marginBottom: 0 }}>
                      {m.warnings.map((w, i) => (
                        <li key={i}>
                          <Typography variant="body2">{w}</Typography>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
                {m.assumptions && m.assumptions.length > 0 && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 1 }}>
                      Assumptions
                    </Typography>
                    <ul style={{ marginTop: 4, marginBottom: 0 }}>
                      {m.assumptions.map((a, i) => (
                        <li key={i}>
                          <Typography variant="body2">{a}</Typography>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
                {m.canExecute && (
                  <Box sx={{ mt: 1 }}>
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<PlayArrowIcon />}
                      disabled={!!executingSqlId}
                      onClick={() => handleExecuteSql(m.id, m.sql, m.database)}
                    >
                      {executingSqlId === m.id ? 'Executing...' : 'Execute SQL'}
                    </Button>
                  </Box>
                )}
              </>
            )}

            {/* SQL execution results */}
            {Array.isArray(m.sqlResults) && (
              <>
                <Divider sx={{ my: 1.25 }} />
                <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                  Results
                </Typography>
                <ResultTable rows={m.sqlResults} />
                {m.count != null && (
                  <Typography variant="caption" sx={{ opacity: 0.7, display: 'block', mt: 0.75 }}>
                    Rows: {m.count}
                  </Typography>
                )}
                {m.sqlQuery && (
                  <>
                    <Typography variant="subtitle2" sx={{ mt: 1 }}>
                      Executed SQL
                    </Typography>
                    <CodeBlock code={m.sqlQuery} language="sql" />
                  </>
                )}
              </>
            )}
          </MessageBubble>
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