import { useState, useEffect } from 'react';
import { generateCampaign } from '../services/api';
import type { CampaignVariant } from '../services/api';

export interface CampaignContext {
  actionText?: string;
  suggestedObjective?: string;
  category?: string;
}

interface CampaignModalProps {
  open: boolean;
  onClose: () => void;
  brand: string;
  context?: CampaignContext;
}

const OBJECTIVES = [
  { value: 'customer_reactivation', label: 'Customer Reactivation' },
  { value: 'new_product_launch', label: 'New Product Launch' },
  { value: 'loyalty_reminder', label: 'Loyalty Reminder' },
  { value: 'seasonal_sale', label: 'Seasonal Sale' },
  { value: 'feedback_request', label: 'Feedback Request' },
];

const TONES = [
  { value: 'warm_personal', label: 'Warm & Personal' },
  { value: 'urgent_exclusive', label: 'Urgent & Exclusive' },
  { value: 'playful_casual', label: 'Playful & Casual' },
  { value: 'professional_confident', label: 'Professional & Confident' },
];

// Map action categories to campaign objectives
function mapCategoryToObjective(category?: string): string {
  if (!category) return 'customer_reactivation';
  const c = category.toLowerCase();
  if (c.includes('crisis') || c.includes('response')) return 'customer_reactivation';
  if (c.includes('campaign') || c.includes('promotion')) return 'seasonal_sale';
  if (c.includes('product')) return 'new_product_launch';
  if (c.includes('engage')) return 'feedback_request';
  return 'customer_reactivation';
}

export default function CampaignModal({ open, onClose, brand, context }: CampaignModalProps) {
  const [brandInput, setBrandInput] = useState(brand || '');
  const [objective, setObjective] = useState('customer_reactivation');
  const [tone, setTone] = useState('warm_personal');
  const [variants, setVariants] = useState<CampaignVariant[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showResults, setShowResults] = useState(false);

  // Sync brand prop and context
  useEffect(() => {
    if (brand) setBrandInput(brand);
  }, [brand]);

  useEffect(() => {
    if (context?.suggestedObjective) {
      setObjective(context.suggestedObjective);
    } else if (context?.category) {
      setObjective(mapCategoryToObjective(context.category));
    }
  }, [context]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  const handleGenerate = async () => {
    if (!brandInput.trim() || loading) return;
    setLoading(true);
    setError(null);

    try {
      const result = await generateCampaign(brandInput.trim(), objective, tone);
      setVariants(result.variants);
      setShowResults(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to generate campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setShowResults(false);
    setError(null);
  };

  const handleRegenerate = () => {
    setShowResults(false);
    setError(null);
    // Small delay so user sees the form flash, then auto-generate
    setTimeout(() => handleGenerate(), 100);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-3xl bg-white rounded-xl border border-gray-200 p-6 animate-fade-in shadow-xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
            <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            AI Campaign Studio
            <span className="text-[10px] font-normal text-gray-400 ml-1">(OCI GenAI)</span>
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all"
            title="Close (Esc)"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto min-h-0">
          {!showResults ? (
            /* ── Form ── */
            <div className="space-y-4">
              <p className="text-sm text-gray-500 leading-relaxed">
                Generate personalized marketing email variants informed by real sentiment data.
                The AI uses customer feedback insights to craft data-driven campaign content.
              </p>

              {/* Context banner when launched from an action */}
              {context?.actionText && (
                <div className="p-3 rounded-lg bg-accent/5 border border-accent/15 flex items-start gap-2">
                  <svg className="w-4 h-4 text-accent flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-0.5">Based on action insight</p>
                    <p className="text-xs text-gray-600 leading-relaxed">{context.actionText}</p>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                  Brand <span className="text-accent">*</span>
                </label>
                <input
                  type="text"
                  value={brandInput}
                  onChange={(e) => setBrandInput(e.target.value)}
                  placeholder="e.g., Nike, Coca Cola, Apple"
                  className="w-full px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                    Campaign Objective
                  </label>
                  <select
                    value={objective}
                    onChange={(e) => setObjective(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-900 focus:outline-none focus:border-accent/50 transition-all cursor-pointer"
                  >
                    {OBJECTIVES.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                    Tone
                  </label>
                  <select
                    value={tone}
                    onChange={(e) => setTone(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm text-gray-900 focus:outline-none focus:border-accent/50 transition-all cursor-pointer"
                  >
                    {TONES.map((t) => (
                      <option key={t.value} value={t.value}>{t.label}</option>
                    ))}
                  </select>
                </div>
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleGenerate}
                disabled={!brandInput.trim() || loading}
                className="w-full py-2.5 rounded-lg text-sm font-semibold bg-accent text-white hover:bg-accent/90 transition-all shadow-md shadow-accent/20 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Generating with OCI GenAI...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    Generate Campaign Variants
                  </>
                )}
              </button>
            </div>
          ) : (
            /* ── Results ── */
            <div className="space-y-4">
              {/* Actions bar */}
              <div className="flex items-center justify-between">
                <button
                  onClick={handleBack}
                  className="text-xs text-gray-400 hover:text-gray-900 transition-all flex items-center gap-1"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Change inputs
                </button>
                <button
                  onClick={handleRegenerate}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:text-gray-900 transition-all disabled:opacity-40 flex items-center gap-1.5"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Regenerate
                </button>
              </div>

              {/* Variant Cards */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                {variants.map((v, i) => (
                  <div
                    key={v.variant_label}
                    className={`rounded-xl p-4 border transition-all ${
                      i === 0
                        ? 'bg-green-50 border-green-200 ring-1 ring-green-200'
                        : 'bg-gray-50 border-gray-200'
                    }`}
                    style={{ animationDelay: `${i * 0.1}s` }}
                  >
                    {/* Variant header */}
                    <div className="flex items-center justify-between mb-3">
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${
                        i === 0 ? 'text-green-600' : 'text-gray-400'
                      }`}>
                        {i === 0 ? 'Best Match' : `Variant ${v.variant_label}`}
                      </span>
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        v.predicted_open_rate >= 30
                          ? 'bg-green-100 text-green-700'
                          : v.predicted_open_rate >= 25
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {v.predicted_open_rate.toFixed(1)}% open rate
                      </span>
                    </div>

                    {/* Subject */}
                    <h4 className="text-sm font-semibold text-gray-900 mb-2 leading-snug">
                      {v.subject}
                    </h4>

                    {/* Body */}
                    <div className="text-xs text-gray-500 leading-relaxed mb-3 whitespace-pre-line">
                      {v.body}
                    </div>

                    {/* Rationale */}
                    <p className="text-[10px] text-gray-400 italic border-t border-gray-200 pt-2">
                      {v.rationale}
                    </p>
                  </div>
                ))}
              </div>

              {variants.length === 0 && !loading && (
                <div className="text-center py-8 text-gray-400">
                  <p className="text-sm">No variants generated. Try again.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
