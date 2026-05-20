'use client';

import { useEffect, useState } from 'react';
import { Box, Button, Typography, Paper, Alert, CircularProgress } from '@mui/material';
import { FlaskConical } from 'lucide-react';

export default function LoginPage() {
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    // Check if already authenticated
    fetch('/api/auth/session')
      .then(res => res.json())
      .then(data => {
        if (data.authenticated) {
          window.location.href = '/';
        } else if (!data.authEnabled) {
          window.location.href = '/';
        } else {
          setChecking(false);
        }
      })
      .catch(() => setChecking(false));

    // Check for error in URL params
    const params = new URLSearchParams(window.location.search);
    const err = params.get('error');
    if (err === 'idcs_denied') setError('Access denied by identity provider');
    else if (err === 'token_failed') setError('Authentication failed. Please try again.');
    else if (err === 'no_code') setError('Invalid login response. Please try again.');
  }, []);

  if (checking) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress size={24} sx={{ color: '#1a1a1a' }} />
      </Box>
    );
  }

  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)',
    }}>
      <Paper
        elevation={0}
        sx={{
          p: 5,
          width: 380,
          borderRadius: 3,
          border: '1px solid rgba(0,0,0,0.08)',
          textAlign: 'center',
        }}
      >
        <FlaskConical size={32} strokeWidth={1.5} color="#1a1a1a" />
        <Typography variant="h5" sx={{ mt: 1.5, fontWeight: 300, letterSpacing: '0.02em' }}>
          <strong>OCI</strong> Enterprise AI Agents
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', mt: 0.5, mb: 3 }}>
          Sign in with your OCI account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2, borderRadius: 2, textAlign: 'left' }}>
            {error}
          </Alert>
        )}

        <Button
          fullWidth
          variant="contained"
          href="/api/auth/login"
          sx={{
            py: 1.2,
            borderRadius: 2,
            textTransform: 'none',
            bgcolor: '#1a1a1a',
            '&:hover': { bgcolor: '#333' },
          }}
        >
          Sign in with OCI Identity
        </Button>
      </Paper>
    </Box>
  );
}
