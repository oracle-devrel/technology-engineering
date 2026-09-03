import { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  Route,
  Zap,
  BarChart3,
  HelpCircle,
  Sun,
  Moon,
  ExternalLink,
  BookOpen,
  Info,
  LogOut,
  User,
  Layers,
  Database,
  Cloud,
  Cpu,
  MapPin,
  Truck,
  GitBranch,
  Box,
  ArrowRight,
  CheckCircle2,
  Plane,
} from 'lucide-react';
import { clsx } from 'clsx';
import { Dashboard } from '@/components/Dashboard';
import { AdminPage } from '@/components/Admin';
import { LoginScreen } from '@/components/Auth';
import { AirTrafficDashboard } from '@/components/AirTraffic';
import { Toast } from '@/components/shared/Toast';
import { Modal } from '@/components/shared/Modal';
import { useAppStore, useConfigStore } from '@/store';

// Auth storage key
const AUTH_KEY = 'cuopt_auth';

type AppMode = 'dashboard' | 'airtraffic' | 'admin';

interface NavItem {
  id: AppMode;
  label: string;
  icon: React.ReactNode;
  description: string;
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Route Optimizer',
    icon: <LayoutDashboard className="w-5 h-5" />,
    description: 'Full optimization dashboard',
  },
  {
    id: 'airtraffic',
    label: 'Air Traffic',
    icon: <Plane className="w-5 h-5" />,
    description: 'Live aircraft visualization',
  },
  {
    id: 'admin',
    label: 'Configuration',
    icon: <Settings className="w-5 h-5" />,
    description: 'Regional & scenario settings',
  },
];

type HelpTab = 'about' | 'quickstart' | 'docs';

