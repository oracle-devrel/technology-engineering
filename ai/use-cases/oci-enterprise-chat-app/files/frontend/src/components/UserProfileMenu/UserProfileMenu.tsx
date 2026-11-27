import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import {
  DirectoryConfiguration,
  DirectoryConfigurationUpdate,
  DirectoryGroupMapping,
  User,
} from '../../types';

interface UserProfilePageProps {
  user: User;
  onBack: () => void;
  onLogout: () => void;
  onUserUpdate: (user: User) => void;
}

interface AlertProps {
  type: 'success' | 'error';
  message: string;
  onClose: () => void;
}

interface DirectoryFormState extends Omit<DirectoryConfigurationUpdate, 'client_secret'> {
  client_secret: string;
}

const emptyDirectoryForm: DirectoryFormState = {
  tenant_id: '',
  client_id: '',
  redirect_uri: '',
  client_secret: '',
  group_sync_enabled: false,
  group_mappings: [],
};

const configurationToDirectoryForm = (
  configuration: DirectoryConfiguration
): DirectoryFormState => ({
  tenant_id: configuration.tenant_id || '',
  client_id: configuration.client_id || '',
  redirect_uri: configuration.redirect_uri || '',
  client_secret: '',
  group_sync_enabled: configuration.group_sync_enabled,
  group_mappings: configuration.group_mappings,
});

