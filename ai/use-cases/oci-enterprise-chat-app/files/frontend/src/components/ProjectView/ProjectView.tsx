import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { projectService } from '../../services/projectService';
import { Project, Document, WebSource, User, WordFrequency } from '../../types';
import WordCloud from '../WordCloud/WordCloud';

interface ProjectViewProps {
  user: User;
  project: Project;
  onBack: () => void;
  onViewDocument: (document: Document) => void;
  onStartChat: (
    documents: Document[],
    webSources: WebSource[],
    projectName: string
  ) => void;
  onProjectChange: () => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'completed':
      return 'text-green-400 bg-green-400/10';
    case 'processing':
      return 'text-yellow-400 bg-yellow-400/10';
    case 'failed':
      return 'text-red-400 bg-red-400/10';
    default:
      return 'text-blue-400 bg-blue-400/10';
  }
};

const ProjectView: React.FC<ProjectViewProps> = ({
  user,
  project,
  onBack,
  onViewDocument,
  onStartChat,
  onProjectChange,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Web URL form state
  const [showUrlForm, setShowUrlForm] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [newUrlTitle, setNewUrlTitle] = useState('');
  const [isScrapingUrl, setIsScrapingUrl] = useState(false);

  // Tag management
  const [tagInput, setTagInput] = useState('');
  const [showTagInput, setShowTagInput] = useState(false);

  // Word cloud state
  const [showWordCloud, setShowWordCloud] = useState(false);
  const [wordCloudData, setWordCloudData] = useState<WordFrequency[] | null>(null);
  const [wordCloudLoading, setWordCloudLoading] = useState(false);
  const [wordCloudError, setWordCloudError] = useState<string | null>(null);
  const [wordCloudStats, setWordCloudStats] = useState<{ totalDocs: number; totalWords: number } | null>(null);

  // Active tab
  const [activeTab, setActiveTab] = useState<'files' | 'urls'>('files');

  const loadDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      const allDocs = await api.listDocuments();
      const projectDocs = allDocs.filter((doc) =>
        project.document_ids.includes(doc.id)
      );
      setDocuments(projectDocs);
      setError(null);
    } catch (err) {
      setError('Failed to load documents');
      console.error('Error loading documents:', err);
    } finally {
      setIsLoading(false);
    }
  }, [project.document_ids]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (!file.name.toLowerCase().endsWith('.pdf')) {
          setError(`Skipped ${file.name}: Only PDF files are supported`);
          continue;
        }

        setUploadProgress(Math.round(((i) / files.length) * 100));

        const response = await api.uploadDocument(file, (progress) => {
          const overallProgress = Math.round(
            ((i + progress / 100) / files.length) * 100
          );
          setUploadProgress(overallProgress);
        });

        // Add document to project
        projectService.addDocumentToProject(project.id, response.document_id);

        // Start extraction
        await api.extractParameters(response.document_id);
      }

      onProjectChange();
      await loadDocuments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      e.target.value = '';
    }
  };

  const handleRemoveDocument = async (docId: string) => {
    projectService.removeDocumentFromProject(project.id, docId);
    onProjectChange();
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
  };

  const handleAddWebUrl = async () => {
    if (!newUrl.trim()) return;
    try {
      new URL(newUrl.trim());
    } catch {
      setError('Please enter a valid URL');
      return;
    }

    setIsScrapingUrl(true);
    setError(null);

    try {
      const response = await api.scrapeWebUrl(newUrl.trim(), newUrlTitle.trim());
      projectService.addWebSourceWithId(
        project.id,
        response.id,
        response.url,
        response.title,
        response.status
      );
      setNewUrl('');
      setNewUrlTitle('');
      setShowUrlForm(false);
      onProjectChange();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to scrape URL');
    } finally {
      setIsScrapingUrl(false);
    }
  };

  const handleRemoveWebSource = async (wsId: string) => {
    try {
      await api.deleteWebSource(wsId);
    } catch (err) {
      console.error('Failed to delete web source from backend:', err);
    }
    projectService.removeWebSource(project.id, wsId);
    onProjectChange();
  };

  const handleAddTag = () => {
    const tag = tagInput.trim();
    if (!tag) return;
    const currentTags = project.tags || [];
    if (currentTags.includes(tag)) {
      setTagInput('');
      return;
    }
    projectService.updateProject(project.id, { tags: [...currentTags, tag] });
    setTagInput('');
    setShowTagInput(false);
    onProjectChange();
  };

  const handleRemoveTag = (tag: string) => {
    const currentTags = project.tags || [];
    projectService.updateProject(project.id, { tags: currentTags.filter((t) => t !== tag) });
    onProjectChange();
  };

  const handleGenerateWordCloud = async () => {
    if (project.document_ids.length === 0) return;
    setShowWordCloud(true);
    setWordCloudLoading(true);
    setWordCloudError(null);
    setWordCloudData(null);
    setWordCloudStats(null);

    try {
      const response = await api.getWordCloud(project.document_ids, 100);
      setWordCloudData(response.words);
      setWordCloudStats({
        totalDocs: response.total_documents,
        totalWords: response.total_words_processed,
      });
    } catch (err: any) {
      setWordCloudError(
        err.response?.data?.detail || 'Failed to generate word cloud'
      );
    } finally {
      setWordCloudLoading(false);
    }
  };

  const handleStartChat = () => {
    onStartChat(documents, project.web_sources, project.name);
  };

  const totalSources = documents.length + project.web_sources.length;

  return (
    <div className="flex-1 overflow-auto bg-dark-900">
      {/* Project Header */}
      <div className="bg-dark-800 border-b border-dark-700 px-6 py-5">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={onBack}
            className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-md transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">{project.name}</h1>
            {project.description && (
              <p className="text-sm text-dark-400 mt-0.5">{project.description}</p>
            )}
            {/* Tags */}
            <div className="flex flex-wrap items-center gap-1.5 mt-2">
              {(project.tags || []).map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-oracle-red/10 text-oracle-red text-xs font-medium rounded-full group/tag"
                >
                  {tag}
                  <button
                    onClick={(e) => { e.stopPropagation(); handleRemoveTag(tag); }}
                    className="opacity-0 group-hover/tag:opacity-100 hover:text-white transition-all"
                    title="Remove tag"
                  >
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </span>
              ))}
              {showTagInput ? (
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    placeholder="Tag name..."
                    className="px-2 py-0.5 bg-dark-700 border border-dark-600 rounded-full text-xs text-white placeholder-dark-400 focus:outline-none focus:border-oracle-red w-24"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleAddTag();
                      if (e.key === 'Escape') { setShowTagInput(false); setTagInput(''); }
                    }}
                    onBlur={() => {
                      if (!tagInput.trim()) { setShowTagInput(false); setTagInput(''); }
                    }}
                  />
                </div>
              ) : (
                <button
                  onClick={() => setShowTagInput(true)}
                  className="px-2 py-0.5 border border-dashed border-dark-500 hover:border-oracle-red/50 text-dark-400 hover:text-oracle-red text-xs rounded-full transition-colors"
                >
                  + Add tag
                </button>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleGenerateWordCloud}
              disabled={project.document_ids.length === 0}
              className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 hover:text-white font-medium rounded-lg transition-colors flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed border border-dark-600"
              title={project.document_ids.length === 0 ? 'Upload documents first' : 'Generate word cloud from all documents'}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.002 4.002 0 003 15z" />
              </svg>
              Word Cloud
            </button>
            <button
              onClick={handleStartChat}
              disabled={totalSources === 0}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              Chat with Sources
            </button>
          </div>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm text-dark-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span>{documents.length} file{documents.length !== 1 ? 's' : ''}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-dark-400">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            <span>{project.web_sources.length} web source{project.web_sources.length !== 1 ? 's' : ''}</span>
          </div>
          <span className="text-xs text-dark-500">
            Created {formatDate(project.created_at)}
          </span>
        </div>
      </div>

      <div className="p-6">
        {/* Error */}
        {error && (
          <div className="mb-4 bg-red-900/20 border border-red-500/50 text-red-400 px-4 py-3 rounded-md flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">&times;</button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 mb-6 bg-dark-800 rounded-lg p-1 w-fit">
          <button
            onClick={() => setActiveTab('files')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'files'
                ? 'bg-dark-600 text-white'
                : 'text-dark-400 hover:text-dark-200'
            }`}
          >
            Files ({documents.length})
          </button>
          <button
            onClick={() => setActiveTab('urls')}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'urls'
                ? 'bg-dark-600 text-white'
                : 'text-dark-400 hover:text-dark-200'
            }`}
          >
            Web URLs ({project.web_sources.length})
          </button>
        </div>

        {/* Files Tab */}
        {activeTab === 'files' && (
          <div>
            {/* Upload action */}
            <div className="flex items-center gap-3 mb-4">
              <label className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white font-medium rounded-md cursor-pointer transition-colors flex items-center gap-2">
                <input
                  type="file"
                  accept=".pdf"
                  multiple
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={isUploading}
                />
                {isUploading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Uploading {uploadProgress}%
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Upload Files
                  </span>
                )}
              </label>
              <span className="text-sm text-dark-500">PDF files supported. You can select multiple files.</span>
            </div>

            {/* Files list */}
            {isLoading ? (
              <div className="flex items-center justify-center py-16">
                <svg className="animate-spin h-8 w-8 text-oracle-red" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
            ) : documents.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 bg-dark-800 rounded-lg border border-dark-700">
                <svg className="w-12 h-12 text-dark-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-base font-medium text-white mb-1">No files yet</h3>
                <p className="text-dark-400 text-sm">Upload PDF files to add them to this project</p>
              </div>
            ) : (
              <div className="bg-dark-800 rounded-lg border border-dark-700 overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-dark-700">
                      <th className="px-4 py-3 text-left text-sm font-medium text-dark-300">Document</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-dark-300">Status</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-dark-300">Size</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-dark-300">Pages</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-dark-300">Uploaded</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-dark-300">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {documents.map((doc) => (
                      <tr key={doc.id} className="border-b border-dark-700 last:border-b-0 hover:bg-dark-700/50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-red-500/20 rounded flex items-center justify-center flex-shrink-0">
                              <svg className="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <span className="text-white font-medium truncate max-w-xs">{doc.metadata.filename}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                            {doc.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-dark-300 text-sm">{formatFileSize(doc.metadata.file_size)}</td>
                        <td className="px-4 py-3 text-dark-300 text-sm">{doc.metadata.page_count || '-'}</td>
                        <td className="px-4 py-3 text-dark-300 text-sm">{formatDate(doc.created_at)}</td>
                        <td className="px-4 py-3">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => onViewDocument(doc)}
                              className="p-1.5 text-dark-400 hover:text-white hover:bg-dark-600 rounded transition-colors"
                              title="View document"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                            </button>
                            <button
                              onClick={() => handleRemoveDocument(doc.id)}
                              className="p-1.5 text-dark-400 hover:text-red-400 hover:bg-dark-600 rounded transition-colors"
                              title="Remove from project"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Web URLs Tab */}
        {activeTab === 'urls' && (
          <div>
            {/* Add URL action */}
            <div className="mb-4">
              {showUrlForm ? (
                <div className="bg-dark-800 rounded-lg border border-dark-600 p-4 space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-dark-200 mb-1">URL</label>
                    <input
                      type="url"
                      value={newUrl}
                      onChange={(e) => setNewUrl(e.target.value)}
                      placeholder="https://example.com/article"
                      className="input-field w-full"
                      autoFocus
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-dark-200 mb-1">
                      Title <span className="text-dark-500">(optional)</span>
                    </label>
                    <input
                      type="text"
                      value={newUrlTitle}
                      onChange={(e) => setNewUrlTitle(e.target.value)}
                      placeholder="A descriptive title for this source"
                      className="input-field w-full"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleAddWebUrl();
                      }}
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => {
                        setShowUrlForm(false);
                        setNewUrl('');
                        setNewUrlTitle('');
                      }}
                      className="btn-secondary text-sm"
                      disabled={isScrapingUrl}
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleAddWebUrl}
                      disabled={!newUrl.trim() || isScrapingUrl}
                      className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                      {isScrapingUrl ? (
                        <>
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                          </svg>
                          Scraping & Indexing...
                        </>
                      ) : (
                        'Add URL'
                      )}
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setShowUrlForm(true)}
                  className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white font-medium rounded-md transition-colors flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Add Web URL
                </button>
              )}
            </div>

            {/* Web sources list */}
            {project.web_sources.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 bg-dark-800 rounded-lg border border-dark-700">
                <svg className="w-12 h-12 text-dark-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
                <h3 className="text-base font-medium text-white mb-1">No web sources yet</h3>
                <p className="text-dark-400 text-sm">Add web URLs as additional knowledge sources</p>
              </div>
            ) : (
              <div className="space-y-2">
                {project.web_sources.map((ws) => (
                  <div
                    key={ws.id}
                    className="bg-dark-800 rounded-lg border border-dark-700 px-4 py-3 flex items-center gap-4 group hover:border-dark-600 transition-colors"
                  >
                    <div className="w-8 h-8 bg-blue-500/20 rounded flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-medium text-sm truncate">
                        {ws.title || ws.url}
                      </p>
                      <p className="text-dark-500 text-xs truncate">{ws.url}</p>
                    </div>
                    {ws.status && ws.status !== 'completed' && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                        ws.status === 'failed' ? 'text-red-400 bg-red-400/10' :
                        'text-yellow-400 bg-yellow-400/10'
                      }`}>
                        {ws.status}
                      </span>
                    )}
                    {ws.status === 'completed' && ws.content_length && (
                      <span className="text-xs text-dark-500 flex-shrink-0">
                        {(ws.content_length / 1024).toFixed(1)} KB
                      </span>
                    )}
                    <span className="text-xs text-dark-500 flex-shrink-0">
                      {formatDate(ws.added_at)}
                    </span>
                    <button
                      onClick={() => handleRemoveWebSource(ws.id)}
                      className="p-1.5 text-dark-500 hover:text-red-400 hover:bg-dark-700 rounded opacity-0 group-hover:opacity-100 transition-all flex-shrink-0"
                      title="Remove URL"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Word Cloud Modal */}
      {showWordCloud && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setShowWordCloud(false)}
        >
          <div
            className="bg-dark-800 rounded-2xl border border-dark-600 shadow-modal w-full max-w-3xl mx-4 animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-dark-700">
              <div>
                <h2 className="text-lg font-bold text-white">Word Cloud</h2>
                <p className="text-sm text-dark-400">
                  Generated from documents in {project.name}
                </p>
              </div>
              <button
                onClick={() => setShowWordCloud(false)}
                className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div className="px-6 py-6">
              {wordCloudLoading ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <svg className="animate-spin h-10 w-10 text-oracle-red mb-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <p className="text-dark-400 text-sm">Extracting text and generating word cloud...</p>
                </div>
              ) : wordCloudError ? (
                <div className="flex flex-col items-center justify-center py-16">
                  <svg className="w-12 h-12 text-red-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                  <p className="text-red-400 text-sm">{wordCloudError}</p>
                  <button
                    onClick={handleGenerateWordCloud}
                    className="mt-3 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white text-sm rounded-lg transition-colors"
                  >
                    Retry
                  </button>
                </div>
              ) : wordCloudData && wordCloudData.length > 0 ? (
                <div className="flex flex-col items-center">
                  <div className="bg-dark-900 rounded-xl border border-dark-700 p-4 overflow-hidden">
                    <WordCloud words={wordCloudData} width={640} height={380} />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16">
                  <p className="text-dark-400 text-sm">No words extracted from the documents.</p>
                </div>
              )}
            </div>

            {/* Footer stats */}
            {wordCloudStats && !wordCloudLoading && (
              <div className="px-6 py-3 border-t border-dark-700 flex items-center gap-6 text-xs text-dark-500">
                <span>{wordCloudStats.totalDocs} document{wordCloudStats.totalDocs !== 1 ? 's' : ''} analyzed</span>
                <span>{wordCloudStats.totalWords.toLocaleString()} words processed</span>
                <span>{wordCloudData?.length || 0} unique terms displayed</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectView;
