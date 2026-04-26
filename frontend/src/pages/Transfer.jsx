import React, { useState } from 'react';
import {
  Box, Button, TextField, Typography, Alert, CircularProgress,
  Card, CardContent, Divider
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import api from '../api';

export default function Transfer() {
  const [form, setForm]       = useState({ sender: '', receiver: '', amount: '' });
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
      const res = await api.post('/api/transfer', {
        sender:   form.sender.trim(),
        receiver: form.receiver.trim(),
        amount:   Number(form.amount),
      });
      setResult(res.data);
      setForm({ sender: '', receiver: '', amount: '' });
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
