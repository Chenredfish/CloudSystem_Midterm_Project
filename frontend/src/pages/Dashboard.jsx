import React, { useEffect, useState } from 'react';
import {
  Box, Typography, CircularProgress, Alert,
  Accordion, AccordionSummary, AccordionDetails,
  Chip, List, ListItem, ListItemText, Button
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import api from '../api';

export default function Dashboard() {
  const [blocks, setBlocks]   = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState('');

  const fetchBlocks = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/api/blocks');
      setBlocks(res.data);
    } catch (err) {
      setError(err.response?.data?.error || '無法取得區塊資料');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBlocks(); }, []);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">區塊鏈帳本</Typography>
        <Button startIcon={<RefreshIcon />} onClick={fetchBlocks} disabled={loading} size="small">
          重新整理
        </Button>
      </Box>

      {loading && <Box display="flex" justifyContent="center" py={4}><CircularProgress /></Box>}
      {error && <Alert severity="error">{error}</Alert>}

      {!loading && blocks.slice().reverse().map(block => (
        <Accordion key={block.block_num} defaultExpanded={block.block_num === blocks.length}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Box display="flex" alignItems="center" gap={2} width="100%">
              <Chip label={`Block #${block.block_num}`} color="primary" size="small" />
              <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: 11 }}>
                {block.hash?.slice(0, 16)}…
              </Typography>
              <Chip
                label={`${block.transactions.length} 筆交易`}
                size="small"
                variant="outlined"
                sx={{ ml: 'auto' }}
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="caption" display="block" color="text.secondary" mb={1}>
              prev: {block.prev_hash?.slice(0, 32)}…
            </Typography>
            <List dense disablePadding>
              {block.transactions.map((tx, i) => (
                <ListItem key={i} disableGutters sx={{ borderBottom: '1px solid #f0f0f0' }}>
                  <ListItemText
                    primary={tx}
                    primaryTypographyProps={{ fontFamily: 'monospace', fontSize: 13 }}
                  />
                </ListItem>
              ))}
            </List>
          </AccordionDetails>
        </Accordion>
      ))}

      {!loading && blocks.length === 0 && !error && (
        <Typography color="text.secondary" align="center" py={4}>尚無區塊資料</Typography>
      )}
    </Box>
  );
}
