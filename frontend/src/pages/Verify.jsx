import React, { useState } from 'react';
import {
  Box, Button, Typography, Alert, CircularProgress,
  Card, CardContent, CardHeader, Divider,
  List, ListItem, ListItemText, Chip, Stack
} from '@mui/material';
import VerifiedIcon from '@mui/icons-material/Verified';
import WarningIcon from '@mui/icons-material/Warning';
import CompareArrowsIcon from '@mui/icons-material/CompareArrows';
import BuildIcon from '@mui/icons-material/Build';
import api from '../api';

function StatusCard({ title, icon, status, children }) {
  return (
    <Card sx={{ mb: 2 }}>
      <CardHeader
        avatar={icon}
        title={title}
        action={status}
        titleTypographyProps={{ variant: 'subtitle1' }}
      />
      <Divider />
      <CardContent>{children}</CardContent>
    </Card>
  );
}

export default function Verify({ role }) {
  const [verifyResult, setVerifyResult] = useState(null);
  const [compareResult, setCompareResult] = useState(null);
  const [repairResult, setRepairResult]   = useState(null);
  const [loading, setLoading] = useState('');
  const [error, setError]     = useState('');

  const run = async (action) => {
    setError('');
    setLoading(action);
    try {
      let res;
      if (action === 'verify')  res = await api.get('/api/chain/verify');
      if (action === 'compare') res = await api.post('/api/chain/compare');
      if (action === 'repair')  res = await api.post('/api/chain/repair');

      if (action === 'verify')  setVerifyResult(res.data);
      if (action === 'compare') setCompareResult(res.data);
      if (action === 'repair')  { setRepairResult(res.data); setCompareResult(null); }
    } catch (err) {
      setError(err.response?.data?.error || `${action} 失敗`);
    } finally {
      setLoading('');
    }
  };

  return (
    <Box>
      <Typography variant="h6" mb={2}>鏈結驗證 / 修復</Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Verify */}
      <StatusCard
        title="本節點完整性驗證"
        icon={<VerifiedIcon color="primary" />}
        status={verifyResult && (
          <Chip
            label={verifyResult.valid ? '通過' : '失敗'}
            color={verifyResult.valid ? 'success' : 'error'}
            size="small"
          />
        )}
      >
        <Button
          variant="contained"
          onClick={() => run('verify')}
          disabled={!!loading}
          startIcon={loading === 'verify' ? <CircularProgress size={18} /> : <VerifiedIcon />}
          sx={{ mb: verifyResult ? 2 : 0 }}
        >
          執行驗證
        </Button>

        {verifyResult && (
          <Box mt={1}>
            <Typography variant="body2">區塊數：{verifyResult.block_count}</Typography>
            {verifyResult.valid && verifyResult.reward && (
              <Alert severity="info" sx={{ mt: 1 }}>
                驗證獎勵：{verifyResult.reward.transaction}（區塊 #{verifyResult.reward.block_num}）
              </Alert>
            )}
            {!verifyResult.valid && verifyResult.errors.length > 0 && (
              <Box mt={1}>
                <Typography variant="body2" color="error" gutterBottom>錯誤列表：</Typography>
                <List dense disablePadding>
                  {verifyResult.errors.map((e, i) => (
                    <ListItem key={i} disableGutters>
                      <WarningIcon color="error" fontSize="small" sx={{ mr: 1 }} />
                      <ListItemText primary={e} primaryTypographyProps={{ fontSize: 13 }} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </Box>
        )}
      </StatusCard>

      {/* Compare & Repair — admin only */}
      {role === 'admin' && (
        <>
          <StatusCard
            title="跨節點比對"
            icon={<CompareArrowsIcon color="primary" />}
            status={compareResult && (
              <Chip
                label={compareResult.consistent ? '一致' : `${compareResult.diffs?.length} 個差異`}
                color={compareResult.consistent ? 'success' : 'warning'}
                size="small"
              />
            )}
          >
            <Stack direction="row" spacing={1} mb={compareResult ? 2 : 0}>
              <Button
                variant="outlined"
                onClick={() => run('compare')}
                disabled={!!loading}
                startIcon={loading === 'compare' ? <CircularProgress size={18} /> : <CompareArrowsIcon />}
              >
                比對所有節點
              </Button>
            </Stack>

            {compareResult && !compareResult.consistent && compareResult.diffs?.map(diff => (
              <Card key={diff.block_num} variant="outlined" sx={{ mb: 1, p: 1 }}>
                <Typography variant="body2" fontWeight="bold">Block #{diff.block_num}</Typography>
                <Typography variant="caption" display="block">本機 hash：{diff.local_hash?.slice(0, 24)}…</Typography>
                {Object.entries(diff.peer_hashes).map(([peer, hash]) => (
                  <Typography key={peer} variant="caption" display="block" color="text.secondary">
                    {peer}：{hash?.slice(0, 24) ?? '無法取得'}…
                  </Typography>
                ))}
              </Card>
            ))}
          </StatusCard>

          <StatusCard
            title="多數決修復"
            icon={<BuildIcon color="primary" />}
            status={repairResult && (
              <Chip
                label={`已修復 ${repairResult.repaired_count} 個區塊`}
                color={repairResult.repaired_count > 0 ? 'success' : 'default'}
                size="small"
              />
            )}
          >
            <Button
              variant="contained"
              color="warning"
              onClick={() => run('repair')}
              disabled={!!loading}
              startIcon={loading === 'repair' ? <CircularProgress size={18} /> : <BuildIcon />}
            >
              執行修復
            </Button>
            {repairResult && repairResult.repaired_count > 0 && (
              <Alert severity="success" sx={{ mt: 2 }}>
                已修復區塊：{repairResult.repaired_blocks.join(', ')}
              </Alert>
            )}
          </StatusCard>
        </>
      )}
    </Box>
  );
}
