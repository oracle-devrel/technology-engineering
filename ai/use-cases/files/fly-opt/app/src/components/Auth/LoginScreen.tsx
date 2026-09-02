import { useState } from 'react';
import { Zap, Eye, EyeOff, Cloud } from 'lucide-react';

interface LoginScreenProps {
  onLogin: (username: string) => void;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password');
      return;
    }

    setIsLoading(true);

    // Simulate authentication delay
    await new Promise(resolve => setTimeout(resolve, 800));

    // For demo: accept any non-empty credentials
    // In production, this would validate against IDCS/OAuth
    onLogin(username);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center p-4">
      {/* Background Pattern */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-5">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
        </div>
        {/* Gradient accent */}
        <div className="absolute top-0 right-0 w-1/2 h-1/2 bg-gradient-to-bl from-oracle-red/10 to-transparent" />
        <div className="absolute bottom-0 left-0 w-1/2 h-1/2 bg-gradient-to-tr from-oci-blue/10 to-transparent" />
      </div>

      <div className="relative w-full max-w-md">
        {/* OCI Logo and Title */}
        <div className="text-center mb-8">
          {/* White background with Oracle Red cloud icon */}
          <div className="inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-white mb-4 shadow-lg">
            <Cloud className="w-12 h-12" style={{ color: '#C74634' }} strokeWidth={2.5} />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">OCI Route Optimizer</h1>
          <p className="text-gray-400">Powered by Oracle Cloud Infrastructure</p>
        </div>

        {/* Login Card */}
        <div className="bg-dark-card border border-dark-border rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-oracle-red focus:border-transparent transition-all"
                placeholder="Enter your username"
                autoComplete="username"
                disabled={isLoading}
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-bg border border-dark-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-oracle-red focus:border-transparent transition-all pr-12"
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Submit Button - OCI Red */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-oracle-red hover:bg-oracle-red-hover disabled:bg-oracle-red/50 text-white font-semibold rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-oracle-red/20"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5" />
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Demo Note */}
          <div className="mt-6 pt-6 border-t border-dark-border">
            <p className="text-xs text-gray-500 text-center">
              Demo Mode: Enter any username and password to continue
            </p>
          </div>
        </div>

        {/* Technology Stack Footer */}
        <div className="mt-8 text-center">
          {/* Main branding - NVIDIA cuOPT powered by OCI */}
          <div className="mb-4">
            <span className="text-nvidia-green font-bold text-lg">NVIDIA cuOPT</span>
            <span className="text-gray-500 mx-2">powered by</span>
            <span style={{ color: '#C74634' }} className="font-bold text-lg">OCI</span>
          </div>

          <p className="text-xs text-gray-500 mb-3">
            GPU-Accelerated Route Optimization
          </p>
          <div className="flex items-center justify-center gap-3">
            <span className="px-2 py-1 bg-oracle-red/10 border border-oracle-red/30 rounded text-xs text-oracle-red">OKE</span>
            <span className="px-2 py-1 bg-oracle-red/10 border border-oracle-red/30 rounded text-xs text-oracle-red">OCI GenAI</span>
            <span className="px-2 py-1 bg-nvidia-green/10 border border-nvidia-green/30 rounded text-xs text-nvidia-green">A10G GPU</span>
          </div>
        </div>
      </div>
    </div>
  );
}