const Alert: React.FC<AlertProps> = ({ type, message, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed top-20 right-6 z-50 animate-slide-in">
      <div
        className={`flex items-center gap-3 px-5 py-3 rounded-lg border shadow-lg ${
          type === 'success'
            ? 'bg-green-900/80 border-green-500/50 text-green-300'
            : 'bg-red-900/80 border-red-500/50 text-red-300'
        }`}
      >
        {type === 'success' ? (
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        )}
        <span className="text-sm font-medium">{message}</span>
        <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100 transition-opacity">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

const UserProfilePage: React.FC<UserProfilePageProps> = ({
  user,
  onBack,
  onLogout,
  onUserUpdate,
}) => {
  const [fullName, setFullName] = useState(user.full_name);
  const [email, setEmail] = useState(user.email);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');

  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // Microsoft Entra ID / Active Directory configuration state
  const [directoryConfiguration, setDirectoryConfiguration] = useState<DirectoryConfiguration | null>(null);
  const [directoryForm, setDirectoryForm] = useState<DirectoryFormState>(emptyDirectoryForm);
  const [isDirectoryLoading, setIsDirectoryLoading] = useState(true);
  const [isDirectoryFormOpen, setIsDirectoryFormOpen] = useState(false);
  const [isSavingDirectory, setIsSavingDirectory] = useState(false);
  const [isTestingDirectory, setIsTestingDirectory] = useState(false);

  // Alert state
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    setFullName(user.full_name);
    setEmail(user.email);
  }, [user]);

  useEffect(() => {
    const loadDirectoryConfiguration = async () => {
      try {
        const configuration = await api.getDirectoryConfiguration();
        setDirectoryConfiguration(configuration);
        setDirectoryForm(configurationToDirectoryForm(configuration));
      } catch {
        setAlert({ type: 'error', message: 'Unable to load Active Directory settings.' });
      } finally {
        setIsDirectoryLoading(false);
      }
    };

    void loadDirectoryConfiguration();
  }, []);

  const handleSaveProfile = async () => {
    setIsSaving(true);
    setSaveMessage('');
    try {
      const updated = await api.updateProfile({ full_name: fullName, email });
      onUserUpdate(updated);
      setSaveMessage('Profile saved successfully');
      setTimeout(() => setSaveMessage(''), 3000);
    } catch {
      setSaveMessage('Failed to save profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      setAlert({ type: 'error', message: 'New passwords do not match.' });
      return;
    }
    if (newPassword.length < 6) {
      setAlert({ type: 'error', message: 'New password must be at least 6 characters.' });
      return;
    }
    setIsChangingPassword(true);
    try {
      await api.changePassword({ current_password: currentPassword, new_password: newPassword });
      setAlert({ type: 'success', message: 'Password changed successfully!' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Failed to change password.';
      setAlert({ type: 'error', message });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleDirectorySave = async () => {
    if (directoryForm.group_sync_enabled && directoryForm.group_mappings.length === 0) {
      setAlert({ type: 'error', message: 'Add at least one group mapping when group sync is enabled.' });
      return;
    }

    setIsSavingDirectory(true);
    try {
      const payload: DirectoryConfigurationUpdate = {
        tenant_id: directoryForm.tenant_id,
        client_id: directoryForm.client_id,
        redirect_uri: directoryForm.redirect_uri,
        group_sync_enabled: directoryForm.group_sync_enabled,
        group_mappings: directoryForm.group_mappings,
        ...(directoryForm.client_secret ? { client_secret: directoryForm.client_secret } : {}),
      };
      const configuration = await api.updateDirectoryConfiguration(payload);
      setDirectoryConfiguration(configuration);
      setDirectoryForm(configurationToDirectoryForm(configuration));
      setAlert({ type: 'success', message: 'Active Directory settings saved.' });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Unable to save Active Directory settings.';
      setAlert({ type: 'error', message });
    } finally {
      setIsSavingDirectory(false);
    }
  };

  const handleDirectoryTest = async () => {
    setIsTestingDirectory(true);
    try {
      const result = await api.testDirectoryConnection();
      setAlert({
        type: result.status === 'connected' ? 'success' : 'error',
        message: result.message,
      });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'Unable to test Active Directory connectivity.';
      setAlert({ type: 'error', message });
    } finally {
      setIsTestingDirectory(false);
    }
  };

  const updateDirectoryMapping = (
    index: number,
    field: keyof DirectoryGroupMapping,
    value: string
  ) => {
    setDirectoryForm((current) => ({
      ...current,
      group_mappings: current.group_mappings.map((mapping, mappingIndex) =>
        mappingIndex === index ? { ...mapping, [field]: value } : mapping
      ),
    }));
  };

  const addDirectoryMapping = () => {
    setDirectoryForm((current) => ({
      ...current,
      group_mappings: [...current.group_mappings, { group_id: '', role: 'viewer' }],
    }));
  };

  const removeDirectoryMapping = (index: number) => {
    setDirectoryForm((current) => ({
      ...current,
      group_mappings: current.group_mappings.filter((_, mappingIndex) => mappingIndex !== index),
    }));
  };

  const passwordFormValid = currentPassword.length > 0 && newPassword.length >= 6 && confirmPassword.length > 0;
  const profileDirty = fullName !== user.full_name || email !== user.email;

  const initials = user.full_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className="flex-1 overflow-auto bg-dark-900 p-6">
      {/* Alert popup */}
      {alert && (
        <Alert
          type={alert.type}
          message={alert.message}
          onClose={() => setAlert(null)}
        />
      )}

      {/* Back button */}
      <button
        onClick={onBack}
        className="flex items-center gap-2 text-dark-400 hover:text-white mb-6 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
        <span className="text-sm">Back to Dashboard</span>
      </button>

      <div className="max-w-2xl mx-auto space-y-6">
        {/* Page title */}
        <div>
          <h1 className="text-2xl font-bold text-white">Profile Settings</h1>
          <p className="text-dark-400 text-sm mt-1">Manage your account, identity, and access settings</p>
        </div>

        {/* Profile Details card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Profile Details</h2>
          <p className="text-dark-400 text-sm mb-5">Your account information</p>

          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-oracle-red/20 text-oracle-red flex items-center justify-center text-2xl font-bold">
              {initials}
            </div>
            <div>
              <p className="text-white text-lg font-medium">{user.full_name}</p>
              <p className="text-dark-400 text-sm">@{user.username}</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">User ID</p>
              <p className="text-sm text-dark-200 font-mono">{user.username}</p>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Email</p>
              <p className="text-sm text-dark-200">{user.email}</p>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Account Status</p>
              <span className={`inline-flex items-center gap-1.5 text-sm ${user.is_active ? 'text-green-400' : 'text-red-400'}`}>
                <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                {user.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Member Since</p>
              <p className="text-sm text-dark-200">
                {new Date(user.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Edit Profile card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Edit Profile</h2>
          <p className="text-dark-400 text-sm mb-5">Update your name and email</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
              />
            </div>
            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleSaveProfile}
                disabled={!profileDirty || isSaving}
                className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
              {saveMessage && (
                <span className={`text-sm ${saveMessage.includes('success') ? 'text-green-400' : 'text-red-400'}`}>
                  {saveMessage}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Reset Password card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Reset Password</h2>
          <p className="text-dark-400 text-sm mb-5">Change your account password</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Current Password</label>
              <div className="relative">
                <input
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  className="w-full px-3 py-2 pr-10 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200 transition-colors"
                >
                  {showCurrentPassword ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L6.59 6.59m7.532 7.532l3.29 3.29M3 3l18 18" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">New Password</label>
              <div className="relative">
                <input
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password (min 6 characters)"
                  className="w-full px-3 py-2 pr-10 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200 transition-colors"
                >
                  {showNewPassword ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L6.59 6.59m7.532 7.532l3.29 3.29M3 3l18 18" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {newPassword.length > 0 && newPassword.length < 6 && (
                <p className="text-xs text-red-400 mt-1">Password must be at least 6 characters</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Confirm New Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
              />
              {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                <p className="text-xs text-red-400 mt-1">Passwords do not match</p>
              )}
            </div>
            <div className="pt-2">
              <button
                onClick={handleChangePassword}
                disabled={!passwordFormValid || isChangingPassword}
                className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isChangingPassword ? 'Changing...' : 'Change Password'}
              </button>
            </div>
          </div>
        </div>

        {/* OCI Federation card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">OCI Federation</h2>
          <p className="text-dark-400 text-sm mb-5">Link your account with Oracle Cloud Infrastructure identity</p>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Tenancy</p>
                <p className="text-sm text-dark-200">OCI AI Accelerator</p>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Federation Status</p>
                <span className="inline-flex items-center gap-1.5 text-sm text-amber-400">
                  <span className="w-2 h-2 rounded-full bg-amber-400" />
                  Not Configured
                </span>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Identity Provider</p>
                <p className="text-sm text-dark-200">OCI IAM</p>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Region</p>
                <p className="text-sm text-dark-200">us-chicago-1</p>
              </div>
            </div>
            <div className="pt-2">
              <button
                disabled
                className="px-4 py-2 bg-dark-700 text-dark-400 text-sm font-medium rounded-md border border-dark-600 cursor-not-allowed"
              >
                Configure Federation
              </button>
              <p className="text-xs text-dark-500 mt-2">Contact your administrator to set up OCI federation</p>
            </div>
          </div>
        </div>

        {/* Active Directory card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Active Directory</h2>
          <p className="text-dark-400 text-sm mb-5">Microsoft Entra ID OIDC settings and group-to-role mappings</p>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Directory Type</p>
                <p className="text-sm text-dark-200">Microsoft Entra ID</p>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Directory Status</p>
                <span className={`inline-flex items-center gap-1.5 text-sm ${directoryConfiguration?.is_configured ? 'text-green-400' : 'text-amber-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${directoryConfiguration?.is_configured ? 'bg-green-400' : 'bg-amber-400'}`} />
                  {isDirectoryLoading ? 'Loading...' : directoryConfiguration?.is_configured ? 'Configured' : 'Not Configured'}
                </span>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Protocol</p>
                <p className="text-sm text-dark-200">OpenID Connect (OIDC)</p>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Group Mappings</p>
                <span className={`inline-flex items-center gap-1.5 text-sm ${directoryConfiguration?.group_sync_enabled ? 'text-green-400' : 'text-dark-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${directoryConfiguration?.group_sync_enabled ? 'bg-green-400' : 'bg-dark-500'}`} />
                  {directoryConfiguration?.group_sync_enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
            <div className="pt-2">
              {user.is_admin ? (
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    type="button"
                    onClick={() => setIsDirectoryFormOpen((isOpen) => !isOpen)}
                    disabled={isDirectoryLoading}
                    className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isDirectoryFormOpen ? 'Close Configuration' : 'Configure Directory'}
                  </button>
                  <button
                    type="button"
                    onClick={handleDirectoryTest}
                    disabled={!directoryConfiguration?.is_configured || isTestingDirectory}
                    className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 hover:text-white text-sm font-medium rounded-md border border-dark-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isTestingDirectory ? 'Testing...' : 'Test Connection'}
                  </button>
                </div>
              ) : (
                <p className="text-xs text-dark-500">Contact your administrator to set up Active Directory integration.</p>
              )}
            </div>

            {user.is_admin && isDirectoryFormOpen && (
              <div className="border-t border-dark-700 pt-5 space-y-4">
                <p className="text-sm text-dark-300">Register the redirect URI in Microsoft Entra ID, then enter the application details below.</p>
                <div className="grid grid-cols-1 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1.5">Directory (tenant) ID</label>
                    <input
                      type="text"
                      value={directoryForm.tenant_id}
                      onChange={(event) => setDirectoryForm((current) => ({ ...current, tenant_id: event.target.value }))}
                      placeholder="contoso.onmicrosoft.com or tenant GUID"
                      className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1.5">Application (client) ID</label>
                    <input
                      type="text"
                      value={directoryForm.client_id}
                      onChange={(event) => setDirectoryForm((current) => ({ ...current, client_id: event.target.value }))}
                      placeholder="Application client ID"
                      className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1.5">Redirect URI</label>
                    <input
                      type="url"
                      value={directoryForm.redirect_uri}
                      onChange={(event) => setDirectoryForm((current) => ({ ...current, redirect_uri: event.target.value }))}
                      placeholder="https://app.example.com/auth/callback"
                      className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-dark-300 mb-1.5">Client Secret</label>
                    <input
                      type="password"
                      value={directoryForm.client_secret}
                      onChange={(event) => setDirectoryForm((current) => ({ ...current, client_secret: event.target.value }))}
                      placeholder={directoryConfiguration?.client_secret_configured ? 'Configured — enter a value only to rotate it' : 'Optional for public-client PKCE'}
                      className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                    />
                    <p className="text-xs text-dark-500 mt-1.5">The secret is write-only and is never sent back to the browser.</p>
                  </div>
                </div>

                <label className="flex items-center gap-2 text-sm text-dark-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={directoryForm.group_sync_enabled}
                    onChange={(event) => setDirectoryForm((current) => ({ ...current, group_sync_enabled: event.target.checked }))}
                    className="rounded border-dark-500 bg-dark-700 text-oracle-red focus:ring-oracle-red/50"
                  />
                  Enable group-to-role mappings
                </label>

                {directoryForm.group_sync_enabled && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-dark-300">Group mappings</p>
                      <button type="button" onClick={addDirectoryMapping} className="text-sm text-oracle-red hover:text-red-300 transition-colors">Add group</button>
                    </div>
                    {directoryForm.group_mappings.map((mapping, index) => (
                      <div className="grid grid-cols-[1fr_130px_auto] gap-2" key={`${mapping.group_id}-${index}`}>
                        <input
                          type="text"
                          value={mapping.group_id}
                          onChange={(event) => updateDirectoryMapping(index, 'group_id', event.target.value)}
                          placeholder="Entra group object ID"
                          className="min-w-0 px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                        />
                        <select
                          value={mapping.role}
                          onChange={(event) => updateDirectoryMapping(index, 'role', event.target.value)}
                          className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
                        >
                          <option value="viewer">Viewer</option>
                          <option value="analyst">Analyst</option>
                          <option value="admin">Administrator</option>
                        </select>
                        <button type="button" onClick={() => removeDirectoryMapping(index)} className="px-2 text-sm text-dark-400 hover:text-red-300 transition-colors">Remove</button>
                      </div>
                    ))}
                  </div>
                )}

                <div className="flex flex-wrap items-center gap-3 pt-1">
                  <button
                    type="button"
                    onClick={handleDirectorySave}
                    disabled={isSavingDirectory || !directoryForm.tenant_id || !directoryForm.client_id || !directoryForm.redirect_uri}
                    className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {isSavingDirectory ? 'Saving...' : 'Save Directory Settings'}
                  </button>
                  <p className="text-xs text-dark-500">Runtime changes reset when the backend restarts; use ENTRA_* deployment secrets for persistent configuration.</p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Session / Logout card */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Session</h2>
          <p className="text-dark-400 text-sm mb-4">Logged in as <span className="text-dark-200">{user.username}</span></p>
          <button
            onClick={onLogout}
            className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white text-sm font-medium rounded-md border border-dark-600 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserProfilePage;
