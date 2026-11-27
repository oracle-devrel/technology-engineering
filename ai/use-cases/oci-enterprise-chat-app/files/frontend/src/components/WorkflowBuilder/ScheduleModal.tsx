import React, { useState, useEffect, useCallback } from 'react';
import { X, Clock, Calendar, Repeat, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import { WorkflowSchedule } from '../../types';

interface ScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowId: string;
  workflowName: string;
  hasChatNode: boolean;
}

type ScheduleType = 'one_time' | 'recurring';
type FrequencyPreset = 'hourly' | 'daily' | 'weekly' | 'custom';

const PRESET_CRONS: Record<Exclude<FrequencyPreset, 'custom'>, string> = {
  hourly: '0 * * * *',
  daily: '0 9 * * *',
  weekly: '0 9 * * 1',
};

function getCronDescription(cron: string): string {
  const parts = cron.trim().split(/\s+/);
  if (parts.length !== 5) return 'Invalid cron expression';

  const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;

  // Every hour at :MM
  if (hour === '*' && dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
    const min = minute === '0' ? '00' : minute;
    return `Runs every hour at :${min.padStart(2, '0')}`;
  }

  // Build day-of-week label
  const dayNames: Record<string, string> = {
    '0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday',
    '4': 'Thursday', '5': 'Friday', '6': 'Saturday', '7': 'Sunday',
  };

  // Format time
  const formatTime = (h: string, m: string): string => {
    const hourNum = parseInt(h, 10);
    if (isNaN(hourNum)) return `${h}:${m.padStart(2, '0')}`;
    const period = hourNum >= 12 ? 'PM' : 'AM';
    const displayHour = hourNum === 0 ? 12 : hourNum > 12 ? hourNum - 12 : hourNum;
    return `${displayHour}:${m.padStart(2, '0')} ${period}`;
  };

  // Every day at HH:MM
  if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*' && hour !== '*') {
    return `Runs every day at ${formatTime(hour, minute)}`;
  }

  // Specific day(s) of week
  if (dayOfMonth === '*' && month === '*' && dayOfWeek !== '*' && hour !== '*') {
    const days = dayOfWeek.split(',').map(d => dayNames[d] || d).join(', ');
    return `Runs every ${days} at ${formatTime(hour, minute)}`;
  }

  // Specific day of month
  if (dayOfMonth !== '*' && month === '*' && dayOfWeek === '*' && hour !== '*') {
    return `Runs on day ${dayOfMonth} of every month at ${formatTime(hour, minute)}`;
  }

  return `Cron: ${cron}`;
}

