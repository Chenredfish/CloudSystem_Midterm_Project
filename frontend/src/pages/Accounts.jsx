import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Typography, Alert, CircularProgress,
  Card, CardContent, CardHeader, Divider,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, IconButton, Button, TextField, Dialog, DialogTitle,
  DialogContent, DialogActions, Stack,
} from '@mui/material';
import ManageAccountsIcon from '@mui/icons-material/ManageAccounts';
import LockIcon from '@mui/icons-material/Lock';
import LockOpenIcon from '@mui/icons-material/LockOpen';
import KeyIcon from '@mui/icons-material/Key';
import RefreshIcon from '@mui/icons-material/Refresh';
import api from '../api';

export default function Accounts() {
  const [accounts, setAccounts]   = useState([]);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [success, setSuccess]     = useState('');
  const [pwDialog, setPwDialog]   = useState(null); // { account } or null
  const [pwValue, setPwValue]     = useState('');
  const [pwLoading, setPwLoading] = useState(false);

  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.get('/api/admin/accounts');
      setAccounts(res.data.accounts || []);
    } catch (err) {
      setError(err.response?.data?.error || '無法取得帳戶列表');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAccounts(); }, [fetchAccounts]);

  const handleFreeze = async (account, freeze) => {
    setError('');
    setSuccess('');
    try {
      await api.post(freeze ? '/api/admin/freeze' : '/api/admin/unfreeze', { account });
      setSuccess(`${account} 已${freeze ? '凍結' : '解凍'}`);
      await fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.error || '操作失敗');
    }
  };

  const openPwDialog = (account) => {
    setPwDialog({ account });
    setPwValue('');
  };

  const handleSetPassword = async () => {
    if (!pwValue.trim()) return;
    setPwLoading(true);
    setError('');
    setSuccess('');
    try {
      await api.post('/api/admin/account/password', {
        account:  pwDialog.account,
        password: pwValue,
      });
      setSuccess(`${pwDialog.account} 密碼已設定`);
      setPwDialog(null);
      await fetchAccounts();
    } catch (err) {
      setError(err.response?.data?.error || '設定密碼失敗');
    } finally {
      setPwLoading(false);
    }
  };

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
        <Typography variant="h6">帳戶管理</Typography>
        <IconButton onClick={fetchAccounts} disabled={loading} size="small">
          {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
        </IconButton>
      </Stack>

      {error   && <Alert severity="error"   sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Card>
        <CardHeader
          avatar={<ManageAccountsIcon color="primary" />}
          title="帳本帳戶列表"
          titleTypographyProps={{ variant: 'subtitle1' }}
          action={
            <Chip
              label={`${accounts.length} 個帳戶`}
              size="small"
              color="primary"
              variant="outlined"
            />
          }
        />
        <Divider />
        <CardContent sx={{ p: 0 }}>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'grey.50' }}>
                  <TableCell>帳戶</TableCell>
                  <TableCell align="right">餘額</TableCell>
                  <TableCell align="center">密碼狀態</TableCell>
                  <TableCell align="center">帳戶狀態</TableCell>
                  <TableCell align="center">操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accounts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ color: 'text.secondary', py: 3 }}>
                      帳本內尚無帳戶
                    </TableCell>
                  </TableRow>
                ) : accounts.map(row => (
                  <TableRow key={row.account} hover>
                    <TableCell sx={{ fontFamily: 'monospace' }}>{row.account}</TableCell>
                    <TableCell align="right">{row.balance ?? '—'}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={row.has_password ? '已啟用' : '未設定'}
                        size="small"
                        color={row.has_password ? 'success' : 'default'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={row.frozen ? '已凍結' : '正常'}
                        size="small"
                        color={row.frozen ? 'error' : 'success'}
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Stack direction="row" spacing={0.5} justifyContent="center">
                        <IconButton
                          size="small"
                          title="設定密碼"
                          onClick={() => openPwDialog(row.account)}
                        >
                          <KeyIcon fontSize="small" />
                        </IconButton>
                        <IconButton
                          size="small"
                          title={row.frozen ? '解凍' : '凍結'}
                          color={row.frozen ? 'success' : 'error'}
                          onClick={() => handleFreeze(row.account, !row.frozen)}
                        >
                          {row.frozen ? <LockOpenIcon fontSize="small" /> : <LockIcon fontSize="small" />}
                        </IconButton>
                      </Stack>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Set Password Dialog */}
      <Dialog open={!!pwDialog} onClose={() => setPwDialog(null)} maxWidth="xs" fullWidth>
        <DialogTitle>設定帳戶密碼</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            帳戶：<strong>{pwDialog?.account}</strong>
          </Typography>
          <TextField
            label="新密碼"
            type="password"
            fullWidth
            autoFocus
            value={pwValue}
            onChange={e => setPwValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSetPassword()}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPwDialog(null)}>取消</Button>
          <Button
            variant="contained"
            onClick={handleSetPassword}
            disabled={!pwValue.trim() || pwLoading}
            startIcon={pwLoading ? <CircularProgress size={16} /> : <KeyIcon />}
          >
            確認設定
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
