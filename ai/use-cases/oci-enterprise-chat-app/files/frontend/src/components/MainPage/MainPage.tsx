import React, { useState, useEffect, useCallback } from 'react';
import { User, Project, Document } from '../../types';
import { api } from '../../services/api';

interface MainPageProps {
  user: User;
  projects: Project[];
  onNavigateProjects: () => void;
  onProjectSelect: (project: Project) => void;
  showWelcome?: boolean;
  onWelcomeDismissed?: () => void;
}

interface WelcomeToastProps {
  userName: string;
  onClose: () => void;
}

const WelcomeToast: React.FC<WelcomeToastProps> = ({ userName, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-fade-in">
      <div className="flex items-center gap-3 px-6 py-3.5 bg-dark-800 border border-oracle-red/40 rounded-xl shadow-lg">
        <div className="w-8 h-8 rounded-full bg-oracle-red/20 flex items-center justify-center flex-shrink-0">
          <svg className="w-4 h-4 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <span className="text-white text-sm font-medium">
          Welcome back, {userName}!
        </span>
        <button onClick={onClose} className="ml-2 text-dark-400 hover:text-white transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

interface SearchResult {
  type: 'project' | 'document';
  id: string;
  title: string;
  subtitle: string;
  project?: Project;
}

const MainPage: React.FC<MainPageProps> = ({
  user,
  projects,
  onNavigateProjects,
  onProjectSelect,
  showWelcome,
  onWelcomeDismissed,
}) => {
  const totalFiles = projects.reduce((sum, p) => sum + p.document_ids.length, 0);
  const totalUrls = projects.reduce((sum, p) => sum + p.web_sources.length, 0);

  const [searchQuery, setSearchQuery] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);

  // Load all documents for search
  useEffect(() => {
    setIsLoadingDocs(true);
    api.listDocuments()
      .then(setDocuments)
      .catch(() => setDocuments([]))
      .finally(() => setIsLoadingDocs(false));
  }, []);

  const getSearchResults = useCallback((): SearchResult[] => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return [];

    const results: SearchResult[] = [];

    // Search projects
    for (const project of projects) {
      if (
        project.name.toLowerCase().includes(q) ||
        project.description.toLowerCase().includes(q)
      ) {
        results.push({
          type: 'project',
          id: project.id,
          title: project.name,
          subtitle: `${project.document_ids.length} files, ${project.web_sources.length} URLs`,
          project,
        });
      }
    }

    // Search documents
    for (const doc of documents) {
      if (doc.metadata.filename.toLowerCase().includes(q)) {
        // Find which project this doc belongs to
        const parentProject = projects.find((p) => p.document_ids.includes(doc.id));
        results.push({
          type: 'document',
          id: doc.id,
          title: doc.metadata.filename,
          subtitle: parentProject ? `in ${parentProject.name}` : 'Unassigned',
          project: parentProject,
        });
      }
    }

    return results.slice(0, 10);
  }, [searchQuery, projects, documents]);

  const searchResults = getSearchResults();
  const showResults = searchQuery.trim().length > 0;

  const handleResultClick = (result: SearchResult) => {
    if (result.project) {
      onProjectSelect(result.project);
    } else {
      onNavigateProjects();
    }
    setSearchQuery('');
  };

  return (
    <div className="flex-1 overflow-auto bg-dark-900 p-6">
      {/* Welcome toast */}
      {showWelcome && onWelcomeDismissed && (
        <WelcomeToast userName={user.full_name} onClose={onWelcomeDismissed} />
      )}

      <div className="max-w-4xl mx-auto">
        {/* Search section */}
        <div className="mb-10 pt-8">
          <h1 className="text-3xl font-bold text-white mb-2 text-center">
            Enterprise Knowledge Chat
          </h1>
          <p className="text-dark-300 text-center mb-6">
            Search across your projects and documents
          </p>
          <div className="relative max-w-2xl mx-auto">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-dark-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects and documents..."
              className="w-full pl-12 pr-10 py-3.5 bg-dark-800 border border-dark-600 rounded-xl text-white placeholder-dark-400 focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red transition-all text-sm"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-dark-400 hover:text-white transition-colors"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            )}

            {/* Search results dropdown */}
            {showResults && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-dark-800 border border-dark-600 rounded-xl shadow-modal overflow-hidden z-50 animate-scale-in">
                {isLoadingDocs ? (
                  <div className="px-4 py-3 text-sm text-dark-400">Searching...</div>
                ) : searchResults.length === 0 ? (
                  <div className="px-4 py-3 text-sm text-dark-400">
                    No results found for "{searchQuery}"
                  </div>
                ) : (
                  <div className="max-h-80 overflow-y-auto">
                    {searchResults.map((result) => (
                      <button
                        key={`${result.type}-${result.id}`}
                        onClick={() => handleResultClick(result)}
                        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-dark-700 transition-colors border-b border-dark-700 last:border-b-0"
                      >
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                          result.type === 'project'
                            ? 'bg-oracle-red/15'
                            : 'bg-red-500/15'
                        }`}>
                          {result.type === 'project' ? (
                            <svg className="w-4 h-4 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                          ) : (
                            <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-white text-sm font-medium truncate">{result.title}</p>
                          <p className="text-dark-400 text-xs truncate">{result.subtitle}</p>
                        </div>
                        <span className="ml-auto text-xs text-dark-500 flex-shrink-0 capitalize">
                          {result.type}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Stats cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          <div className="bg-dark-800 rounded-xl border border-dark-700 p-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-oracle-red/15 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-white">{projects.length}</p>
            <p className="text-sm text-dark-400">Projects</p>
          </div>

          <div className="bg-dark-800 rounded-xl border border-dark-700 p-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-oracle-red/15 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-white">{totalFiles}</p>
            <p className="text-sm text-dark-400">Documents</p>
          </div>

          <div className="bg-dark-800 rounded-xl border border-dark-700 p-6 text-center">
            <div className="w-12 h-12 rounded-xl bg-oracle-red/15 flex items-center justify-center mx-auto mb-3">
              <svg className="w-6 h-6 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
              </svg>
            </div>
            <p className="text-2xl font-bold text-white">{totalUrls}</p>
            <p className="text-sm text-dark-400">Web Sources</p>
          </div>
        </div>

        {/* Quick actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
          <button
            onClick={onNavigateProjects}
            className="bg-dark-800 rounded-xl border border-dark-700 hover:border-oracle-red/50 p-6 text-left transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-oracle-red/15 group-hover:bg-oracle-red/25 flex items-center justify-center transition-colors">
                <svg className="w-6 h-6 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg group-hover:text-oracle-red transition-colors">
                  View Projects
                </h3>
                <p className="text-dark-400 text-sm">
                  Manage your projects, upload documents, and add web sources
                </p>
              </div>
              <svg className="w-5 h-5 text-dark-500 group-hover:text-oracle-red ml-auto transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>

          <button
            onClick={onNavigateProjects}
            className="bg-dark-800 rounded-xl border border-dark-700 hover:border-oracle-red/50 p-6 text-left transition-all group"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-oracle-red/15 group-hover:bg-oracle-red/25 flex items-center justify-center transition-colors">
                <svg className="w-6 h-6 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div>
                <h3 className="text-white font-semibold text-lg group-hover:text-oracle-red transition-colors">
                  Create New Project
                </h3>
                <p className="text-dark-400 text-sm">
                  Start a new project for document analysis and chat
                </p>
              </div>
              <svg className="w-5 h-5 text-dark-500 group-hover:text-oracle-red ml-auto transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        </div>

        {/* Capabilities */}
        <div className="bg-dark-800 rounded-xl border border-dark-700 p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Platform Capabilities</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-oracle-red/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-medium text-sm">Document Upload</h4>
                <p className="text-dark-400 text-xs mt-1">Upload PDFs for automatic parameter extraction and analysis</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-oracle-red/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-medium text-sm">AI Chat</h4>
                <p className="text-dark-400 text-xs mt-1">Chat with your documents using RAG-powered AI</p>
              </div>
            </div>
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-lg bg-oracle-red/15 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-4 h-4 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <div>
                <h4 className="text-white font-medium text-sm">Parameter Extraction</h4>
                <p className="text-dark-400 text-xs mt-1">Automatically extract key data with confidence scoring</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainPage;
