import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Typography,
  Paper,
  Chip,
  styled,
  CircularProgress,
  Avatar,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Send as SendIcon,
  Psychology as AIIcon,
  Person as UserIcon,
  Code as CodeIcon,
  ContentCopy as CopyIcon,
  PlayArrow as RunIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useApi } from '../contexts/ApiContext';

const ChatContainer = styled(Box)(({ theme }) => ({
  height: '100vh',
  display: 'flex',
  flexDirection: 'column',
  backgroundColor: theme.palette.background.default,
}));

const ChatHeader = styled(Box)(({ theme }) => ({
  padding: '8px 16px',
  borderBottom: `1px solid ${theme.palette.divider}`,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  minHeight: 35,
  backgroundColor: theme.palette.background.paper,
}));

const MessagesContainer = styled(Box)({
  flex: 1,
  overflowY: 'auto',
  padding: '16px',
  display: 'flex',
  flexDirection: 'column',
  gap: '16px',
});

const MessageBubble = styled(Paper)(({ theme, isUser }) => ({
  padding: '12px 16px',
  maxWidth: '80%',
  alignSelf: isUser ? 'flex-end' : 'flex-start',
  backgroundColor: isUser ? '#264f78' : theme.palette.background.paper,
  border: `1px solid ${isUser ? '#264f78' : theme.palette.divider}`,
  borderRadius: 8,
}));

const InputContainer = styled(Box)(({ theme }) => ({
  padding: '16px',
  borderTop: `1px solid ${theme.palette.divider}`,
  backgroundColor: theme.palette.background.paper,
}));

const CodeBlock = styled(Box)(({ theme }) => ({
  backgroundColor: '#1e1e1e',
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: 4,
  padding: '12px',
  marginTop: '8px',
  fontFamily: '"Consolas", "Monaco", "Courier New", monospace',
  fontSize: 13,
  overflow: 'auto',
  position: 'relative',
  '&:hover .code-actions': {
    opacity: 1,
  },
}));

