import React, { useState } from 'react';
import { api } from '../../services/api';
import { User } from '../../types';

interface LoginProps {
  onLoginSuccess: (user: User, token: string) => void;
}

const OracleLogo = () => (
  <img
    src="/oracle-logo.png"
    alt="Oracle"
    className="h-8 w-auto"
  />
);


const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      console.log('Attempting login for:', username);
      const response = await api.login({ username, password });
      console.log('Login response received:', response);

      if (response && response.token && response.user) {
        console.log('Login successful, calling onLoginSuccess');
        try {
          onLoginSuccess(response.user, response.token);
          console.log('onLoginSuccess completed');
        } catch (callbackErr) {
          console.error('Error in onLoginSuccess callback:', callbackErr);
          setError('Login succeeded but failed to initialize session');
          setIsLoading(false);
        }
      } else {
        console.error('Invalid response format:', response);
        setError('Invalid response from server');
        setIsLoading(false);
      }
    } catch (err: any) {
      console.error('Login error:', err);
      if (err.code === 'ERR_NETWORK') {
        setError('Cannot connect to server. Please ensure the backend is running.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.message) {
        setError(err.message);
      } else {
        setError('Invalid username or password');
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-900 flex flex-col items-center justify-center p-4">
      {/* Logo section */}
      <div className="mb-8 flex items-center gap-4">
        <OracleLogo />
      </div>

      {/* Login card */}
      <div className="w-full max-w-md bg-dark-800 rounded-lg border border-dark-700 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Enterprise Knowledge Chat</h1>
          <p className="text-dark-300 text-sm">
            AI-powered document analysis platform
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-900/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <div>
            <label
              htmlFor="username"
              className="block text-sm font-medium text-dark-200 mb-2"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red focus:border-transparent transition-all"
              placeholder="Enter your username"
              required
              autoComplete="username"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-dark-200 mb-2"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red focus:border-transparent transition-all"
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-oracle-red hover:bg-oracle-red-dark text-white font-semibold rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

      </div>

      {/* Tech stack section */}
      <div className="mt-8 text-center">
        <p className="text-dark-300 text-sm mb-3">AI-Powered Document Analysis</p>
        <div className="flex items-center justify-center gap-3">
          <span className="px-4 py-1.5 rounded-md border border-oracle-red/50 text-oracle-red text-sm font-medium">
            OKE
          </span>
          <span className="px-4 py-1.5 rounded-md border border-oracle-red/50 text-oracle-red text-sm font-medium">
            OCI GenAI
          </span>
        </div>
      </div>

      <p className="mt-6 text-dark-500 text-xs">
        Powered by Oracle Cloud Infrastructure
      </p>
    </div>
  );
};

export default Login;
