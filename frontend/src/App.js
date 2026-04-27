import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import {
  Box, CssBaseline, AppBar, Toolbar, Typography, Drawer, List,
  ListItemButton, ListItemIcon, ListItemText, Divider, Button, Chip
} from '@mui/material';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SendIcon from '@mui/icons-material/Send';
import AccountBalanceWalletIcon from '@mui/icons-material/AccountBalanceWallet';
import VerifiedIcon from '@mui/icons-material/Verified';
import LogoutIcon from '@mui/icons-material/Logout';
import HubIcon from '@mui/icons-material/Hub';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Transfer from './pages/Transfer';
import Balance from './pages/Balance';
import Verify from './pages/Verify';
import Nodes from './pages/Nodes';
import api from './api';

const DRAWER_WIDTH = 220;

const theme = createTheme({
  palette: { primary: { main: '#1565c0' } },
});

const NAV_ITEMS = [
  { label: '帳本總覽',   path: '/dashboard', icon: <DashboardIcon /> },
  { label: '執行轉帳',   path: '/transfer',  icon: <SendIcon /> },
  { label: '餘額查詢',   path: '/balance',   icon: <AccountBalanceWalletIcon /> },
  { label: '驗證 / 修復', path: '/verify',   icon: <VerifiedIcon /> },
  { label: '節點管理',   path: '/nodes',     icon: <HubIcon />, adminOnly: true },
];

function Layout({ user, onLogout }) {
  const navigate  = useNavigate();
  const location  = useLocation();

  const handleLogout = async () => {
    try { await api.post('/api/logout'); } catch (_) {}
    onLogout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: t => t.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>分散式共享帳本</Typography>
          <Chip label={user.role === 'admin' ? '管理員' : '用戶'} size="small" color="default"
            sx={{ mr: 1, bgcolor: 'rgba(255,255,255,0.2)', color: '#fff' }} />
          <Typography variant="body2" sx={{ mr: 2 }}>{user.username}</Typography>
          <Button color="inherit" size="small" startIcon={<LogoutIcon />} onClick={handleLogout}>
            登出
          </Button>
        </Toolbar>
      </AppBar>

      <Drawer variant="permanent" sx={{
        width: DRAWER_WIDTH,
        '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
      }}>
        <Toolbar />
        <List>
          {NAV_ITEMS.filter(item => !item.adminOnly || user.role === 'admin').map(item => (
            <ListItemButton
              key={item.path}
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
        <Divider />
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transfer"  element={<Transfer />} />
          <Route path="/balance"   element={<Balance />} />
          <Route path="/verify"    element={<Verify role={user.role} />} />
          <Route path="/nodes"     element={<Nodes />} />
          <Route path="*"          element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

export default function App() {
  const [user, setUser]     = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    api.get('/api/me')
      .then(res => setUser(res.data))
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);

  if (checking) return null;

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        {user ? (
          <Layout user={user} onLogout={() => setUser(null)} />
        ) : (
          <Routes>
            <Route path="*" element={<Login onLogin={data => setUser(data)} />} />
          </Routes>
        )}
      </BrowserRouter>
    </ThemeProvider>
  );
}
