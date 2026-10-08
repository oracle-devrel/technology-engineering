import { DollarSign, Clock, Users, Shield, Zap, Brain, Globe, Cpu, TrendingUp, CheckCircle, Lock, Server, Layers, ArrowRight } from 'lucide-react';
import PageShell from '../shared/PageShell';
import InfoTip from '../shared/InfoTip';

export default function BusinessImpact() {
  return (
    <PageShell title="Business Impact & ROI" subtitle="Estimated savings vs. manual processing, OCI GenAI deployment strategy">
      <div className="h-full overflow-y-auto space-y-4 w-full">

        {/* Impact KPI Cards */}
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500">Estimated savings vs. manual document processing</span>
          <InfoTip lines={[
            { label: 'Method', value: 'Side-by-side comparison of manual analyst effort vs. AI-automated processing for equivalent workload' },
            { label: 'Baseline', value: 'Manual: 2 senior document analysts at $75/hr, processing 8 documents/day (60-page avg)' },
            { label: 'AI Cost', value: 'OCI GenAI inference tokens ($0.0015/1K) + Oracle 26ai storage + OKE compute per document', color: 'text-emerald-400' },
            { label: 'Scope', value: 'Includes extraction, compliance checking, chunking, and indexing — not just text extraction' },
          ]} />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { icon: Clock, label: 'Document Processing', before: '2.5 hrs', after: '45 sec', savings: '99.5%', color: '#C74634',
              desc: 'Time to extract key fields from a 60-page document',
              info: [
                { label: 'Manual', value: 'Analyst reads document, identifies fields, enters data into spreadsheet — avg 2.5 hours for 60-page technical document' },
                { label: 'AI-Powered', value: 'PyMuPDF text extraction + Llama 4 Maverick field extraction + compliance check + RAG indexing = ~45 seconds', color: 'text-emerald-400' },
                { label: 'Includes', value: 'Text extraction, table detection, 28+ field extraction, compliance rule checking, chunk indexing for search' },
              ] },
            { icon: DollarSign, label: 'Cost per Document', before: '$187.50', after: '$0.08', savings: '99.9%', color: '#4CB848',
              desc: 'Analyst cost ($75/hr) vs. AI processing cost',
              info: [
                { label: 'Manual Cost', value: '$75/hr × 2.5 hrs = $187.50 per document (senior analyst fully loaded rate)' },
                { label: 'AI Cost Breakdown', value: 'LLM tokens ~$0.04 + embedding ~$0.01 + Oracle 26ai storage ~$0.02 + compute ~$0.01 = $0.08', color: 'text-emerald-400' },
                { label: 'Savings', value: '$187.42 saved per document — 2,341x cost reduction' },
              ] },
            { icon: Users, label: 'Analyst Capacity', before: '8 docs/day', after: '500+ docs/day', savings: '62x', color: '#0066CC',
              desc: 'Documents one analyst can process per day',
              info: [
                { label: 'Manual', value: '8 hrs/day ÷ 2.5 hrs/doc × 80% productivity = ~8 documents per analyst per day' },
                { label: 'AI-Powered', value: 'Parallel processing, 45-sec extraction — limited only by LLM throughput (~105 tok/s)', color: 'text-emerald-400' },
                { label: 'Note', value: '1 analyst with AI oversight can review and approve 500+ AI-processed documents per day' },
              ] },
            { icon: Shield, label: 'Compliance Coverage', before: '60%', after: '100%', savings: '+40%', color: '#F0AB00',
              desc: 'Checks consistently applied to every document',
              info: [
                { label: 'Manual', value: 'Analysts check ~60% of compliance rules due to time pressure, fatigue, and inconsistency across reviewers' },
                { label: 'AI-Powered', value: 'Every document checked against ALL domain rules automatically — keyword, field, and standard checks', color: 'text-emerald-400' },
                { label: 'Impact', value: 'Eliminates compliance gaps, reduces regulatory risk, provides auditable evidence trail' },
              ] },
          ].map(({ icon: Icon, label, before, after, savings, color, desc, info }) => (
            <div key={label} className="bg-dark-800 border border-dark-700 rounded-lg p-3">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: color + '15' }}>
                    <Icon size={14} style={{ color }} />
                  </div>
                  <span className="text-[11px] text-white font-medium">{label}</span>
                </div>
                <InfoTip lines={info} />
              </div>
              <div className="flex items-end justify-between mb-1.5">
                <div>
                  <p className="text-[11px] text-gray-600">Manual</p>
                  <p className="text-xs text-gray-400 line-through">{before}</p>
                </div>
                <div className="text-right">
                  <p className="text-[11px] text-gray-600">AI-Powered</p>
                  <p className="text-sm font-bold text-emerald-400">{after}</p>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-[11px] text-gray-500">{desc}</p>
                <span className="text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded shrink-0 ml-2">{savings}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Cost Breakdown + ROI */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {/* Monthly Cost */}
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <DollarSign size={14} className="text-emerald-400" />
              <span className="text-xs text-white font-semibold flex-1">Monthly Platform Cost (USD)</span>
              <InfoTip lines={[
                { label: 'Pricing Model', value: 'On-demand (token-based) OCI GenAI — pay per inference request' },
                { label: 'Volume', value: '~1,000 documents/month, 5,000 RAG chat queries, 200 research reports' },
                { label: 'OCI GenAI', value: 'Llama 4 Maverick at ~$0.0015/1K input tokens, ~$0.002/1K output tokens' },
                { label: 'Oracle 26ai', value: 'Autonomous Database with AI Vector Search — always-on, auto-scaling' },
                { label: 'Production', value: 'Switch to DAC for fixed monthly pricing with unlimited tokens at scale', color: 'text-emerald-400' },
              ]} />
            </div>
            <div className="space-y-1.5">
              {[
                { item: 'OCI GenAI (Llama 4 Maverick)', cost: '$320', desc: 'LLM inference — extraction + chat + reports' },
                { item: 'Oracle 26ai ADB', cost: '$250', desc: 'Autonomous Database with AI Vector Search' },
                { item: 'OKE Cluster (2 pods)', cost: '$180', desc: 'Kubernetes compute for backend + frontend' },
                { item: 'OCI Object Storage', cost: '$25', desc: 'Document storage and backups' },
                { item: 'Cohere Embeddings', cost: '$45', desc: 'Document vectorization for RAG search' },
              ].map(({ item, cost, desc }) => (
                <div key={item} className="flex items-center justify-between py-1 border-b border-dark-700/20 last:border-0">
                  <div className="min-w-0">
                    <p className="text-[11px] text-gray-300">{item}</p>
                    <p className="text-[11px] text-gray-600">{desc}</p>
                  </div>
                  <span className="text-xs font-semibold text-white shrink-0 ml-3">{cost}</span>
                </div>
              ))}
              <div className="flex items-center justify-between pt-2 mt-1 border-t border-dark-700">
                <span className="text-[11px] text-white font-semibold">Total Monthly (est.)</span>
                <span className="text-sm font-bold text-oracle-red">$820/mo</span>
              </div>
            </div>
          </div>

          {/* ROI */}
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={14} className="text-emerald-400" />
              <span className="text-xs text-white font-semibold flex-1">ROI Analysis (USD)</span>
              <InfoTip lines={[
                { label: 'Method', value: 'Total cost of ownership: full manual team vs. AI platform + 1 oversight analyst' },
                { label: 'Manual Team', value: '2 document analysts ($75/hr full-time) + compliance reviewer + data entry QC staff' },
                { label: 'AI Team', value: 'OCI platform ($820/mo all-in) + 1 senior analyst for review, approval, and edge cases', color: 'text-emerald-400' },
                { label: 'Calculation', value: 'Annual savings = ($38,700 - $13,820) × 12 = $298,560/year' },
                { label: 'Note', value: 'Conservative estimate — does not include reduced error rates, faster turnaround, or regulatory risk reduction' },
              ]} />
            </div>
            <div className="space-y-2.5">
              <div>
                <p className="text-[11px] text-gray-500 mb-1">Without AI (Manual Processing)</p>
                {[
                  { item: '2 Document Analysts ($75/hr)', cost: '$26,000/mo' },
                  { item: 'Compliance Review Team', cost: '$8,500/mo' },
                  { item: 'Data Entry & QC', cost: '$4,200/mo' },
                ].map(({ item, cost }) => (
                  <div key={item} className="flex justify-between text-[11px] py-0.5">
                    <span className="text-gray-400">{item}</span>
                    <span className="text-red-400">{cost}</span>
                  </div>
                ))}
                <div className="flex justify-between text-[11px] pt-1 border-t border-dark-700/30">
                  <span className="text-gray-300 font-medium">Manual Total</span>
                  <span className="text-red-400 font-bold">$38,700/mo</span>
                </div>
              </div>
              <div>
                <p className="text-[11px] text-gray-500 mb-1">With OCI AI Platform</p>
                {[
                  { item: 'OCI Platform (fully managed)', cost: '$820/mo' },
                  { item: '1 Analyst (review & oversight)', cost: '$13,000/mo' },
                ].map(({ item, cost }) => (
                  <div key={item} className="flex justify-between text-[11px] py-0.5">
                    <span className="text-gray-400">{item}</span>
                    <span className="text-emerald-400">{cost}</span>
                  </div>
                ))}
                <div className="flex justify-between text-[11px] pt-1 border-t border-dark-700/30">
                  <span className="text-gray-300 font-medium">AI-Powered Total</span>
                  <span className="text-emerald-400 font-bold">$13,820/mo</span>
                </div>
              </div>
              <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2 text-center relative">
                <div className="absolute top-2 right-2">
                  <InfoTip lines={[
                    { label: 'Formula', value: '($38,700 - $13,820) × 12 months = $298,560 annual savings' },
                    { label: 'Cost Reduction', value: '64% reduction in total document processing costs', color: 'text-emerald-400' },
                    { label: 'Throughput', value: '62x increase in documents processed per analyst per day' },
                    { label: 'Payback', value: 'Platform pays for itself within the first month of operation' },
                  ]} />
                </div>
                <p className="text-[11px] text-emerald-400 uppercase tracking-wider font-medium">Annual Savings</p>
                <p className="text-xl font-bold text-emerald-400">$298,560</p>
                <p className="text-[11px] text-gray-400">64% cost reduction &middot; 62x throughput increase</p>
              </div>
            </div>
          </div>
        </div>

        {/* Key Business Benefits */}
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-500 font-medium">Key Business Benefits</span>
          <InfoTip lines={[
            { label: 'Why These 4', value: 'These are the most common customer pain points solved by the platform' },
            { label: 'Validated', value: 'Based on POC deployments across Construction, Healthcare, Airlines, and Logistics domains', color: 'text-emerald-400' },
            { label: 'Measurable', value: 'Each benefit is quantifiable — time saved, coverage %, cost reduction, staff hours freed' },
          ]} />
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
          {[
            { icon: Zap, title: 'Faster Time-to-Insight', desc: 'Reduce document review from hours to seconds. Get answers instantly with RAG chat.', color: '#C74634' },
            { icon: CheckCircle, title: '100% Compliance Coverage', desc: 'Every document checked against all rules automatically. No human oversight gaps.', color: '#4CB848' },
            { icon: Globe, title: 'Multi-Domain Scale', desc: '5 industry adapters ready. Add new domains with JSON config — no code changes.', color: '#0066CC' },
            { icon: Cpu, title: 'Zero GPU Management', desc: 'Fully managed OCI GenAI. No GPU provisioning, no model hosting, no MLOps overhead.', color: '#8B5CF6' },
          ].map(({ icon: Icon, title, desc, color }) => (
            <div key={title} className="bg-dark-800 border border-dark-700 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1.5">
                <Icon size={13} style={{ color }} />
                <span className="text-[11px] text-white font-medium">{title}</span>
              </div>
              <p className="text-[11px] text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* OCI GenAI Deployment Strategy */}
        <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
          <div className="px-4 py-3 border-b border-dark-700">
            <div className="flex items-center gap-2">
              <Server size={15} className="text-oracle-red" />
              <span className="text-sm font-semibold text-white flex-1">OCI GenAI Deployment Strategy</span>
              <InfoTip lines={[
                { label: 'Strategy', value: 'Start with On-Demand tokens for POC validation, then migrate to DAC for production' },
                { label: 'On-Demand', value: 'Ideal for POC: fast setup, no commitment, pay only for what you use during evaluation' },
                { label: 'DAC', value: 'Required for production: data isolation, regulatory compliance, custom models, predictable pricing', color: 'text-emerald-400' },
                { label: 'Breakeven', value: 'DAC becomes 40-60% cheaper than on-demand at ~50,000 queries/month' },
                { label: 'Migration', value: 'Zero code changes — same API, same models. Only the infrastructure tier changes.' },
              ]} />
            </div>
            <p className="text-[11px] text-gray-500 mt-0.5">Recommended deployment path from POC to Production</p>
          </div>
          <div className="p-4">
            {/* Journey bar */}
            <div className="flex items-center gap-2 mb-4 bg-dark-900 border border-dark-700/50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-amber-400">
                <Zap size={14} />
                <span className="text-[11px] font-semibold">POC / Dev</span>
              </div>
              <div className="text-[11px] text-gray-600 px-2">On-Demand (Token-Based)</div>
              <ArrowRight size={14} className="text-gray-600" />
              <div className="flex items-center gap-2 text-emerald-400">
                <Lock size={14} />
                <span className="text-[11px] font-semibold">Production</span>
              </div>
              <div className="text-[11px] text-gray-600 px-2">Dedicated AI Cluster (DAC)</div>
              <div className="ml-auto">
                <span className="text-[11px] px-2 py-1 bg-oracle-red/10 text-oracle-red rounded-full font-medium">Recommended</span>
              </div>
            </div>

            {/* Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-4">
              {/* On-Demand */}
              <div className="border border-amber-500/20 rounded-lg overflow-hidden">
                <div className="px-4 py-2.5 bg-amber-500/5 border-b border-amber-500/20 flex items-center justify-between">
                  <div className="flex items-center gap-2"><Zap size={14} className="text-amber-400" /><span className="text-xs font-semibold text-white">On-Demand (Token-Based)</span></div>
                  <span className="text-[11px] px-2 py-0.5 bg-amber-500/20 text-amber-400 rounded-full">POC / Dev</span>
                </div>
                <div className="p-3 space-y-2">
                  <p className="text-[11px] text-gray-400 leading-relaxed mb-2">Pay-per-token pricing on shared infrastructure. Ideal for proof-of-concept and development.</p>
                  {[
                    { l: 'Infrastructure', v: 'Shared multi-tenant GPUs' }, { l: 'Pricing', v: '~$0.0015/1K input tokens' },
                    { l: 'Data Isolation', v: 'Shared environment' }, { l: 'Custom Models', v: 'Not supported' },
                    { l: 'Fine-Tuning', v: 'Not available' }, { l: 'SLA', v: 'Best effort' },
                  ].map(({ l, v }) => (
                    <div key={l} className="flex justify-between py-1 border-b border-dark-700/20 last:border-0">
                      <span className="text-[11px] text-gray-500">{l}</span><span className="text-[11px] text-gray-300">{v}</span>
                    </div>
                  ))}
                  <div className="mt-2 pt-2 border-t border-dark-700/30">
                    <p className="text-[11px] text-amber-400 font-medium">Est. Monthly: $320 - $1,200</p>
                  </div>
                </div>
              </div>

              {/* DAC */}
              <div className="border border-emerald-500/30 rounded-lg overflow-hidden relative">
                <div className="absolute top-0 right-0 bg-oracle-red text-white text-[11px] font-bold px-2.5 py-1 rounded-bl-lg uppercase tracking-wider">Production Ready</div>
                <div className="px-4 py-2.5 bg-emerald-500/5 border-b border-emerald-500/20 flex items-center justify-between">
                  <div className="flex items-center gap-2"><Lock size={14} className="text-emerald-400" /><span className="text-xs font-semibold text-white">Dedicated AI Cluster (DAC)</span></div>
                  <span className="hidden">Production</span>
                </div>
                <div className="p-3 space-y-2">
                  <p className="text-[11px] text-gray-400 leading-relaxed mb-2">Dedicated GPU infrastructure isolated to your tenancy. Enterprise-grade security and custom model support.</p>
                  {[
                    { l: 'Infrastructure', v: 'Dedicated isolated GPUs' }, { l: 'Pricing', v: 'Fixed monthly — unlimited tokens' },
                    { l: 'Data Isolation', v: 'Fully isolated tenancy' }, { l: 'Custom Models', v: 'Import Qwen, Mistral, Phi, etc.' },
                    { l: 'Fine-Tuning', v: 'Full fine-tuning support' }, { l: 'SLA', v: '99.9% availability guarantee' },
                  ].map(({ l, v }) => (
                    <div key={l} className="flex justify-between py-1 border-b border-dark-700/20 last:border-0">
                      <span className="text-[11px] text-gray-500">{l}</span><span className="text-[11px] text-emerald-400 font-medium">{v}</span>
                    </div>
                  ))}
                  <div className="mt-2 pt-2 border-t border-dark-700/30">
                    <p className="text-[11px] text-emerald-400 font-medium">Starting: $3,500/month per cluster</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Why DAC */}
            <div className="bg-dark-900 border border-oracle-red/20 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <Lock size={14} className="text-oracle-red" />
                <span className="text-xs font-semibold text-white flex-1">Why Dedicated AI Clusters for Production?</span>
                <InfoTip lines={[
                  { label: 'Compliance', value: 'DAC meets HIPAA, SOC2, PCI-DSS, GDPR — required for regulated industries (healthcare, finance, government)' },
                  { label: 'Performance', value: 'No noisy neighbors = consistent latency. Critical for SLA-bound production workloads.' },
                  { label: 'Custom Models', value: 'Import and deploy any Hugging Face model — Qwen, Mistral, Phi, or your own fine-tuned model', color: 'text-emerald-400' },
                  { label: 'Economics', value: 'At 50K+ queries/month, DAC is 40-60% cheaper than on-demand token pricing' },
                ]} />
              </div>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-2.5">
                {[
                  { icon: Lock, title: 'Data Sovereignty', desc: 'Full compliance with HIPAA, SOC2, PCI-DSS, GDPR. No data shared across tenants.', color: '#C74634' },
                  { icon: Server, title: 'Dedicated GPUs', desc: 'No noisy neighbors. Consistent latency with A10G or A100 GPUs dedicated to your workload.', color: '#0066CC' },
                  { icon: Brain, title: 'Custom Model Import', desc: 'Bring Qwen 2.5, Mistral, Phi-4, CodeLlama, or your own fine-tuned models.', color: '#76B900' },
                  { icon: DollarSign, title: 'Predictable Costs', desc: 'Fixed monthly with unlimited tokens. At 50K+ queries/month, 40-60% less than on-demand.', color: '#4CB848' },
                  { icon: Layers, title: 'Fine-Tuning', desc: 'Train construction, healthcare, or industry-specific models directly on your cluster.', color: '#8B5CF6' },
                  { icon: TrendingUp, title: 'Scale Without Limits', desc: 'Handle peak loads during audit season or bulk processing without throttling.', color: '#F0AB00' },
                ].map(({ icon: Icon, title, desc, color }) => (
                  <div key={title} className="bg-dark-800 border border-dark-700/50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1.5"><Icon size={13} style={{ color }} /><span className="text-[11px] text-white font-medium">{title}</span></div>
                    <p className="text-[11px] text-gray-500 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Models table */}
            <div className="bg-dark-900 border border-dark-700/50 rounded-lg overflow-hidden mb-3">
              <div className="px-4 py-2.5 border-b border-dark-700/50 flex items-center gap-2">
                <Brain size={13} className="text-oracle-red" />
                <span className="text-[11px] text-white font-semibold flex-1">Models Available on OCI GenAI DAC</span>
                <InfoTip lines={[
                  { label: 'Active', value: 'Currently deployed and running on this platform instance' },
                  { label: 'Available', value: 'Pre-hosted on OCI GenAI — can be activated on your DAC with no setup', color: 'text-emerald-400' },
                  { label: 'Import Ready', value: 'Third-party models that can be imported to your DAC from Hugging Face or custom sources' },
                  { label: 'DAC Only', value: 'Features exclusively available on Dedicated AI Clusters (not on-demand)' },
                ]} />
              </div>
              <table className="w-full text-[11px]">
                <thead><tr className="border-b border-dark-700/50 text-gray-500">
                  <th className="text-left px-4 py-2 font-medium">Model</th>
                  <th className="text-left px-2 py-2 font-medium">Provider</th>
                  <th className="text-right px-2 py-2 font-medium">Params</th>
                  <th className="text-left px-2 py-2 font-medium">Use Case</th>
                  <th className="text-right px-4 py-2 font-medium">Status</th>
                </tr></thead>
                <tbody>
                  {[
                    { m: 'Llama 4 Maverick', p: 'Meta / NVIDIA', s: '17B-128E', u: 'General AI, document analysis, RAG', st: 'Active', pr: true },
                    { m: 'Llama 3.3 70B', p: 'Meta', s: '70B', u: 'Complex reasoning, long documents', st: 'Available', pr: false },
                    { m: 'Cohere Command R+', p: 'Cohere', s: '104B', u: 'Enterprise RAG, multilingual', st: 'Available', pr: false },
                    { m: 'Qwen 2.5 72B', p: 'Alibaba (Import)', s: '72B', u: 'Multilingual, code generation', st: 'Import Ready', pr: false },
                    { m: 'Mistral Large 2', p: 'Mistral (Import)', s: '123B', u: 'European compliance, multilingual', st: 'Import Ready', pr: false },
                    { m: 'Phi-4', p: 'Microsoft (Import)', s: '14B', u: 'Lightweight inference, edge', st: 'Import Ready', pr: false },
                    { m: 'Custom Fine-Tuned', p: 'Your Organization', s: 'Any', u: 'Domain-specific extraction', st: 'DAC Only', pr: false },
                  ].map(({ m, p, s, u, st, pr }) => (
                    <tr key={m} className="border-b border-dark-700/20 hover:bg-dark-700/30">
                      <td className="px-4 py-2"><span className="text-gray-200">{m}</span>{pr && <span className="ml-1.5 text-[11px] px-1 py-0.5 bg-oracle-red/20 text-oracle-red rounded">CURRENT</span>}</td>
                      <td className="px-2 py-2 text-gray-400">{p}</td>
                      <td className="text-right px-2 py-2 text-gray-400">{s}</td>
                      <td className="px-2 py-2 text-gray-500 text-[11px]">{u}</td>
                      <td className="text-right px-4 py-2">
                        <span className={`text-[11px] px-1.5 py-0.5 rounded ${st === 'Active' ? 'bg-emerald-500/20 text-emerald-400' : st === 'Available' ? 'bg-blue-500/20 text-blue-400' : st === 'DAC Only' ? 'bg-oracle-red/20 text-oracle-red' : 'bg-amber-500/20 text-amber-400'}`}>{st}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* CTA */}
            <div className="bg-gradient-to-r from-oracle-red/10 to-blue-500/10 border border-oracle-red/20 rounded-lg p-4 text-center">
              <p className="text-sm text-white font-semibold mb-1">Ready for Production?</p>
              <p className="text-[11px] text-gray-400 mb-2 max-w-lg mx-auto">
                Upgrade from token-based POC to a Dedicated AI Cluster for enterprise-grade security, unlimited inference,
                and custom model deployment. Contact your Oracle AI Centre of Excellence (CoE) Team or Oracle AI Accelerator Team.
              </p>
              <div className="flex items-center justify-center gap-3">
                <span className="text-[11px] text-gray-500">Current: <span className="text-amber-400">On-Demand (POC)</span></span>
                <ArrowRight size={12} className="text-gray-600" />
                <span className="text-[11px] text-gray-500">Recommended: <span className="text-emerald-400 font-semibold">Dedicated AI Cluster</span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
