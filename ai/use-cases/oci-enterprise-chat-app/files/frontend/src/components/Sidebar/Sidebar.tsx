import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  FolderOpen,
  MessageSquare,
  FileText,
  Settings,
  HelpCircle,
  ChevronRight,
  Database,
  GitBranch,
  BookOpen,
  Shield,
  BarChart3,
  TrendingUp,
} from 'lucide-react';

const navItems = [
  {
    section: 'Main',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/projects', icon: FolderOpen, label: 'Projects' },
      { to: '/documents', icon: FileText, label: 'All Documents' },
      { to: '/research', icon: BookOpen, label: 'Research' },
      { to: '/compliance', icon: Shield, label: 'Compliance' },
      { to: '/batch', icon: Database, label: 'Batch Processing' },
      { to: '/workflows', icon: GitBranch, label: 'Workflows' },
      { to: '/benchmark', icon: BarChart3, label: 'Benchmarking' },
      { to: '/impact', icon: TrendingUp, label: 'Impact & ROI' },
    ],
  },
  {
    section: 'System',
    items: [
      { to: '/settings', icon: Settings, label: 'System Settings' },
      { to: '/help', icon: HelpCircle, label: 'Help & Support' },
    ],
  },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <aside className="w-64 bg-dark-800 border-r border-dark-700 flex flex-col h-[calc(100vh-4rem)] flex-shrink-0">
      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-4">
        {navItems.map((section) => (
          <div key={section.section} className="mb-6">
            <h3 className="text-xs font-semibold text-dark-400 uppercase tracking-wider px-4 mb-2">
              {section.section}
            </h3>
            <ul className="space-y-1">
              {section.items.map((item) => {
                const Icon = item.icon;
                const isActive =
                  item.to === '/'
                    ? location.pathname === '/'
                    : location.pathname.startsWith(item.to);

                return (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                        isActive
                          ? 'text-white bg-dark-700 border-l-4 border-oracle-red'
                          : 'text-dark-200 hover:text-white hover:bg-dark-700'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span className="flex-1">{item.label}</span>
                      {isActive && (
                        <ChevronRight className="h-4 w-4 text-oracle-red" />
                      )}
                    </NavLink>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>

      {/* Bottom section */}
      <div className="p-4 border-t border-dark-700">
        <div className="bg-dark-700 rounded-xl border border-dark-600 p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-lg bg-oracle-red/20 flex items-center justify-center">
              <svg viewBox="0 0 24 24" className="h-6 w-6 text-oracle-red" fill="none" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-white">AI-Q Engine</p>
              <p className="text-xs text-dark-300">Enterprise Chat</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-xs text-dark-300">All systems operational</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
