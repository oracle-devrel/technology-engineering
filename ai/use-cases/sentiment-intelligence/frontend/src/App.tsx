import { useState, useCallback } from 'react';
import HomePage from './pages/HomePage';
import Dashboard from './pages/Dashboard';
import AgentsPage from './pages/AgentsPage';
import type { WorkflowStep } from './components/WorkflowProgress';

type Page = 'home' | 'dashboard' | 'agents';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [sharedWorkflowSteps, setSharedWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [sharedIsAnalyzing, setSharedIsAnalyzing] = useState(false);

  const handleWorkflowUpdate = useCallback((steps: WorkflowStep[], analyzing: boolean) => {
    setSharedWorkflowSteps(steps);
    setSharedIsAnalyzing(analyzing);
  }, []);

  return (
    <>
      {currentPage === 'home' && (
        <HomePage onNavigate={setCurrentPage} />
      )}
      {currentPage === 'dashboard' && (
        <Dashboard
          onNavigate={setCurrentPage}
          onWorkflowUpdate={handleWorkflowUpdate}
        />
      )}
      {currentPage === 'agents' && (
        <AgentsPage
          onNavigate={setCurrentPage}
          workflowSteps={sharedWorkflowSteps}
          isAnalyzing={sharedIsAnalyzing}
        />
      )}
    </>
  );
}

export default App;
