interface HomePageProps {
  onNavigate: (page: 'home' | 'dashboard' | 'agents') => void;
}

const VALUE_PROPS = [
  {
    title: 'Any Brand',
    description:
      'Analyze customer sentiment for any brand — Nike, Coca Cola, Apple, or your own. Simply enter a brand name and let the agents do the work.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  {
    title: 'In-Database AI',
    description:
      'Sentiment analysis runs inside Oracle Autonomous Database via DBMS_CLOUD_AI.GENERATE — no data movement, maximum performance.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    title: 'Autonomous Agents',
    description:
      'A 6-step agent pipeline autonomously searches the web, ingests reviews, analyzes sentiment, and generates marketing recommendations.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    title: 'AI Campaign Studio',
    description:
      'Turn sentiment insights into action — GenAI generates personalized marketing email variants informed by real customer feedback and emotions.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: 'RAG Knowledge Base',
    description:
      'Ask natural language questions over your document library — Select AI RAG uses vector search with Cohere embeddings to retrieve and synthesize answers.',
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
];

const PIPELINE_STEPS = [
  { label: 'Query Gen', sub: 'OCI GenAI', icon: '1' },
  { label: 'Web Search', sub: 'DuckDuckGo', icon: '2' },
  { label: 'Ingestion', sub: 'Oracle ADB', icon: '3' },
  { label: 'Sentiment', sub: 'DBMS_CLOUD_AI', icon: '4' },
  { label: 'Analytics', sub: 'Select AI', icon: '5' },
  { label: 'Actions', sub: 'OCI GenAI', icon: '6' },
];

const FRONTEND_STACK = [
  { name: 'React 19', desc: 'UI Framework' },
  { name: 'TypeScript', desc: 'Type Safety' },
  { name: 'Vite', desc: 'Build Tool' },
  { name: 'Tailwind CSS', desc: 'Styling' },
  { name: 'Chart.js', desc: 'Visualization' },
];

const BACKEND_STACK = [
  { name: 'FastAPI', desc: 'REST API' },
  { name: 'Oracle ADB', desc: 'Database & In-DB AI' },
  { name: 'OCI GenAI', desc: 'Cohere Command A' },
  { name: 'Select AI', desc: 'NL2SQL & RAG' },
  { name: 'DuckDuckGo', desc: 'Web Search' },
];

export default function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div className="min-h-screen bg-primary">
      {/* ── Hero ── */}
      <section className="relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute top-[-200px] left-[-100px] w-[500px] h-[500px] rounded-full bg-accent/5 blur-[120px] pointer-events-none" />
        <div className="absolute bottom-[-200px] right-[-100px] w-[600px] h-[600px] rounded-full bg-accent2/5 blur-[120px] pointer-events-none" />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
          {/* Badge */}
          <div
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white border border-gray-200 shadow-sm mb-8"
            style={{ animation: 'fade-in 0.6s ease-out both' }}
          >
            <span className="w-2 h-2 rounded-full bg-green-600" />
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              Powered by Oracle Cloud AI
            </span>
          </div>

          {/* Title */}
          <h1
            className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight mb-6"
            style={{ animation: 'slide-in-up 0.6s ease-out 0.1s both' }}
          >
            <span className="text-gray-900">Sentiment</span>{' '}
            <span className="bg-gradient-to-r from-accent to-[#E8634E] bg-clip-text text-transparent">
              Intelligence
            </span>
          </h1>

          {/* Subtitle */}
          <p
            className="text-lg sm:text-xl text-gray-500 max-w-2xl mx-auto mb-4 leading-relaxed"
            style={{ animation: 'slide-in-up 0.6s ease-out 0.2s both' }}
          >
            AI-powered brand monitoring that searches the web, analyzes customer sentiment
            <span className="text-gray-900 font-medium"> inside the database</span>, generates
            actionable insights, creates <span className="text-gray-900 font-medium">personalized marketing campaigns</span>,
            and answers questions over your <span className="text-gray-900 font-medium">document knowledge base</span> — all autonomously.
          </p>

          <p
            className="text-sm text-gray-400 max-w-xl mx-auto mb-10"
            style={{ animation: 'slide-in-up 0.6s ease-out 0.3s both' }}
          >
            Enter any brand name. Our 6-agent pipeline does the rest — from web discovery
            to sentiment analytics to strategy recommendations.
          </p>

          {/* CTA */}
          <div
            className="flex items-center justify-center gap-4"
            style={{ animation: 'slide-in-up 0.6s ease-out 0.4s both' }}
          >
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-8 py-3 rounded-xl text-base font-semibold bg-accent text-white hover:bg-accent/90 transition-all shadow-lg shadow-accent/20 flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
              </svg>
              Get Started
            </button>
            <button
              onClick={() => onNavigate('agents')}
              className="px-8 py-3 rounded-xl text-base font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:text-gray-900 transition-all shadow-sm"
            >
              View Agent Pipeline
            </button>
          </div>
        </div>
      </section>

      {/* ── Value Proposition ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2
          className="text-center text-xs font-bold uppercase tracking-[0.2em] text-gray-400 mb-10"
          style={{ animation: 'fade-in 0.6s ease-out 0.5s both' }}
        >
          Why This Demo Matters
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {VALUE_PROPS.map((vp, i) => (
            <div
              key={vp.title}
              className="glass-card p-6 hover:ring-1 hover:ring-accent/20 transition-all group"
              style={{ animation: `slide-in-up 0.5s ease-out ${0.5 + i * 0.1}s both` }}
            >
              <div className="w-14 h-14 rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-4 group-hover:bg-accent/15 transition-colors">
                {vp.icon}
              </div>
              <h3 className="text-base font-bold text-gray-900 mb-2">{vp.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{vp.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How It Works ── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-center text-xs font-bold uppercase tracking-[0.2em] text-gray-400 mb-10">
          How It Works
        </h2>
        <div className="flex flex-wrap items-start justify-center gap-3 lg:gap-0">
          {PIPELINE_STEPS.map((step, i) => (
            <div key={step.label} className="flex items-center">
              <div
                className="flex flex-col items-center text-center w-28"
                style={{ animation: `slide-in-up 0.4s ease-out ${0.1 + i * 0.08}s both` }}
              >
                <div className="w-12 h-12 rounded-xl bg-accent text-white flex items-center justify-center text-lg font-bold mb-2 shadow-lg shadow-accent/20">
                  {step.icon}
                </div>
                <span className="text-xs font-semibold text-gray-900">{step.label}</span>
                <span className="text-[10px] text-gray-400 mt-0.5">{step.sub}</span>
              </div>
              {i < PIPELINE_STEPS.length - 1 && (
                <div className="hidden lg:flex items-center mx-1 mt-[-20px]">
                  <svg className="w-8 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 32 16">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2 8h24m0 0l-6-6m6 6l-6 6" />
                  </svg>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── Tech Stack ── */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <h2 className="text-center text-xs font-bold uppercase tracking-[0.2em] text-gray-400 mb-10">
          Tech Stack
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Frontend */}
          <div className="glass-card p-6" style={{ animation: 'slide-in-up 0.5s ease-out 0.2s both' }}>
            <h3 className="text-xs font-bold uppercase tracking-wider text-accent mb-4 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Frontend
            </h3>
            <div className="space-y-2.5">
              {FRONTEND_STACK.map((tech) => (
                <div key={tech.name} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{tech.name}</span>
                  <span className="text-xs text-gray-400">{tech.desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Backend */}
          <div className="glass-card p-6" style={{ animation: 'slide-in-up 0.5s ease-out 0.3s both' }}>
            <h3 className="text-xs font-bold uppercase tracking-wider text-accent mb-4 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
              </svg>
              Backend
            </h3>
            <div className="space-y-2.5">
              {BACKEND_STACK.map((tech) => (
                <div key={tech.name} className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900">{tech.name}</span>
                  <span className="text-xs text-gray-400">{tech.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Bottom CTA ── */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16 text-center">
        <div className="glass-card p-8" style={{ animation: 'fade-in 0.6s ease-out 0.3s both' }}>
          <h2 className="text-xl font-bold text-gray-900 mb-3">Ready to explore?</h2>
          <p className="text-sm text-gray-500 mb-6">
            Open the dashboard to analyze a brand, or view the agent pipeline to see how the autonomous workflow operates.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button
              onClick={() => onNavigate('dashboard')}
              className="px-6 py-2.5 rounded-lg text-sm font-semibold bg-accent text-white hover:bg-accent/90 transition-all shadow-lg shadow-accent/20 flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Open Dashboard
            </button>
            <button
              onClick={() => onNavigate('agents')}
              className="px-6 py-2.5 rounded-lg text-sm font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:text-gray-900 transition-all shadow-sm flex items-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
              View Agent Pipeline
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-6 border-t border-gray-200">
        <p className="text-[10px] text-gray-400 uppercase tracking-widest">
          Sentiment Intelligence &mdash; Powered by Oracle Cloud AI &amp; Select AI
        </p>
      </footer>
    </div>
  );
}
