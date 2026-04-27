import React, { useState } from 'react';
import {
  Box, Button, TextField, Typography, Alert, CircularProgress,
  Card, CardContent, Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import api from '../api';

export default function Transfer({ role }) {
  const isAdmin = role === 'admin';
  const [form, setForm]       = useState({ sender: '', receiver: '', amount: '', password: '' });
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const payload = {
        sender:   form.sender.trim(),
        receiver: form.receiver.trim(),
        amount:   Number(form.amount),
      };
      if (!isAdmin) payload.password = form.password;
      const res = await api.post('/api/transfer', payload);
      setResult(res.data);
      setForm({ sender: '', receiver: '', amount: '', password: '' });
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || '轉帳失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box maxWidth={480} mx="auto">
      <Typography variant="h6" mb={2}>執行轉帳</Typography>

      {error  && <Alert severity="error"   sx={{ mb: 2 }}>{error}</Alert>}
      {result && (
        <Alert severity="success" sx={{ mb: 2 }}>
          轉帳成功！區塊 #{result.block_num}
          {result.new_block_created && '（新區塊已建立）'}
          <br />{result.transaction}
        </Alert>
      )}

      <Card>
        <CardContent>
          <Box component="form" onSubmit={handleSubmit} display="flex" flexDirection="column" gap={2}>
            <TextField
              label="付款方"
              name="sender"
              value={form.sender}
              onChange={handleChange}
              required
              autoFocus
            />
            <TextField
              label="收款方"
              name="receiver"
              value={form.receiver}
              onChange={handleChange}
              required
            />
            <TextField
              label="金額"
              name="amount"
              type="number"
              value={form.amount}
              onChange={handleChange}
              required
              inputProps={{ min: 1 }}
            />
            {!isAdmin && (
              <TextField
                label="付款方密碼"
                name="password"
                type="password"
                value={form.password}
                onChange={handleChange}
                required
                helperText="帳戶密碼由管理員設定"
              />
            )}
            <Divider />
            <Button
              type="submit"
              variant="contained"
              disabled={loading}
              startIcon={loading ? <CircularProgress size={18} /> : <SendIcon />}
              size="large"
            >
              確認轉帳
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
