import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { LlamaModel, DomainInfo, DomainDetail, AdapterRule, AdapterLesson } from '../../types';

interface SystemSettingsProps {
  onBack: () => void;
  selectedInferenceModel: string;
  selectedEmbeddingModel: string;
  onInferenceModelChange: (model: string) => void;
  onEmbeddingModelChange: (model: string) => void;
}

interface AlertProps {
  type: 'success' | 'error';
  message: string;
  onClose: () => void;
}

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

const severityColor = (severity: string) => {
  switch (severity) {
    case 'critical': return 'bg-red-500/20 text-red-400 border-red-500/30';
    case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    case 'low': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    default: return 'bg-dark-600 text-dark-300 border-dark-500';
  }
};

// ── Rule Editor Modal ───────────────────────────────────────────────────

interface RuleEditorProps {
  rule: AdapterRule;
  onSave: (updated: AdapterRule) => void;
  onCancel: () => void;
}

const RuleEditor: React.FC<RuleEditorProps> = ({ rule, onSave, onCancel }) => {
  const [draft, setDraft] = useState<AdapterRule>({ ...rule });

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-medium text-white">Edit Rule: {draft.id}</h4>
        <div className="flex gap-2">
          <button onClick={() => onSave(draft)} className="px-3 py-1 text-xs bg-oracle-red hover:bg-oracle-red-dark text-white rounded transition-colors">Save</button>
          <button onClick={onCancel} className="px-3 py-1 text-xs bg-dark-600 hover:bg-dark-500 text-dark-300 rounded transition-colors">Cancel</button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-dark-400 mb-1">Category</label>
          <input value={draft.category} onChange={e => setDraft({ ...draft, category: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
        </div>
        <div>
          <label className="block text-xs text-dark-400 mb-1">Severity</label>
          <select value={draft.severity} onChange={e => setDraft({ ...draft, severity: e.target.value as AdapterRule['severity'] })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50">
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>
      {draft.keyword !== undefined && (
        <div>
          <label className="block text-xs text-dark-400 mb-1">Keyword</label>
          <input value={draft.keyword || ''} onChange={e => setDraft({ ...draft, keyword: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
        </div>
      )}
      {draft.standard !== undefined && (
        <div>
          <label className="block text-xs text-dark-400 mb-1">Standard reference</label>
          <input value={draft.standard || ''} onChange={e => setDraft({ ...draft, standard: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
        </div>
      )}
      {draft.field_name !== undefined && (
        <div>
          <label className="block text-xs text-dark-400 mb-1">Required field</label>
          <input value={draft.field_name || ''} onChange={e => setDraft({ ...draft, field_name: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
        </div>
      )}
      <div>
        <label className="block text-xs text-dark-400 mb-1">Aliases (comma-separated)</label>
        <input value={(draft.aliases || []).join(', ')} onChange={e => setDraft({ ...draft, aliases: e.target.value.split(',').map(alias => alias.trim()).filter(Boolean) })} placeholder="Alternative labels or terms" className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">When absent</label>
        <select value={draft.missing_status || (draft.type === 'required_field' ? 'fail' : 'warning')} onChange={e => setDraft({ ...draft, missing_status: e.target.value as AdapterRule['missing_status'] })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50">
          <option value="warning">Warning</option>
          <option value="review">Needs human review</option>
          <option value="fail">Fail</option>
        </select>
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">Pass Message</label>
        <input value={draft.pass_message} onChange={e => setDraft({ ...draft, pass_message: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">Fail Message</label>
        <input value={draft.fail_message} onChange={e => setDraft({ ...draft, fail_message: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
      </div>
    </div>
  );
};

// ── Lesson Editor Modal ─────────────────────────────────────────────────

interface LessonEditorProps {
  lesson: AdapterLesson;
  onSave: (updated: AdapterLesson) => void;
  onCancel: () => void;
}

const LessonEditor: React.FC<LessonEditorProps> = ({ lesson, onSave, onCancel }) => {
  const [draft, setDraft] = useState<AdapterLesson>({ ...lesson });

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-lg p-4 space-y-3">
      <div className="flex justify-between items-center">
        <h4 className="text-sm font-medium text-white">Edit Lesson: {draft.id}</h4>
        <div className="flex gap-2">
          <button onClick={() => onSave(draft)} className="px-3 py-1 text-xs bg-oracle-red hover:bg-oracle-red-dark text-white rounded transition-colors">Save</button>
          <button onClick={onCancel} className="px-3 py-1 text-xs bg-dark-600 hover:bg-dark-500 text-dark-300 rounded transition-colors">Cancel</button>
        </div>
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">Title</label>
        <input value={draft.title} onChange={e => setDraft({ ...draft, title: e.target.value })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">Description</label>
        <textarea value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })} rows={3} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50 resize-none" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-dark-400 mb-1">Severity</label>
          <select value={draft.severity} onChange={e => setDraft({ ...draft, severity: e.target.value as AdapterLesson['severity'] })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50">
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-dark-400 mb-1">Keywords (comma-separated)</label>
          <input value={draft.keywords.join(', ')} onChange={e => setDraft({ ...draft, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) })} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50" />
        </div>
      </div>
      <div>
        <label className="block text-xs text-dark-400 mb-1">Recommendation</label>
        <textarea value={draft.recommendation} onChange={e => setDraft({ ...draft, recommendation: e.target.value })} rows={2} className="w-full px-2 py-1.5 bg-dark-800 border border-dark-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-oracle-red/50 resize-none" />
      </div>
    </div>
  );
};

// ── Domain Adapter Card ─────────────────────────────────────────────────

interface DomainCardProps {
  domain: DomainInfo;
  onToggle: (name: string, enabled: boolean) => void;
  onAlert: (type: 'success' | 'error', message: string) => void;
}

const DomainCard: React.FC<DomainCardProps> = ({ domain, onToggle, onAlert }) => {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<'fields' | 'rules' | 'lessons'>('fields');
  const [detail, setDetail] = useState<DomainDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [editingLessonId, setEditingLessonId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const loadDetail = useCallback(async () => {
    if (detail) return;
    setLoading(true);
    try {
      const d = await api.getDomainDetail(domain.name);
      setDetail(d);
    } catch {
      onAlert('error', `Failed to load ${domain.display_name} details`);
    } finally {
      setLoading(false);
    }
  }, [domain.name, domain.display_name, detail, onAlert]);

  const handleExpand = () => {
    const next = !expanded;
    setExpanded(next);
    if (next) loadDetail();
  };

  const handleSaveRule = async (updated: AdapterRule) => {
    if (!detail) return;
    setSaving(true);
    try {
      const newChecks = detail.rules.checks.map(r => r.id === updated.id ? updated : r);
      const newRules = { ...detail.rules, checks: newChecks };
      await api.updateDomainConfig(domain.name, 'rules', newRules);
      setDetail({ ...detail, rules: newRules });
      setEditingRuleId(null);
      onAlert('success', `Rule ${updated.id} updated`);
    } catch {
      onAlert('error', `Failed to save rule ${updated.id}`);
    } finally {
      setSaving(false);
    }
  };

  const handleSaveLesson = async (updated: AdapterLesson) => {
    if (!detail) return;
    setSaving(true);
    try {
      const newItems = detail.lessons.items.map(l => l.id === updated.id ? updated : l);
      const newLessons = { ...detail.lessons, items: newItems };
      await api.updateDomainConfig(domain.name, 'lessons', newLessons);
      setDetail({ ...detail, lessons: newLessons });
      setEditingLessonId(null);
      onAlert('success', `Lesson ${updated.id} updated`);
    } catch {
      onAlert('error', `Failed to save lesson ${updated.id}`);
    } finally {
      setSaving(false);
    }
  };

  const fields = detail?.schema?.fields || [];
  const rules = detail?.rules?.checks || [];
  const lessons = detail?.lessons?.items || [];

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={handleExpand}
        className="w-full flex items-center justify-between px-5 py-4 hover:bg-dark-700/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <svg className={`w-4 h-4 text-dark-400 transition-transform ${expanded ? 'rotate-90' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <div className="text-left">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-white">{domain.display_name}</span>
              {domain.name === 'generic' && (
                <span className="px-1.5 py-0.5 text-[10px] font-medium bg-dark-600 text-dark-300 rounded">DEFAULT</span>
              )}
              <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded ${domain.enabled ? 'bg-green-500/20 text-green-400' : 'bg-dark-600 text-dark-400'}`}>
                {domain.enabled ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
            <p className="text-xs text-dark-400 mt-0.5 line-clamp-1">{domain.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-dark-400">
          <span>{domain.field_count} fields</span>
          <span>{domain.rule_count} rules</span>
          <span>{domain.lesson_count} lessons</span>
          {domain.name !== 'generic' && (
            <button
              onClick={(e) => { e.stopPropagation(); onToggle(domain.name, !domain.enabled); }}
              className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
                domain.enabled
                  ? 'bg-dark-600 hover:bg-dark-500 text-dark-300'
                  : 'bg-oracle-red/20 hover:bg-oracle-red/30 text-oracle-red'
              }`}
            >
              {domain.enabled ? 'Disable' : 'Enable'}
            </button>
          )}
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="border-t border-dark-700">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <svg className="animate-spin h-5 w-5 text-dark-400" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          ) : (
            <>
              {/* Tabs */}
              <div className="flex border-b border-dark-700">
                {(['fields', 'rules', 'lessons'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 px-4 py-2.5 text-xs font-medium transition-colors ${
                      activeTab === tab
                        ? 'text-oracle-red border-b-2 border-oracle-red bg-dark-700/30'
                        : 'text-dark-400 hover:text-dark-200'
                    }`}
                  >
                    {tab === 'fields' && `Fields (${fields.length})`}
                    {tab === 'rules' && `Rules (${rules.length})`}
                    {tab === 'lessons' && `Lessons (${lessons.length})`}
                  </button>
                ))}
              </div>

              {/* Tab content */}
              <div className="p-4 max-h-96 overflow-y-auto">
                {/* Fields tab */}
                {activeTab === 'fields' && (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="text-dark-400 border-b border-dark-700">
                        <th className="text-left py-2 pr-3 font-medium">Field</th>
                        <th className="text-left py-2 pr-3 font-medium">Type</th>
                        <th className="text-left py-2 pr-3 font-medium">Group</th>
                        <th className="text-left py-2 font-medium">Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fields.map((f) => (
                        <tr key={f.name} className="border-b border-dark-700/50 hover:bg-dark-700/30">
                          <td className="py-2 pr-3 text-white font-medium">{f.label}</td>
                          <td className="py-2 pr-3">
                            <span className="px-1.5 py-0.5 bg-dark-600 text-dark-300 rounded text-[10px]">{f.type}</span>
                          </td>
                          <td className="py-2 pr-3 text-dark-400">{f.group}</td>
                          <td className="py-2 text-dark-400 max-w-xs truncate">{f.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {/* Rules tab */}
                {activeTab === 'rules' && (
                  <div className="space-y-2">
                    {rules.map((r) => (
                      editingRuleId === r.id ? (
                        <RuleEditor key={r.id} rule={r} onSave={handleSaveRule} onCancel={() => setEditingRuleId(null)} />
                      ) : (
                        <div key={r.id} className="flex items-start gap-3 p-3 bg-dark-700/50 rounded-lg hover:bg-dark-700/70 group">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[10px] font-mono text-dark-500">{r.id}</span>
                              <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${severityColor(r.severity)}`}>{r.severity}</span>
                              <span className="px-1.5 py-0.5 text-[10px] bg-dark-600 text-dark-400 rounded">{r.type}</span>
                              <span className="text-[10px] text-dark-500">{r.category}</span>
                            </div>
                            <p className="text-xs text-dark-300">{r.fail_message}</p>
                          </div>
                          <button
                            onClick={() => setEditingRuleId(r.id)}
                            className="opacity-0 group-hover:opacity-100 p-1 text-dark-400 hover:text-white transition-all"
                            title="Edit rule"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                          </button>
                        </div>
                      )
                    ))}
                  </div>
                )}

                {/* Lessons tab */}
                {activeTab === 'lessons' && (
                  <div className="space-y-2">
                    {lessons.map((l) => (
                      editingLessonId === l.id ? (
                        <LessonEditor key={l.id} lesson={l} onSave={handleSaveLesson} onCancel={() => setEditingLessonId(null)} />
                      ) : (
                        <div key={l.id} className="p-3 bg-dark-700/50 rounded-lg hover:bg-dark-700/70 group">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-[10px] font-mono text-dark-500">{l.id}</span>
                                <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border ${severityColor(l.severity)}`}>{l.severity}</span>
                              </div>
                              <p className="text-xs font-medium text-white mb-1">{l.title}</p>
                              <p className="text-xs text-dark-400 line-clamp-2">{l.description}</p>
                              {l.recommendation && (
                                <p className="text-xs text-dark-500 mt-1 italic">Rec: {l.recommendation}</p>
                              )}
                            </div>
                            <button
                              onClick={() => setEditingLessonId(l.id)}
                              className="opacity-0 group-hover:opacity-100 p-1 text-dark-400 hover:text-white transition-all flex-shrink-0"
                              title="Edit lesson"
                            >
                              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      )
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
};


// ── Main Component ──────────────────────────────────────────────────────

const SystemSettings: React.FC<SystemSettingsProps> = ({
  onBack,
  selectedInferenceModel,
  selectedEmbeddingModel,
  onInferenceModelChange,
  onEmbeddingModelChange,
}) => {
  const [models, setModels] = useState<LlamaModel[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(true);

  // Draft model selections (not persisted until save)
  const [draftInferenceModel, setDraftInferenceModel] = useState(selectedInferenceModel);
  const [draftEmbeddingModel, setDraftEmbeddingModel] = useState(selectedEmbeddingModel);
  const [isSavingModels, setIsSavingModels] = useState(false);

  // Object store settings
  const [bucketName, setBucketName] = useState('paas-rag-GZkYza-bucket');
  const [namespace, setNamespace] = useState('iduyx1qnmway');
  const [isSavingStorage, setIsSavingStorage] = useState(false);

  // Domain adapters
  const [domains, setDomains] = useState<DomainInfo[]>([]);
  const [isLoadingDomains, setIsLoadingDomains] = useState(true);

  // Alert state
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  useEffect(() => {
    setDraftInferenceModel(selectedInferenceModel);
    setDraftEmbeddingModel(selectedEmbeddingModel);
  }, [selectedInferenceModel, selectedEmbeddingModel]);

  useEffect(() => {
    setIsLoadingModels(true);
    api.listModels()
      .then(setModels)
      .catch(() => setModels([]))
      .finally(() => setIsLoadingModels(false));
  }, []);

  useEffect(() => {
    setIsLoadingDomains(true);
    api.listDomains()
      .then(setDomains)
      .catch(() => setDomains([]))
      .finally(() => setIsLoadingDomains(false));
  }, []);

  const handleSaveModels = () => {
    setIsSavingModels(true);
    try {
      onInferenceModelChange(draftInferenceModel);
      onEmbeddingModelChange(draftEmbeddingModel);
      setAlert({ type: 'success', message: 'Model configuration saved successfully!' });
    } catch {
      setAlert({ type: 'error', message: 'Failed to save model configuration.' });
    } finally {
      setIsSavingModels(false);
    }
  };

  const handleSaveStorage = () => {
    setIsSavingStorage(true);
    try {
      setAlert({ type: 'success', message: 'Object store settings saved.' });
    } catch {
      setAlert({ type: 'error', message: 'Failed to save storage settings.' });
    } finally {
      setIsSavingStorage(false);
    }
  };

  const handleToggleDomain = async (name: string, enabled: boolean) => {
    try {
      await api.toggleDomain(name, enabled);
      setDomains(prev => prev.map(d => d.name === name ? { ...d, enabled } : d));
      setAlert({ type: 'success', message: `${name} adapter ${enabled ? 'enabled' : 'disabled'}` });
    } catch {
      setAlert({ type: 'error', message: `Failed to toggle ${name}` });
    }
  };

  const handleAlert = useCallback((type: 'success' | 'error', message: string) => {
    setAlert({ type, message });
  }, []);

  const modelsDirty = draftInferenceModel !== selectedInferenceModel || draftEmbeddingModel !== selectedEmbeddingModel;

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

      <div className="max-w-3xl mx-auto space-y-6">
        {/* Page title */}
        <div>
          <h1 className="text-2xl font-bold text-white">System Settings</h1>
          <p className="text-dark-400 text-sm mt-1">Configure AI models, compliance adapters, and infrastructure</p>
        </div>

        {/* ── Industry Compliance Adapters ─────────────────────────────── */}
        <div>
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-white">Industry Compliance Adapters</h2>
            <p className="text-dark-400 text-sm mt-1">
              Configure domain-specific compliance rules, extraction schemas, and lessons learned for each industry.
              Click an adapter to view and edit its configuration.
            </p>
          </div>

          {isLoadingDomains ? (
            <div className="flex items-center gap-2 text-sm text-dark-400 py-8 justify-center">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Loading adapters...
            </div>
          ) : domains.length === 0 ? (
            <div className="bg-dark-800 border border-dark-700 rounded-lg p-6 text-center text-sm text-dark-400">
              No adapters found. Check that the backend adapters directory is configured.
            </div>
          ) : (
            <div className="space-y-2">
              {domains.map((d) => (
                <DomainCard key={d.name} domain={d} onToggle={handleToggleDomain} onAlert={handleAlert} />
              ))}
            </div>
          )}
        </div>

        {/* ── AI Model Selection ──────────────────────────────────────── */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">AI Model Selection</h2>
          <p className="text-dark-400 text-sm mb-5">Select the inference model for chat and document analysis</p>

          {isLoadingModels ? (
            <div className="flex items-center gap-2 text-sm text-dark-400 py-4">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Loading available models...
            </div>
          ) : models.length === 0 ? (
            <div className="bg-dark-700/50 border border-dark-600 rounded-md p-4 text-sm text-dark-400">
              No models available from the endpoint. Check that the LlamaStack service is running.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">Inference Model</label>
                <select
                  value={draftInferenceModel}
                  onChange={(e) => setDraftInferenceModel(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-white focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red"
                >
                  <option value="">Select a model</option>
                  {models.filter((m) => m.type === 'llm').map((m) => (
                    <option key={m.id} value={m.id}>{m.id}</option>
                  ))}
                </select>
                <p className="text-xs text-dark-500 mt-1">Used for chat, summarization, and document analysis</p>
              </div>
            </div>
          )}
        </div>

        {/* Embedding Model Selection */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Embedding Model Selection</h2>
          <p className="text-dark-400 text-sm mb-5">Select the embedding model for document indexing and vector search</p>

          {isLoadingModels ? (
            <div className="flex items-center gap-2 text-sm text-dark-400 py-4">
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Loading available models...
            </div>
          ) : models.length === 0 ? (
            <div className="bg-dark-700/50 border border-dark-600 rounded-md p-4 text-sm text-dark-400">
              No models available from the endpoint. Check that the LlamaStack service is running.
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-1.5">Embedding Model</label>
                <select
                  value={draftEmbeddingModel}
                  onChange={(e) => setDraftEmbeddingModel(e.target.value)}
                  className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-sm text-white focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red"
                >
                  <option value="">Select a model</option>
                  {models.filter((m) => m.type === 'embedding').map((m) => (
                    <option key={m.id} value={m.id}>{m.id}</option>
                  ))}
                </select>
                <p className="text-xs text-dark-500 mt-1">Used for document indexing and vector search (RAG)</p>
              </div>
              <div className="pt-2">
                <button
                  onClick={handleSaveModels}
                  disabled={!modelsDirty || isSavingModels}
                  className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {isSavingModels ? 'Saving...' : 'Save Model Configuration'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Object Store Settings */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Object Store Settings</h2>
          <p className="text-dark-400 text-sm mb-5">OCI Object Storage configuration for document storage</p>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Namespace</label>
              <input
                type="text"
                value={namespace}
                onChange={(e) => setNamespace(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
              />
              <p className="text-xs text-dark-500 mt-1">OCI Object Storage namespace</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-1.5">Bucket Name</label>
              <input
                type="text"
                value={bucketName}
                onChange={(e) => setBucketName(e.target.value)}
                className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-md text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red text-sm"
              />
              <p className="text-xs text-dark-500 mt-1">Target bucket for document storage and RAG artifacts</p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Region</p>
                <p className="text-sm text-dark-200">us-chicago-1</p>
              </div>
              <div className="bg-dark-700/50 rounded-md p-3">
                <p className="text-xs text-dark-500 mb-1">Storage Tier</p>
                <p className="text-sm text-dark-200">Standard</p>
              </div>
            </div>
            <div className="pt-2">
              <button
                onClick={handleSaveStorage}
                disabled={isSavingStorage}
                className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white text-sm font-medium rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isSavingStorage ? 'Saving...' : 'Save Storage Settings'}
              </button>
            </div>
          </div>
        </div>

        {/* Vector Database Info */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-1">Vector Database</h2>
          <p className="text-dark-400 text-sm mb-5">Oracle 23ai Autonomous Database with AI Vector Search</p>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Database</p>
              <p className="text-sm text-dark-200">Oracle 23ai ADB</p>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Vector Dimensions</p>
              <p className="text-sm text-dark-200">1024</p>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Vector Table</p>
              <p className="text-sm text-dark-200">document_vectors</p>
            </div>
            <div className="bg-dark-700/50 rounded-md p-3">
              <p className="text-xs text-dark-500 mb-1">Status</p>
              <span className="inline-flex items-center gap-1.5 text-sm text-green-400">
                <span className="w-2 h-2 rounded-full bg-green-400" />
                Connected
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;