const ChatInterface = () => {
  const {
    askQuestion,
    executeSQL,
    isAskingQuestion,
    isExecutingSQL,
    questionResult,
    sqlResult,
    selectedDatabase,
  } = useApi();

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'ai',
      content: 'Hello! I\'m your AI database assistant. Ask me anything about your database schema or data.',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle question result
  useEffect(() => {
    if (questionResult?.data) {
      const result = questionResult.data;
      
      const aiMessage = {
        id: Date.now(),
        type: 'ai',
        content: result.type === 'schema' 
          ? 'Here\'s what I found in your database schema:' 
          : 'I\'ve generated a SQL query for you:',
        timestamp: new Date(),
        data: result,
      };
      
      setMessages(prev => [...prev, aiMessage]);
    }
  }, [questionResult]);

  // Handle SQL execution result
  useEffect(() => {
    if (sqlResult?.data) {
      const aiMessage = {
        id: Date.now(),
        type: 'ai',
        content: `Query executed successfully! Found ${sqlResult.data.count} rows.`,
        timestamp: new Date(),
        data: { results: sqlResult.data.results },
      };
      
      setMessages(prev => [...prev, aiMessage]);
    }
  }, [sqlResult]);

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    // Add user message
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    // Send to API
    askQuestion({ query: inputValue, database: selectedDatabase });
    
    setInputValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleExecuteSQL = (sqlQuery) => {
    if (selectedDatabase) {
      executeSQL({ sqlQuery, database: selectedDatabase });
    }
  };

  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code);
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'ai',
        content: 'Chat cleared. How can I help you?',
        timestamp: new Date(),
      },
    ]);
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';

    return (
      <Box
        key={message.id}
        sx={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 1,
          flexDirection: isUser ? 'row-reverse' : 'row',
        }}
      >
        <Avatar
          sx={{
            width: 32,
            height: 32,
            bgcolor: isUser ? '#264f78' : '#3794ff',
          }}
        >
          {isUser ? <UserIcon fontSize="small" /> : <AIIcon fontSize="small" />}
        </Avatar>

        <Box sx={{ flex: 1, maxWidth: '80%' }}>
          <MessageBubble isUser={isUser} elevation={0}>
            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
              {message.content}
            </Typography>

            {/* Render SQL Query */}
            {message.data?.sql_query && (
              <CodeBlock>
                <Box
                  className="code-actions"
                  sx={{
                    position: 'absolute',
                    top: 8,
                    right: 8,
                    display: 'flex',
                    gap: 0.5,
                    opacity: 0,
                    transition: 'opacity 0.2s',
                  }}
                >
                  <Tooltip title="Copy">
                    <IconButton
                      size="small"
                      onClick={() => handleCopyCode(message.data.sql_query)}
                      sx={{ color: 'text.secondary' }}
                    >
                      <CopyIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Execute">
                    <IconButton
                      size="small"
                      onClick={() => handleExecuteSQL(message.data.sql_query)}
                      sx={{ color: 'success.main' }}
                    >
                      <RunIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography
                  component="pre"
                  sx={{
                    margin: 0,
                    color: '#d4d4d4',
                    fontSize: 13,
                    lineHeight: 1.5,
                  }}
                >
                  {message.data.sql_query}
                </Typography>
              </CodeBlock>
            )}

            {/* Render Schema Results */}
            {message.data?.results && Array.isArray(message.data.results) && (
              <Box sx={{ mt: 1 }}>
                {message.data.results.slice(0, 3).map((result, idx) => (
                  <Paper
                    key={idx}
                    sx={{
                      p: 1,
                      mb: 1,
                      backgroundColor: 'rgba(255, 255, 255, 0.05)',
                      border: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <Typography variant="caption" sx={{ fontFamily: 'monospace', fontSize: 11 }}>
                      {result.content?.substring(0, 200)}...
                    </Typography>
                  </Paper>
                ))}
              </Box>
            )}

            {/* Render Explanation */}
            {message.data?.explanation && (
              <Box sx={{ mt: 1, p: 1, backgroundColor: 'rgba(55, 148, 255, 0.1)', borderRadius: 1 }}>
                <Typography variant="caption" sx={{ fontSize: 11, color: 'info.main' }}>
                  💡 {message.data.explanation}
                </Typography>
              </Box>
            )}
          </MessageBubble>

          <Typography
            variant="caption"
            sx={{
              fontSize: 10,
              color: 'text.secondary',
              mt: 0.5,
              display: 'block',
              textAlign: isUser ? 'right' : 'left',
            }}
          >
            {message.timestamp.toLocaleTimeString()}
          </Typography>
        </Box>
      </Box>
    );
  };

  return (
    <ChatContainer>
      {/* Header */}
      <ChatHeader>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AIIcon sx={{ color: '#3794ff' }} />
          <Typography variant="subtitle2" sx={{ fontWeight: 600, fontSize: 13 }}>
            AI Database Assistant
          </Typography>
          {selectedDatabase && (
            <Chip
              label={selectedDatabase}
              size="small"
              sx={{ height: 20, fontSize: 11 }}
            />
          )}
        </Box>
        <Tooltip title="Clear Chat">
          <IconButton size="small" onClick={handleClearChat}>
            <ClearIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </ChatHeader>

      {/* Messages */}
      <MessagesContainer>
        {messages.map(renderMessage)}
        
        {(isAskingQuestion || isExecutingSQL) && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: '#3794ff' }}>
              <AIIcon fontSize="small" />
            </Avatar>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: 13 }}>
                {isAskingQuestion ? 'Thinking...' : 'Executing query...'}
              </Typography>
            </Box>
          </Box>
        )}
        
        <div ref={messagesEndRef} />
      </MessagesContainer>

      {/* Input */}
      <InputContainer>
        {!selectedDatabase && (
          <Box sx={{ mb: 1 }}>
            <Chip
              label="⚠️ No database selected"
              size="small"
              color="warning"
              sx={{ fontSize: 11 }}
            />
          </Box>
        )}
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me anything about your database..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!selectedDatabase || isAskingQuestion}
            sx={{
              '& .MuiOutlinedInput-root': {
                fontSize: 13,
                padding: '8px 12px',
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || !selectedDatabase || isAskingQuestion}
            sx={{
              backgroundColor: 'primary.main',
              color: 'white',
              '&:hover': {
                backgroundColor: 'primary.dark',
              },
              '&:disabled': {
                backgroundColor: 'action.disabledBackground',
              },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatInterface;