import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Alert, CircularProgress,
  Card, CardContent, CardHeader, Divider,
  List, ListItem, ListItemText, Chip, Stack, IconButton,
} from '@mui/material';
import HistoryIcon from '@mui/icons-material/History';
import RefreshIcon from '@mui/icons-material/Refresh';
import api from '../api';

const ACTION_COLOR = {
  transfer:     'primary',
  set_password: 'info',
  freeze:       'error',
  unfreeze:     'success',
};

const ACTION_LABEL = {
  transfer:     '轉帳',
  set_password: '設密碼',
  freeze:       '凍結',
  unfreeze:     '解凍',
};

export default function AuditLog() {
  const [logs, setLogs]       = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/api/admin/audit');
      setLogs([...(res.data.logs || [])].reverse()); // newest first
    } catch (err) {
      setError(err.response?.data?.error || '無法取得稽核日誌');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">稽核日誌</Typography>
        <IconButton onClick={fetchLogs} disabled={loading} size="small">
          {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
        </IconButton>
      </Stack>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}

      <Card>
        <CardHeader
          avatar={<HistoryIcon color="primary" />}
          title="操作記錄"
          titleTypographyProps={{ variant: 'subtitle1' }}
          action={
            <Chip
              label={`${logs.length} 筆`}
              size="small"
              color="primary"
              variant="outlined"
            />
          }
        />
        <Divider />
        <CardContent sx={{ p: 0 }}>
          {logs.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
              尚無稽核記錄
            </Typography>
          ) : (
            <List dense disablePadding>
              {logs.map((log, idx) => (
                <React.Fragment key={idx}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItem
                    secondaryAction={
                      <Chip
                        label={ACTION_LABEL[log.action] || log.action}
                        size="small"
                        color={ACTION_COLOR[log.action] || 'default'}
                        variant="outlined"
                      />
                    }
                  >
                    <ListItemText
                      primary={
                        <Stack direction="row" spacing={1} alignItems="center">
                          <Typography variant="body2" fontWeight={500}>{log.target}</Typography>
                          {log.detail && (
                            <Typography variant="caption" color="text.secondary">
                              {log.detail}
                            </Typography>
                          )}
                        </Stack>
                      }
                      secondary={`${log.timestamp}  by ${log.actor}`}
                      secondaryTypographyProps={{ fontSize: 11 }}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
