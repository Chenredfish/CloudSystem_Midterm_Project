import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Alert, CircularProgress,
  Card, CardContent, CardHeader, Divider,
  List, ListItem, ListItemText, ListItemIcon,
  TextField, Button, Chip, Stack, IconButton,
} from '@mui/material';
import HubIcon from '@mui/icons-material/Hub';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import PendingIcon from '@mui/icons-material/HourglassEmpty';
import api from '../api';

export default function Nodes() {
  const [nodes, setNodes]       = useState([]);
  const [pending, setPending]   = useState([]);
  const [loading, setLoading]   = useState(false);
  const [newUrl, setNewUrl]     = useState('');
  const [approving, setApproving] = useState(''); // url being approved, or ''
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');

  const fetchNodes = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/api/nodes');
      setNodes(res.data.nodes || []);
      setPending(res.data.pending || []);
    } catch (err) {
      setError(err.response?.data?.error || '無法取得節點資訊');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchNodes(); }, [fetchNodes]);

  const handleApprove = async (url) => {
    const target = url || newUrl.trim();
    if (!target) return;
    setApproving(target);
    setError('');
    setSuccess('');
    try {
      const res = await api.post('/api/nodes/approve', { url: target });
      setSuccess(`節點 ${res.data.url} 已核准並開始同步`);
      if (!url) setNewUrl('');
      await fetchNodes();
    } catch (err) {
      setError(err.response?.data?.error || '核准失敗');
    } finally {
      setApproving('');
    }
  };

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">節點管理</Typography>
        <IconButton onClick={fetchNodes} disabled={loading} size="small">
          {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
        </IconButton>
      </Stack>

      {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      {/* Known peers */}
      <Card sx={{ mb: 3 }}>
        <CardHeader
          avatar={<HubIcon color="primary" />}
          title="已知節點"
          titleTypographyProps={{ variant: 'subtitle1' }}
          action={
            <Chip
              label={`${nodes.length} 個節點`}
              size="small"
              color="primary"
              variant="outlined"
            />
          }
        />
        <Divider />
        <CardContent sx={{ p: 0 }}>
          {nodes.length === 0 ? (
            <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
              目前無已知 peer 節點
            </Typography>
          ) : (
            <List dense disablePadding>
              {nodes.map((node, idx) => (
                <React.Fragment key={node.url}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItem
                    secondaryAction={
                      <Chip
                        label={node.status === 'online' ? `${node.block_count} 個區塊` : '無法連線'}
                        size="small"
                        color={node.status === 'online' ? 'success' : 'error'}
                        variant="outlined"
                      />
                    }
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      {node.status === 'online'
                        ? <CheckCircleIcon color="success" fontSize="small" />
                        : <ErrorIcon color="error" fontSize="small" />}
                    </ListItemIcon>
                    <ListItemText
                      primary={node.node ?? node.url}
                      secondary={node.url}
                      primaryTypographyProps={{ fontSize: 14 }}
                      secondaryTypographyProps={{ fontSize: 12 }}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Pending nodes */}
      {pending.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardHeader
            avatar={<PendingIcon color="warning" />}
            title="待審核節點"
            titleTypographyProps={{ variant: 'subtitle1' }}
            action={
              <Chip
                label={`${pending.length} 個待審核`}
                size="small"
                color="warning"
                variant="outlined"
              />
            }
          />
          <Divider />
          <CardContent sx={{ p: 0 }}>
            <List dense disablePadding>
              {pending.map((url, idx) => (
                <React.Fragment key={url}>
                  {idx > 0 && <Divider component="li" />}
                  <ListItem
                    secondaryAction={
                      <Button
                        size="small"
                        variant="outlined"
                        color="warning"
                        onClick={() => handleApprove(url)}
                        disabled={approving === url}
                        startIcon={approving === url ? <CircularProgress size={14} /> : <AddIcon />}
                      >
                        核准
                      </Button>
                    }
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <PendingIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={url}
                      primaryTypographyProps={{ fontSize: 14 }}
                    />
                  </ListItem>
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Add new node */}
      <Card>
        <CardHeader
          avatar={<AddIcon color="primary" />}
          title="手動核准節點加入"
          titleTypographyProps={{ variant: 'subtitle1' }}
        />
        <Divider />
        <CardContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            輸入新節點的完整 URL（例如 <code>http://node4:5000</code>），核准後系統將自動廣播並觸發區塊同步。
          </Typography>
          <Stack direction="row" spacing={1}>
            <TextField
              size="small"
              placeholder="http://node4:5000"
              value={newUrl}
              onChange={e => setNewUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleApprove()}
              sx={{ flexGrow: 1 }}
              disabled={!!approving}
            />
            <Button
              variant="contained"
              onClick={() => handleApprove()}
              disabled={!!approving || !newUrl.trim()}
              startIcon={approving === newUrl ? <CircularProgress size={18} /> : <AddIcon />}
            >
              核准加入
            </Button>
          </Stack>
        </CardContent>
      </Card>
    </Box>
  );
}
