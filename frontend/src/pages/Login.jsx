import React, { useState } from 'react';
import {
  Box, Button, Card, CardContent, TextField, Typography, Alert, CircularProgress
} from '@mui/material';
import api from '../api';

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError]       = useState('');
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/api/login', { username, password });
      onLogin(res.data);
    } catch (err) {
      setError(err.response?.data?.error || '登入失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Card sx={{ width: 360, p: 2 }}>
        <CardContent>
          <Typography variant="h5" gutterBottom align="center">分散式帳本系統</Typography>
          <Typography variant="body2" color="text.secondary" align="center" mb={3}>
            請登入以繼續
          </Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Box component="form" onSubmit={handleSubmit} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="帳號"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              autoFocus
            />
            <TextField
              label="密碼"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
            <Button type="submit" variant="contained" disabled={loading} size="large">
              {loading ? <CircularProgress size={24} /> : '登入'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