export default function App() {
  const [mode, setMode] = useState<AppMode>('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [helpTab, setHelpTab] = useState<HelpTab>('about');
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const { toasts, removeToast, mapTheme, toggleMapTheme } = useAppStore();
  const { config } = useConfigStore();

  // Check for existing auth on mount
  useEffect(() => {
    const savedAuth = localStorage.getItem(AUTH_KEY);
    if (savedAuth) {
      try {
        const authData = JSON.parse(savedAuth);
        if (authData.username && authData.timestamp) {
          // Check if session is less than 24 hours old
          const sessionAge = Date.now() - authData.timestamp;
          const maxAge = 24 * 60 * 60 * 1000; // 24 hours
          if (sessionAge < maxAge) {
            setIsAuthenticated(true);
            setCurrentUser(authData.username);
          } else {
            // Session expired
            localStorage.removeItem(AUTH_KEY);
          }
        }
      } catch {
        localStorage.removeItem(AUTH_KEY);
      }
    }
  }, []);

  useEffect(() => {
    const handleModeSwitch = (event: Event) => {
      const customEvent = event as CustomEvent<{ mode?: AppMode }>;
      const nextMode = customEvent.detail?.mode;
      if (nextMode === 'dashboard' || nextMode === 'airtraffic' || nextMode === 'admin') {
        setMode(nextMode);
      }
    };

    window.addEventListener('app:mode', handleModeSwitch as EventListener);
    return () => {
      window.removeEventListener('app:mode', handleModeSwitch as EventListener);
    };
  }, []);

  // Handle login
  const handleLogin = (username: string) => {
    const authData = {
      username,
      timestamp: Date.now(),
    };
    localStorage.setItem(AUTH_KEY, JSON.stringify(authData));
    setIsAuthenticated(true);
    setCurrentUser(username);
  };

  // Handle logout - clears session and shows login screen
  const handleLogout = () => {
    localStorage.removeItem(AUTH_KEY);
    sessionStorage.clear();
    setIsAuthenticated(false);
    setCurrentUser(null);
    setShowLogoutConfirm(false);
    setShowSettings(false);
  };

  // Show login screen if not authenticated
  if (!isAuthenticated) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <div className="flex h-screen bg-dark-bg text-white overflow-hidden" style={{ minHeight: '100vh' }}>
      {/* Sidebar */}
      <aside
        className={clsx(
          'flex flex-col border-r border-dark-border bg-dark-card transition-all duration-300',
          sidebarCollapsed ? 'w-16' : 'w-64'
        )}
      >
        {/* Logo - OCI Branded */}
        <div className="h-16 flex items-center gap-3 px-4 border-b border-dark-border">
          <div className="w-8 h-8 rounded-lg bg-oracle-red flex items-center justify-center shrink-0">
            <Route className="w-5 h-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="overflow-hidden">
              <h1 className="font-bold text-white text-sm whitespace-nowrap">cuOPT</h1>
              <p className="text-xs text-gray-500 whitespace-nowrap">Route Optimizer</p>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setMode(item.id)}
              className={clsx(
                'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all',
                mode === item.id
                  ? 'bg-oracle-red/10 text-oracle-red border border-oracle-red/30'
                  : 'text-gray-400 hover:bg-dark-hover hover:text-white'
              )}
            >
              {item.icon}
              {!sidebarCollapsed && (
                <div className="text-left overflow-hidden">
                  <div className="text-sm font-medium">{item.label}</div>
                  <div className="text-xs text-gray-500 truncate">
                    {item.description}
                  </div>
                </div>
              )}
            </button>
          ))}
        </nav>

        {/* Quick Stats */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-dark-border space-y-3">
            <div className="text-xs font-medium text-gray-500 uppercase">
              Quick Stats
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-dark-bg rounded-lg p-2">
                <div className="flex items-center gap-1 text-oci-blue mb-1">
                  <Zap className="w-3 h-3" />
                  <span className="text-xs">OKE</span>
                </div>
                <div className="text-sm font-semibold">GPU</div>
              </div>
              <div className="bg-dark-bg rounded-lg p-2">
                <div className="flex items-center gap-1 text-oracle-red mb-1">
                  <BarChart3 className="w-3 h-3" />
                  <span className="text-xs">NIM</span>
                </div>
                <div className="text-sm font-semibold">cuOPT</div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="p-3 border-t border-dark-border">
          <div className="flex items-center justify-between">
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>
            {!sidebarCollapsed && (
              <div className="flex gap-1">
                <button
                  onClick={() => setShowHelp(true)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
                  title="Help & Documentation"
                >
                  <HelpCircle className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowSettings(true)}
                  className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
                  title="Settings"
                >
                  <Settings className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-dark-border bg-dark-card">
          <div>
            <h2 className="text-lg font-semibold">
              {mode === 'dashboard' && 'Route Optimizer Dashboard'}
              {mode === 'airtraffic' && 'Live Air Traffic'}
              {mode === 'admin' && 'Configuration Settings'}
            </h2>
            <p className="text-xs text-gray-500">
              {mode === 'dashboard' && 'Configure and run route optimization with NVIDIA cuOPT'}
              {mode === 'airtraffic' && 'Monitor live aircraft and regional traffic patterns'}
              {mode === 'admin' && `Region: ${config.countryCode} | Scenario: ${config.activeScenario}`}
            </p>
          </div>
          <div className="flex items-center gap-4">
            {/* Status Indicator */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-dark-bg rounded-full">
              <div className="w-2 h-2 bg-oci-green rounded-full animate-pulse" />
              <span className="text-xs text-gray-400">OCI Ready</span>
            </div>
            {/* Branding - NVIDIA cuOPT powered by OCI */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-nvidia-green font-semibold">NVIDIA cuOPT</span>
              <span className="text-gray-500">powered by</span>
              <span style={{ color: '#C74634' }} className="font-semibold">OCI</span>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {mode === 'dashboard' && <Dashboard />}
          {mode === 'airtraffic' && <AirTrafficDashboard />}
          {mode === 'admin' && <AdminPage />}
        </div>
      </main>

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onClose={removeToast} />
        ))}
      </div>

      {/* Settings Modal */}
      <Modal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        title="Settings"
        size="md"
      >
        <div className="space-y-6">
          {/* User Session */}
          <div className="flex items-center justify-between p-3 bg-dark-bg rounded-lg">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-oracle-red/20 flex items-center justify-center">
                <User className="w-5 h-5 text-oracle-red" />
              </div>
              <div>
                <div className="font-medium text-white">{currentUser || 'User'}</div>
                <div className="text-xs text-gray-400">Logged in</div>
              </div>
            </div>
            <button
              onClick={() => {
                setShowSettings(false);
                setShowLogoutConfirm(true);
              }}
              className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>

          {/* Divider */}
          <div className="border-t border-dark-border" />

          {/* Map Theme */}
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-white">Map Theme</div>
              <div className="text-sm text-gray-400">Switch between dark and light map tiles</div>
            </div>
            <button
              onClick={toggleMapTheme}
              className={clsx(
                'px-4 py-2 rounded-lg flex items-center gap-2 transition-colors',
                mapTheme === 'dark'
                  ? 'bg-gray-700 text-white'
                  : 'bg-yellow-100 text-yellow-800'
              )}
            >
              {mapTheme === 'dark' ? (
                <>
                  <Moon className="w-4 h-4" />
                  Dark
                </>
              ) : (
                <>
                  <Sun className="w-4 h-4" />
                  Light
                </>
              )}
            </button>
          </div>

          {/* Divider */}
          <div className="border-t border-dark-border" />

          {/* API Configuration */}
          <div>
            <div className="font-medium text-white mb-3">API Configuration</div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                <span className="text-gray-400">cuOPT Endpoint</span>
                <span className="text-gray-300 font-mono text-xs">cuopt-2-cuopt.*.nip.io</span>
              </div>
              <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                <span className="text-gray-400">OCI GenAI</span>
                <span className="text-gray-300 font-mono text-xs">us-phoenix-1</span>
              </div>
              <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                <span className="text-gray-400">Weather API</span>
                <span className="text-gray-300 font-mono text-xs">OpenWeatherMap</span>
              </div>
            </div>
          </div>

          {/* Version Info */}
          <div className="pt-4 border-t border-dark-border text-center text-xs text-gray-500">
            OCI Route Optimizer v1.0.0 | Powered by NVIDIA cuOPT NIM
          </div>
        </div>
      </Modal>

      {/* Logout Confirmation Modal */}
      <Modal
        isOpen={showLogoutConfirm}
        onClose={() => setShowLogoutConfirm(false)}
        title="Confirm Logout"
        size="sm"
      >
        <div className="space-y-4">
          <p className="text-gray-300">
            Are you sure you want to logout? You will need to login again to access the application.
          </p>
          <div className="flex justify-end gap-3">
            <button
              onClick={() => setShowLogoutConfirm(false)}
              className="px-4 py-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </Modal>

      {/* Help Modal - Enhanced with About Section */}
      <Modal
        isOpen={showHelp}
        onClose={() => setShowHelp(false)}
        title="Route Optimizer"
        size="xl"
      >
        <div className="space-y-4">
          {/* Tab Navigation */}
          <div className="flex border-b border-dark-border">
            <button
              onClick={() => setHelpTab('about')}
              className={clsx(
                'px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2',
                helpTab === 'about'
                  ? 'text-oracle-red border-b-2 border-oracle-red'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <Info className="w-4 h-4" />
              About
            </button>
            <button
              onClick={() => setHelpTab('quickstart')}
              className={clsx(
                'px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2',
                helpTab === 'quickstart'
                  ? 'text-oracle-red border-b-2 border-oracle-red'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <Zap className="w-4 h-4" />
              Quick Start
            </button>
            <button
              onClick={() => setHelpTab('docs')}
              className={clsx(
                'px-4 py-2 text-sm font-medium transition-colors flex items-center gap-2',
                helpTab === 'docs'
                  ? 'text-oracle-red border-b-2 border-oracle-red'
                  : 'text-gray-400 hover:text-white'
              )}
            >
              <BookOpen className="w-4 h-4" />
              Documentation
            </button>
          </div>

          {/* Tab Content */}
          <div className="min-h-[400px]">
            {/* ABOUT TAB */}
            {helpTab === 'about' && (
              <div className="space-y-6">
                {/* Overview */}
                <div className="p-4 bg-gradient-to-r from-oracle-red/10 to-nvidia-green/10 rounded-xl border border-dark-border">
                  <h3 className="text-lg font-semibold text-white mb-2">Route Optimizer Dashboard</h3>
                  <p className="text-sm text-gray-300">
                    Enterprise-grade Vehicle Routing Problem (VRP) solver powered by NVIDIA cuOPT running on Oracle Cloud Infrastructure (OCI).
                    This dashboard provides real-time route optimization with traffic-aware routing, weather integration, and AI-powered insights.
                  </p>
                </div>

                {/* Quick Stats Grid */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Platform Statistics</h4>
                  <div className="grid grid-cols-4 gap-3">
                    <div className="bg-dark-bg rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-oracle-red">23</div>
                      <div className="text-xs text-gray-400">Components</div>
                    </div>
                    <div className="bg-dark-bg rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-nvidia-green">GPU</div>
                      <div className="text-xs text-gray-400">Accelerated</div>
                    </div>
                    <div className="bg-dark-bg rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-oci-blue">2</div>
                      <div className="text-xs text-gray-400">Map Providers</div>
                    </div>
                    <div className="bg-dark-bg rounded-lg p-3 text-center">
                      <div className="text-2xl font-bold text-green-400">Real-time</div>
                      <div className="text-xs text-gray-400">Traffic + Weather</div>
                    </div>
                  </div>
                </div>

                {/* Architecture Flow */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Data Flow Architecture</h4>
                  <div className="bg-dark-bg rounded-xl p-4">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 rounded-lg bg-oci-blue/20 flex items-center justify-center">
                          <Database className="w-6 h-6 text-oci-blue" />
                        </div>
                        <span className="text-gray-400">Input Data</span>
                        <span className="text-xs text-gray-500">CSV/JSON</span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-600" />
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 rounded-lg bg-oracle-red/20 flex items-center justify-center">
                          <Layers className="w-6 h-6 text-oracle-red" />
                        </div>
                        <span className="text-gray-400">InputPanel</span>
                        <span className="text-xs text-gray-500">Config</span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-600" />
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 rounded-lg bg-nvidia-green/20 flex items-center justify-center">
                          <Cpu className="w-6 h-6 text-nvidia-green" />
                        </div>
                        <span className="text-gray-400">cuOPT NIM</span>
                        <span className="text-xs text-gray-500">GPU Solver</span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-600" />
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center">
                          <MapPin className="w-6 h-6 text-green-400" />
                        </div>
                        <span className="text-gray-400">RouteMap</span>
                        <span className="text-xs text-gray-500">Visualization</span>
                      </div>
                      <ArrowRight className="w-5 h-5 text-gray-600" />
                      <div className="flex flex-col items-center gap-2">
                        <div className="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center">
                          <Truck className="w-6 h-6 text-purple-400" />
                        </div>
                        <span className="text-gray-400">ResultsPanel</span>
                        <span className="text-xs text-gray-500">Routes</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Component Breakdown */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Component Architecture</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    {/* Core Components */}
                    <div className="bg-dark-bg rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <Box className="w-4 h-4 text-oracle-red" />
                        <span className="font-medium text-white">Dashboard Components</span>
                      </div>
                      <ul className="space-y-1 text-gray-400 text-xs">
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>Dashboard.tsx - Main container</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>InputPanel.tsx - Stops & fleet config</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>ResultsPanel.tsx - Route details</span>
                        </li>
                      </ul>
                    </div>

                    {/* Map Components */}
                    <div className="bg-dark-bg rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <MapPin className="w-4 h-4 text-green-400" />
                        <span className="font-medium text-white">Map Components</span>
                      </div>
                      <ul className="space-y-1 text-gray-400 text-xs">
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>GoogleRouteMap.tsx - Traffic & Directions</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>RouteMap.tsx - Leaflet/OSM fallback</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>Weather integration overlay</span>
                        </li>
                      </ul>
                    </div>

                    {/* AI Components */}
                    <div className="bg-dark-bg rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <MessageSquare className="w-4 h-4 text-oci-blue" />
                        <span className="font-medium text-white">AI Chat Components</span>
                      </div>
                      <ul className="space-y-1 text-gray-400 text-xs">
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>ChatInterface.tsx - NLP interface</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>ChatMessage.tsx - Message rendering</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>ChatInput.tsx - User input</span>
                        </li>
                      </ul>
                    </div>

                    {/* Shared Components */}
                    <div className="bg-dark-bg rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-2">
                        <GitBranch className="w-4 h-4 text-purple-400" />
                        <span className="font-medium text-white">Shared UI Components</span>
                      </div>
                      <ul className="space-y-1 text-gray-400 text-xs">
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>Card, Button, Modal, Toast</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>Input, Select, Slider, Toggle</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-400" />
                          <span>Badge, Skeleton, MetricCard</span>
                        </li>
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Technology Stack */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Technology Stack</h4>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-3 py-1.5 bg-blue-500/20 text-blue-400 rounded-full text-xs font-medium">React 18</span>
                    <span className="px-3 py-1.5 bg-blue-600/20 text-blue-300 rounded-full text-xs font-medium">TypeScript</span>
                    <span className="px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-full text-xs font-medium">Vite</span>
                    <span className="px-3 py-1.5 bg-cyan-500/20 text-cyan-400 rounded-full text-xs font-medium">Tailwind CSS</span>
                    <span className="px-3 py-1.5 bg-yellow-500/20 text-yellow-400 rounded-full text-xs font-medium">Zustand</span>
                    <span className="px-3 py-1.5 bg-green-500/20 text-green-400 rounded-full text-xs font-medium">Leaflet</span>
                    <span className="px-3 py-1.5 bg-red-500/20 text-red-400 rounded-full text-xs font-medium">Google Maps API</span>
                    <span className="px-3 py-1.5 bg-nvidia-green/20 text-nvidia-green rounded-full text-xs font-medium">NVIDIA cuOPT</span>
                    <span className="px-3 py-1.5 bg-oracle-red/20 text-oracle-red rounded-full text-xs font-medium">OCI GenAI</span>
                  </div>
                </div>
              </div>
            )}

            {/* QUICK START TAB */}
            {helpTab === 'quickstart' && (
              <div className="space-y-6">
                {/* Workflow Steps */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Optimization Workflow</h4>
                  <div className="space-y-3">
                    <div className="flex gap-4 p-3 bg-dark-bg rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-oracle-red flex items-center justify-center text-white font-bold shrink-0">1</div>
                      <div>
                        <div className="font-medium text-white">Load Stops</div>
                        <div className="text-sm text-gray-400">Use "Load Benchmark Scenario" or upload a CSV file with lat, lng, demand columns. Supports EV charging stations and custom locations.</div>
                      </div>
                    </div>
                    <div className="flex gap-4 p-3 bg-dark-bg rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-oracle-red flex items-center justify-center text-white font-bold shrink-0">2</div>
                      <div>
                        <div className="font-medium text-white">Configure Fleet</div>
                        <div className="text-sm text-gray-400">Set number of vehicles, capacity per vehicle, and enable optional features like home-start mode or parallel processing.</div>
                      </div>
                    </div>
                    <div className="flex gap-4 p-3 bg-dark-bg rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-oracle-red flex items-center justify-center text-white font-bold shrink-0">3</div>
                      <div>
                        <div className="font-medium text-white">Run Optimization</div>
                        <div className="text-sm text-gray-400">Click "Run Optimization" for single-cluster solving, or "Run Parallel" to split stops into geographic clusters for faster processing.</div>
                      </div>
                    </div>
                    <div className="flex gap-4 p-3 bg-dark-bg rounded-lg">
                      <div className="w-8 h-8 rounded-full bg-oracle-red flex items-center justify-center text-white font-bold shrink-0">4</div>
                      <div>
                        <div className="font-medium text-white">Review Results</div>
                        <div className="text-sm text-gray-400">View optimized routes on the map with traffic overlay. Check weather impact, estimated times, and vehicle assignments in the results panel.</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Keyboard Shortcuts */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Keyboard Shortcuts</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">Toggle Sidebar</span>
                      <kbd className="px-2 py-0.5 bg-dark-card rounded text-xs">Ctrl + B</kbd>
                    </div>
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">Switch Mode</span>
                      <kbd className="px-2 py-0.5 bg-dark-card rounded text-xs">Ctrl + M</kbd>
                    </div>
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">Run Optimization</span>
                      <kbd className="px-2 py-0.5 bg-dark-card rounded text-xs">Ctrl + Enter</kbd>
                    </div>
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">Reset</span>
                      <kbd className="px-2 py-0.5 bg-dark-card rounded text-xs">Ctrl + R</kbd>
                    </div>
                  </div>
                </div>

                {/* Map Features */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">Map Features</h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="p-3 bg-dark-bg rounded-lg">
                      <div className="font-medium text-white mb-1">Google Maps</div>
                      <ul className="text-gray-400 text-xs space-y-1">
                        <li>- Real-time traffic layer</li>
                        <li>- Directions API routing</li>
                        <li>- Weather-adjusted ETAs</li>
                        <li>- Multiple map styles</li>
                      </ul>
                    </div>
                    <div className="p-3 bg-dark-bg rounded-lg">
                      <div className="font-medium text-white mb-1">Leaflet (OSM)</div>
                      <ul className="text-gray-400 text-xs space-y-1">
                        <li>- Free, no API key needed</li>
                        <li>- Dark/Light themes</li>
                        <li>- Route polylines</li>
                        <li>- Stop markers with info</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* DOCUMENTATION TAB */}
            {helpTab === 'docs' && (
              <div className="space-y-6">
                {/* API Endpoints */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">API Endpoints</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">cuOPT Solver</span>
                      <span className="text-gray-300 font-mono text-xs">POST /cuopt/solve</span>
                    </div>
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">Weather Data</span>
                      <span className="text-gray-300 font-mono text-xs">GET /weather/:lat/:lng</span>
                    </div>
                    <div className="flex justify-between py-2 px-3 bg-dark-bg rounded-lg">
                      <span className="text-gray-400">GenAI Chat</span>
                      <span className="text-gray-300 font-mono text-xs">POST /genai/chat</span>
                    </div>
                  </div>
                </div>

                {/* Documentation Links */}
                <div>
                  <h4 className="text-sm font-medium text-gray-400 uppercase mb-3">External Documentation</h4>
                  <div className="space-y-2">
                    <a
                      href="https://docs.oracle.com/en-us/iaas/Content/home.htm"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between py-2 px-3 bg-dark-bg rounded-lg hover:bg-dark-hover transition-colors group"
                    >
                      <div className="flex items-center gap-2">
                        <Cloud className="w-4 h-4 text-oracle-red" />
                        <span className="text-gray-300 group-hover:text-white">Oracle Cloud Infrastructure</span>
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-oracle-red" />
                    </a>
                    <a
                      href="https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between py-2 px-3 bg-dark-bg rounded-lg hover:bg-dark-hover transition-colors group"
                    >
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4 text-oci-blue" />
                        <span className="text-gray-300 group-hover:text-white">OCI Generative AI</span>
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-oci-blue" />
                    </a>
                    <a
                      href="https://docs.nvidia.com/cuopt/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between py-2 px-3 bg-dark-bg rounded-lg hover:bg-dark-hover transition-colors group"
                    >
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-nvidia-green" />
                        <span className="text-gray-300 group-hover:text-white">NVIDIA cuOPT Documentation</span>
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-nvidia-green" />
                    </a>
                    <a
                      href="https://developers.google.com/maps/documentation"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between py-2 px-3 bg-dark-bg rounded-lg hover:bg-dark-hover transition-colors group"
                    >
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-red-400" />
                        <span className="text-gray-300 group-hover:text-white">Google Maps Platform</span>
                      </div>
                      <ExternalLink className="w-4 h-4 text-gray-500 group-hover:text-red-400" />
                    </a>
                  </div>
                </div>

                {/* Support */}
                <div className="p-4 bg-gradient-to-r from-oracle-red/10 to-oci-blue/10 rounded-xl border border-dark-border">
                  <div className="font-medium text-white mb-2">Need Help?</div>
                  <p className="text-sm text-gray-400">
                    For technical support, feature requests, or bug reports, contact the Oracle AI CoE team.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="pt-4 border-t border-dark-border text-center text-xs text-gray-500">
            OCI Route Optimizer v1.0.0 | NVIDIA cuOPT NIM | Oracle Cloud Infrastructure
          </div>
        </div>
      </Modal>
    </div>
  );
}
