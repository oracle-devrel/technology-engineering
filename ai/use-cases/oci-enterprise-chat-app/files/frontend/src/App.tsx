import React, { useState, useCallback, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import Header from './components/Header/Header';
import Sidebar from './components/Sidebar/Sidebar';
import Login from './components/Login/Login';
import Dashboard from './components/Dashboard/Dashboard';
import HomePage from './components/HomePage/HomePage';
import AllDocuments from './components/AllDocuments/AllDocuments';
import ProjectView from './components/ProjectView/ProjectView';
import Chat from './components/Chat/Chat';
import PdfViewer from './components/PdfViewer/PdfViewer';
import ExtractionPanel from './components/ExtractionPanel/ExtractionPanel';
import UserProfilePage from './components/UserProfileMenu/UserProfileMenu';
import SystemSettings from './components/SystemSettings/SystemSettings';
import BatchProcessing from './components/BatchProcessing/BatchProcessing';
import WorkflowBuilder from './components/WorkflowBuilder/WorkflowBuilder';
import Research from './components/Research/Research';
import Compliance from './components/Compliance/Compliance';
import Benchmarking from './components/Benchmarking/Benchmarking';
import BusinessImpact from './components/BusinessImpact/BusinessImpact';
import HelpSupport from './components/HelpSupport/HelpSupport';
import { api } from './services/api';
import { projectService } from './services/projectService';
import { User, Document, Project, WebSource, ExtractedParameter, ProcessingStatus } from './types';

// Derive the active nav section from the current path
function getNavView(pathname: string): string {
  if (pathname === '/') return 'home';
  if (pathname.startsWith('/projects')) return 'projects';
  if (pathname.startsWith('/chat')) return 'chat';
  if (pathname.startsWith('/document')) return 'document';
  if (pathname.startsWith('/settings')) return 'settings';
  if (pathname.startsWith('/profile')) return 'profile';
  if (pathname.startsWith('/batch')) return 'batch';
  if (pathname.startsWith('/workflows')) return 'workflows';
  if (pathname.startsWith('/research')) return 'research';
  if (pathname.startsWith('/compliance')) return 'compliance';
  if (pathname.startsWith('/benchmark')) return 'benchmark';
  if (pathname.startsWith('/impact')) return 'impact';
  return 'home';
}

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentView = getNavView(location.pathname);

  // Auth state
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [showWelcome, setShowWelcome] = useState(false);

  // View state
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const [chatDocuments, setChatDocuments] = useState<Document[]>([]);
  const [chatWebSources, setChatWebSources] = useState<WebSource[]>([]);
  const [chatProjectName, setChatProjectName] = useState<string>('');

  // Project state
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');

  // Model selection state
  const [selectedInferenceModel, setSelectedInferenceModel] = useState(
    () => localStorage.getItem('selectedInferenceModel') || ''
  );
  const [selectedEmbeddingModel, setSelectedEmbeddingModel] = useState(
    () => localStorage.getItem('selectedEmbeddingModel') || ''
  );

  // Document view state (for extraction panel)
  const [status, setStatus] = useState<ProcessingStatus>('idle');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [parameters, setParameters] = useState<ExtractedParameter[] | null>(null);
  const [currentFileName, setCurrentFileName] = useState<string>();
  const [error, setError] = useState<string>();
  const [highlightedParam, setHighlightedParam] = useState<ExtractedParameter | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        try {
          const currentUser = await api.getCurrentUser();
          setUser(currentUser);
        } catch {
          localStorage.removeItem('auth_token');
        }
      }
      setIsAuthLoading(false);
    };
    checkAuth();
  }, []);

  // Load projects
  const loadProjects = useCallback(() => {
    setProjects(projectService.listProjects());
  }, []);

  useEffect(() => {
    if (user) {
      loadProjects();
    }
  }, [user, loadProjects]);

  const handleProjectSelect = useCallback((project: Project) => {
    setSelectedProject(project);
    navigate(`/projects/${project.id}`);
  }, [navigate]);

  const handleProjectsChange = useCallback(() => {
    loadProjects();
    if (selectedProject) {
      const updated = projectService.getProject(selectedProject.id);
      if (updated) {
        setSelectedProject(updated);
      }
    }
  }, [loadProjects, selectedProject]);

  const handleLoginSuccess = (loggedInUser: User, token: string) => {
    localStorage.setItem('auth_token', token);
    setUser(loggedInUser);
    setShowWelcome(true);
  };

  const handleUserUpdate = useCallback((updatedUser: User) => {
    setUser(updatedUser);
  }, []);

  const handleInferenceModelChange = useCallback((model: string) => {
    setSelectedInferenceModel(model);
    localStorage.setItem('selectedInferenceModel', model);
  }, []);

  const handleEmbeddingModelChange = useCallback((model: string) => {
    setSelectedEmbeddingModel(model);
    localStorage.setItem('selectedEmbeddingModel', model);
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // Ignore logout errors
    }
    localStorage.removeItem('auth_token');
    setUser(null);
    setSelectedDocument(null);
    setChatDocuments([]);
    setChatWebSources([]);
    setSelectedProject(null);
    navigate('/');
  };

  const handleViewDocument = useCallback(async (document: Document) => {
    setSelectedDocument(document);
    setCurrentFileName(document.metadata.filename);
    setError(undefined);

    const pdfViewUrl = api.getPdfUrl(document.id);
    setPdfUrl(pdfViewUrl);

    if (document.extraction_result) {
      setParameters(document.extraction_result.parameters);
      setStatus(document.status === 'completed' ? 'completed' : 'error');
    } else if (document.status === 'processing') {
      setStatus('processing');
      setParameters(null);

      try {
        await api.pollDocumentStatus(
          document.id,
          2000,
          60,
          (statusUpdate) => {
            if (statusUpdate.extracted_parameters) {
              setParameters(statusUpdate.extracted_parameters);
            }
          }
        );

        const finalStatus = await api.getDocumentStatus(document.id);
        if (finalStatus.status === 'completed' && finalStatus.extracted_parameters) {
          setParameters(finalStatus.extracted_parameters);
          setStatus('completed');
        } else if (finalStatus.status === 'error') {
          setError(finalStatus.error || 'Extraction failed');
          setStatus('error');
        }
      } catch (err) {
        setError('Failed to get extraction status');
        setStatus('error');
      }
    } else {
      setStatus('idle');
      setParameters(null);
    }

    navigate('/document');
  }, [navigate]);

  const handleChatWithDocuments = useCallback((documents: Document[], webSources: WebSource[] = [], projectName: string = '') => {
    setChatDocuments(documents);
    setChatWebSources(webSources);
    setChatProjectName(projectName);
    navigate('/chat');
  }, [navigate]);

  const clearDocumentState = useCallback(() => {
    setSelectedDocument(null);
    setChatDocuments([]);
    setChatWebSources([]);
    setPdfUrl(null);
    setParameters(null);
    setStatus('idle');
    setError(undefined);
    setHighlightedParam(null);
  }, []);

  const handleNavigateHome = useCallback(() => {
    setSelectedProject(null);
    clearDocumentState();
    navigate('/');
  }, [navigate, clearDocumentState]);

  const handleNavigateProjects = useCallback(() => {
    setSelectedProject(null);
    clearDocumentState();
    navigate('/projects');
  }, [navigate, clearDocumentState]);

  const handleBackToProject = useCallback(() => {
    clearDocumentState();
    if (selectedProject) {
      navigate(`/projects/${selectedProject.id}`);
    } else {
      navigate('/projects');
    }
  }, [selectedProject, navigate, clearDocumentState]);

  const handleParameterClick = useCallback((param: ExtractedParameter) => {
    setHighlightedParam(prev =>
      prev && prev.name === param.name && String(prev.value) === String(param.value)
        ? null
        : param
    );
  }, []);

  const handleFileSelect = useCallback(async (file: File) => {
    try {
      setError(undefined);
      setParameters(null);
      setStatus('uploading');
      setCurrentFileName(file.name);

      const uploadResponse = await api.uploadDocument(file, (progress) => {
        console.log(`Upload progress: ${progress}%`);
      });

      const localPdfUrl = URL.createObjectURL(file);
      setPdfUrl(localPdfUrl);

      setStatus('processing');

      try {
        await api.extractParameters(uploadResponse.document_id);

        await api.pollDocumentStatus(
          uploadResponse.document_id,
          2000,
          60,
          (statusUpdate) => {
            if (statusUpdate.extracted_parameters) {
              setParameters(statusUpdate.extracted_parameters);
            }
          }
        );

        const finalStatus = await api.getDocumentStatus(uploadResponse.document_id);

        if (finalStatus.status === 'completed' && finalStatus.extracted_parameters) {
          setParameters(finalStatus.extracted_parameters);
          setStatus('completed');
        } else if (finalStatus.status === 'error') {
          setError(finalStatus.error || 'Extraction failed');
          setStatus('error');
        }
      } catch (extractionError) {
        console.error('Extraction error:', extractionError);
        setError(
          extractionError instanceof Error
            ? extractionError.message
            : 'Failed to extract parameters'
        );
        setStatus('error');
      }
    } catch (uploadError) {
      console.error('Upload error:', uploadError);
      setError(
        uploadError instanceof Error ? uploadError.message : 'Failed to upload document'
      );
      setStatus('error');
      setPdfUrl(null);
      setCurrentFileName(undefined);
    }
  }, []);

  // Show loading screen while checking auth
  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <svg
            className="animate-spin h-10 w-10 text-oracle-red mx-auto mb-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-dark-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login if not authenticated
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="flex flex-col h-screen bg-dark-900">
      <Header
        status={currentView === 'document' ? status : 'idle'}
        onFileSelect={handleFileSelect}
        currentFileName={currentView === 'document' ? currentFileName : undefined}
        showUpload={currentView === 'document'}
        user={user}
        onNavigateProfile={() => navigate('/profile')}
        onLogout={handleLogout}
      />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  user={user}
                  projects={projects}
                  onProjectSelect={handleProjectSelect}
                  onNavigateProjects={() => navigate('/projects')}
                  showWelcome={showWelcome}
                  onWelcomeDismissed={() => setShowWelcome(false)}
                />
              }
            />

            <Route
              path="/projects"
              element={
                <HomePage
                  user={user}
                  projects={projects}
                  onProjectSelect={handleProjectSelect}
                  onProjectsChange={loadProjects}
                />
              }
            />

            <Route
              path="/projects/:projectId"
              element={
                selectedProject ? (
                  <ProjectView
                    user={user}
                    project={selectedProject}
                    onBack={handleNavigateProjects}
                    onViewDocument={handleViewDocument}
                    onStartChat={handleChatWithDocuments}
                    onProjectChange={handleProjectsChange}
                  />
                ) : (
                  <Navigate to="/projects" replace />
                )
              }
            />

            <Route
              path="/documents"
              element={
                <AllDocuments
                  user={user}
                  onViewDocument={handleViewDocument}
                  onChatWithDocuments={handleChatWithDocuments}
                />
              }
            />

            <Route
              path="/chat"
              element={
                <Chat
                  documents={chatDocuments}
                  webSources={chatWebSources}
                  projectName={chatProjectName}
                  onBack={handleBackToProject}
                  inferenceModel={selectedInferenceModel}
                />
              }
            />

            <Route
              path="/settings"
              element={
                <SystemSettings
                  onBack={handleNavigateHome}
                  selectedInferenceModel={selectedInferenceModel}
                  selectedEmbeddingModel={selectedEmbeddingModel}
                  onInferenceModelChange={handleInferenceModelChange}
                  onEmbeddingModelChange={handleEmbeddingModelChange}
                />
              }
            />

            <Route
              path="/profile"
              element={
                <UserProfilePage
                  user={user}
                  onBack={handleNavigateHome}
                  onLogout={handleLogout}
                  onUserUpdate={handleUserUpdate}
                />
              }
            />

            <Route path="/batch" element={<BatchProcessing />} />
            <Route path="/workflows" element={<WorkflowBuilder />} />
            <Route path="/research" element={<Research />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/benchmark" element={<Benchmarking />} />
            <Route path="/impact" element={<BusinessImpact />} />
            <Route path="/help" element={<HelpSupport />} />

            <Route
              path="/document"
              element={
                <div className="flex-1 flex overflow-hidden h-full">
                  <button
                    onClick={handleBackToProject}
                    className="absolute top-20 left-[17rem] z-10 p-2 bg-dark-800 hover:bg-dark-700 text-dark-400 hover:text-white rounded-md border border-dark-700 transition-colors"
                  >
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>

                  <div className="w-1/2 border-r border-dark-700 bg-dark-800">
                    <PdfViewer
                      pdfUrl={pdfUrl}
                      highlightedParam={highlightedParam}
                      allParameters={parameters}
                    />
                  </div>

                  <div className="w-1/2 bg-dark-900">
                    <ExtractionPanel
                      parameters={parameters}
                      isLoading={status === 'processing'}
                      error={error}
                      highlightedParam={highlightedParam}
                      onParameterClick={handleParameterClick}
                    />
                  </div>
                </div>
              }
            />

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;
