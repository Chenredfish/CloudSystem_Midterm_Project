import React, { useState } from 'react';
import {
  Box, Button, TextField, Typography, Alert, CircularProgress,
  Card, CardContent, Chip
} from '@mui/material';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import SearchIcon from '@mui/icons-material/Search';
import api from '../api';

export default function Balance() {
  const [account, setAccount] = useState('');
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleQuery = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    if (!account.trim()) return;
    setLoading(true);
    try {
      const res = await api.get(`/api/balance/${encodeURIComponent(account.trim())}`);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || '查詢失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box maxWidth={480} mx="auto">
      <Typography variant="h6" mb={2}>餘額查詢</Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box component="form" onSubmit={handleQuery} display="flex" gap={1}>
            <TextField
              label="帳戶名稱"
              value={account}
              onChange={e => setAccount(e.target.value)}
              required
              fullWidth
              autoFocus
            />
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              sx={{ minWidth: 90 }}
              startIcon={loading ? <CircularProgress size={18} /> : <SearchIcon />}
            >
              查詢
            </Button>
          </Box>
        </CardContent>
      </Card>

      {error && <Alert severity="error">{error}</Alert>}

      {result && (
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" gap={2}>
              <AccountBalanceWalletIcon color="primary" fontSize="large" />
              <Box>
                <Typography variant="body2" color="text.secondary">帳戶</Typography>
                <Typography variant="h6">{result.account}</Typography>
              </Box>
              <Box ml="auto" textAlign="right">
                <Typography variant="body2" color="text.secondary">餘額</Typography>
                <Chip
                  label={result.balance.toLocaleString()}
                  color="primary"
                  sx={{ fontSize: 18, height: 36 }}
                />
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