const ScheduleModal: React.FC<ScheduleModalProps> = ({
  isOpen,
  onClose,
  workflowId,
  workflowName,
  hasChatNode,
}) => {
  // Form state
  const [scheduleType, setScheduleType] = useState<ScheduleType>('recurring');
  const [oneTimeDate, setOneTimeDate] = useState('');
  const [oneTimeTime, setOneTimeTime] = useState('09:00');
  const [frequencyPreset, setFrequencyPreset] = useState<FrequencyPreset>('daily');
  const [cronFields, setCronFields] = useState({ minute: '0', hour: '9', dayOfMonth: '*', month: '*', dayOfWeek: '*' });
  const [inputDataJson, setInputDataJson] = useState('{}');
  const [isActive, setIsActive] = useState(true);

  // Async state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingSchedule, setExistingSchedule] = useState<WorkflowSchedule | null>(null);

  // Derived cron expression
  const cronExpression = (() => {
    if (scheduleType === 'one_time') return '';
    if (frequencyPreset !== 'custom') return PRESET_CRONS[frequencyPreset];
    return `${cronFields.minute} ${cronFields.hour} ${cronFields.dayOfMonth} ${cronFields.month} ${cronFields.dayOfWeek}`;
  })();

  // Load existing schedule on mount
  const loadSchedule = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const schedule = await api.getWorkflowSchedule(workflowId);
      setExistingSchedule(schedule);

      // Populate form from existing schedule
      setScheduleType(schedule.schedule_type);
      setIsActive(schedule.is_active);

      if (schedule.input_data) {
        setInputDataJson(JSON.stringify(schedule.input_data, null, 2));
      }

      if (schedule.schedule_type === 'one_time' && schedule.run_at) {
        const date = new Date(schedule.run_at);
        setOneTimeDate(`${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`);
        setOneTimeTime(date.toTimeString().slice(0, 5));
      }

      if (schedule.schedule_type === 'recurring' && schedule.cron_expression) {
        const cron = schedule.cron_expression;
        // Check if it matches a preset
        if (cron === PRESET_CRONS.hourly) {
          setFrequencyPreset('hourly');
        } else if (cron === PRESET_CRONS.daily) {
          setFrequencyPreset('daily');
        } else if (cron === PRESET_CRONS.weekly) {
          setFrequencyPreset('weekly');
        } else {
          setFrequencyPreset('custom');
          const parts = cron.trim().split(/\s+/);
          if (parts.length === 5) {
            setCronFields({
              minute: parts[0],
              hour: parts[1],
              dayOfMonth: parts[2],
              month: parts[3],
              dayOfWeek: parts[4],
            });
          }
        }
      }
    } catch (err: any) {
      // 404 means no schedule exists yet -- that is fine
      if (err?.response?.status !== 404) {
        setError('Failed to load existing schedule');
      }
    } finally {
      setLoading(false);
    }
  }, [workflowId]);

  useEffect(() => {
    if (isOpen) {
      loadSchedule();
    }
  }, [isOpen, loadSchedule]);

  // Save handler
  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      // Parse input data JSON
      let inputData: Record<string, any> | undefined;
      if (inputDataJson.trim()) {
        try {
          inputData = JSON.parse(inputDataJson);
          if (!inputData || Array.isArray(inputData) || typeof inputData !== 'object') throw new Error('Expected an object');
        } catch {
          setError('Invalid JSON in input data field');
          setSaving(false);
          return;
        }
      }

      const payload: {
        schedule_type: 'one_time' | 'recurring';
        cron_expression?: string;
        run_at?: string;
        input_data?: Record<string, any>;
        is_active?: boolean;
      } = {
        schedule_type: scheduleType,
        is_active: isActive,
      };

      if (scheduleType === 'one_time') {
        if (!oneTimeDate || !oneTimeTime) {
          setError('Please select both a date and time');
          setSaving(false);
          return;
        }
        payload.run_at = new Date(`${oneTimeDate}T${oneTimeTime}`).toISOString();
      } else {
        payload.cron_expression = cronExpression;
      }

      if (inputData) {
        payload.input_data = inputData;
      }

      await api.createWorkflowSchedule(workflowId, payload);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save schedule');
    } finally {
      setSaving(false);
    }
  };

  // Delete handler
  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      await api.deleteWorkflowSchedule(workflowId);
      onClose();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to delete schedule');
    } finally {
      setDeleting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-dark-800 rounded-lg border border-dark-700 w-[540px] max-h-[90vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-700">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-oracle-red" />
            <h3 className="text-white font-medium">Schedule Workflow</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-dark-400 hover:text-white transition-colors rounded-md hover:bg-dark-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 text-dark-400 animate-spin" />
              <span className="ml-2 text-dark-400 text-sm">Loading schedule...</span>
            </div>
          ) : (
            <>
              {/* Workflow name display */}
              <p className="text-sm text-dark-400">
                Scheduling: <span className="text-white font-medium">{workflowName}</span>
              </p>

              {/* Error display */}
              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              {/* Schedule Type Toggle */}
              <div>
                <label className="block text-sm text-dark-300 mb-2">Schedule Type</label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setScheduleType('one_time')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      scheduleType === 'one_time'
                        ? 'bg-oracle-red text-white'
                        : 'bg-dark-700 text-dark-300 hover:bg-dark-600 hover:text-white'
                    }`}
                  >
                    <Calendar className="h-4 w-4" />
                    One-Time
                  </button>
                  <button
                    onClick={() => setScheduleType('recurring')}
                    className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                      scheduleType === 'recurring'
                        ? 'bg-oracle-red text-white'
                        : 'bg-dark-700 text-dark-300 hover:bg-dark-600 hover:text-white'
                    }`}
                  >
                    <Repeat className="h-4 w-4" />
                    Recurring
                  </button>
                </div>
              </div>

              {/* One-Time Section */}
              {scheduleType === 'one_time' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Date</label>
                    <input
                      type="date"
                      value={oneTimeDate}
                      onChange={e => setOneTimeDate(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red [color-scheme:dark]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-dark-300 mb-1">Time</label>
                    <input
                      type="time"
                      value={oneTimeTime}
                      onChange={e => setOneTimeTime(e.target.value)}
                      className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red [color-scheme:dark]"
                    />
                  </div>
                </div>
              )}

              {/* Recurring Section */}
              {scheduleType === 'recurring' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm text-dark-300 mb-2">Frequency</label>
                    <div className="grid grid-cols-4 gap-2">
                      {([
                        { key: 'hourly', label: 'Every Hour' },
                        { key: 'daily', label: 'Every Day' },
                        { key: 'weekly', label: 'Every Week' },
                        { key: 'custom', label: 'Custom' },
                      ] as { key: FrequencyPreset; label: string }[]).map(preset => (
                        <button
                          key={preset.key}
                          onClick={() => setFrequencyPreset(preset.key)}
                          className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                            frequencyPreset === preset.key
                              ? 'bg-oracle-red text-white'
                              : 'bg-dark-700 text-dark-300 hover:bg-dark-600 hover:text-white'
                          }`}
                        >
                          {preset.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Custom cron fields */}
                  {frequencyPreset === 'custom' && (
                    <div>
                      <label className="block text-sm text-dark-300 mb-2">Cron Expression</label>
                      <div className="grid grid-cols-5 gap-2">
                        {([
                          { key: 'minute', label: 'Min', placeholder: '0' },
                          { key: 'hour', label: 'Hour', placeholder: '9' },
                          { key: 'dayOfMonth', label: 'Day', placeholder: '*' },
                          { key: 'month', label: 'Month', placeholder: '*' },
                          { key: 'dayOfWeek', label: 'Weekday', placeholder: '*' },
                        ] as { key: keyof typeof cronFields; label: string; placeholder: string }[]).map(field => (
                          <div key={field.key}>
                            <label className="block text-xs text-dark-400 mb-1 text-center">{field.label}</label>
                            <input
                              type="text"
                              value={cronFields[field.key]}
                              onChange={e =>
                                setCronFields(prev => ({ ...prev, [field.key]: e.target.value }))
                              }
                              placeholder={field.placeholder}
                              className="w-full bg-dark-900 border border-dark-600 rounded-md px-2 py-1.5 text-white text-sm text-center focus:outline-none focus:border-oracle-red"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Cron preview */}
                  <div className="p-3 bg-dark-900 border border-dark-700 rounded-lg">
                    <p className="text-xs text-dark-400 mb-1">Schedule Preview</p>
                    <p className="text-sm text-white">{getCronDescription(cronExpression)} (UTC)</p>
                    <p className="text-xs text-dark-400 mt-1 font-mono">{cronExpression}</p>
                  </div>
                </div>
              )}

              {/* Input Data Section (only when no chat node) */}
              {(
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Static Input Data (JSON, including scheduled chat messages)</label>
                  <textarea
                    value={inputDataJson}
                    onChange={e => setInputDataJson(e.target.value)}
                    rows={4}
                    placeholder='{"message": "Hello world"}'
                    spellCheck={false}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm font-mono focus:outline-none focus:border-oracle-red resize-none"
                  />
                </div>
              )}

              {existingSchedule && <p className="text-xs text-dark-300">
                Next run: {existingSchedule.next_run_at ? new Date(existingSchedule.next_run_at).toLocaleString() : 'Not scheduled'}
                {existingSchedule.last_run_at && ` · Last run: ${new Date(existingSchedule.last_run_at).toLocaleString()}`}
              </p>}

              {/* Enable / Disable Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-white">Enable Schedule</p>
                  <p className="text-xs text-dark-400">Schedule will run automatically when enabled</p>
                </div>
                <button
                  onClick={() => setIsActive(prev => !prev)}
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    isActive ? 'bg-oracle-red' : 'bg-dark-600'
                  }`}
                  role="switch"
                  aria-checked={isActive}
                  aria-label="Enable schedule"
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                      isActive ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Delete existing schedule link */}
              {existingSchedule && (
                <button
                  onClick={handleDelete}
                  disabled={deleting}
                  className="text-sm text-red-400 hover:text-red-300 transition-colors disabled:opacity-50"
                >
                  {deleting ? 'Removing...' : 'Remove existing schedule'}
                </button>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {!loading && (
          <div className="flex items-center justify-end gap-2 p-4 border-t border-dark-700">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-300 hover:text-white rounded-md text-sm transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm transition-colors disabled:opacity-50"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                'Save Schedule'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScheduleModal;
