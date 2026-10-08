import React, { useState, useRef, useEffect } from 'react';
import UploadButton from '../UploadButton/UploadButton';
import StatusIndicator from '../StatusIndicator/StatusIndicator';
import { ProcessingStatus, User } from '../../types';

interface HeaderProps {
  status: ProcessingStatus;
  onFileSelect: (file: File) => void;
  currentFileName?: string;
  showUpload?: boolean;
  user?: User;
  onNavigateProfile?: () => void;
  onLogout?: () => void;
}

const OracleLogo = () => (
  <img
    src="/oracle-logo.png"
    alt="Oracle"
    className="h-6 w-auto"
  />
);


const Header: React.FC<HeaderProps> = ({
  status,
  onFileSelect,
  currentFileName,
  showUpload = true,
  user,
  onNavigateProfile,
  onLogout,
}) => {
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showDropdown]);

  const initials = user
    ? user.full_name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '';

  return (
    <header className="h-16 bg-dark-800 border-b border-dark-700 flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Left section - Logo */}
      <div className="flex items-center gap-3">
        <OracleLogo />
        <div className="h-6 w-px bg-dark-600" />
        <span className="text-sm font-semibold text-white">AI-Q Enterprise Chat</span>
      </div>

      {/* Right section - Status and Actions */}
      <div className="flex items-center gap-4">
        {showUpload && (
          <>
            <StatusIndicator status={status} fileName={currentFileName} />
            <div className="h-6 w-px bg-dark-600" />
            <UploadButton onFileSelect={onFileSelect} disabled={status === 'uploading' || status === 'processing'} />
          </>
        )}
        {user && (
          <>
            <div className="h-6 w-px bg-dark-600" />
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-dark-700 transition-colors"
              >
                <div className="w-8 h-8 rounded-full bg-oracle-red/20 text-oracle-red flex items-center justify-center text-sm font-bold">
                  {initials}
                </div>
                <span className="text-sm text-dark-300 hidden md:block">{user.full_name}</span>
                <svg className={`w-4 h-4 text-dark-400 hidden md:block transition-transform ${showDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDropdown && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-dark-800 border border-dark-700 rounded-lg shadow-xl z-50 overflow-hidden">
                  {/* User info */}
                  <div className="px-4 py-3 border-b border-dark-700">
                    <p className="text-sm font-medium text-white truncate">{user.full_name}</p>
                    <p className="text-xs text-dark-400 truncate">{user.email}</p>
                  </div>

                  {/* Menu items */}
                  <div className="py-1">
                    {onNavigateProfile && (
                      <button
                        onClick={() => {
                          setShowDropdown(false);
                          onNavigateProfile();
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dark-200 hover:bg-dark-700 hover:text-white transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Profile Settings
                      </button>
                    )}
                    {onLogout && (
                      <button
                        onClick={() => {
                          setShowDropdown(false);
                          onLogout();
                        }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dark-200 hover:bg-dark-700 hover:text-white transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Logout
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </header>
  );
};

export default Header;
