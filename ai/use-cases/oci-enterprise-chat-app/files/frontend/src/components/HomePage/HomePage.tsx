import React, { useState } from 'react';
import { Project, User } from '../../types';
import { projectService } from '../../services/projectService';

interface HomePageProps {
  user: User;
  projects: Project[];
  onProjectSelect: (project: Project) => void;
  onProjectsChange: () => void;
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

const HomePage: React.FC<HomePageProps> = ({
  user,
  projects,
  onProjectSelect,
  onProjectsChange,
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectTags, setNewProjectTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleAddTag = () => {
    const tag = tagInput.trim();
    if (tag && !newProjectTags.includes(tag)) {
      setNewProjectTags([...newProjectTags, tag]);
    }
    setTagInput('');
  };

  const handleRemoveTag = (tag: string) => {
    setNewProjectTags(newProjectTags.filter((t) => t !== tag));
  };

  const handleCreateProject = () => {
    if (!newProjectName.trim()) return;
    projectService.createProject(newProjectName.trim(), newProjectDesc.trim(), newProjectTags);
    setNewProjectName('');
    setNewProjectDesc('');
    setNewProjectTags([]);
    setTagInput('');
    setShowCreateModal(false);
    onProjectsChange();
  };

  const handleDeleteProject = (id: string) => {
    projectService.deleteProject(id);
    setDeleteConfirmId(null);
    onProjectsChange();
  };

  return (
    <div className="flex-1 overflow-auto bg-dark-900 p-6">
      {/* Welcome section */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white mb-2">
          Welcome back, {user.full_name}
        </h1>
        <p className="text-dark-300">
          Create and manage your AI-powered document analysis projects
        </p>
      </div>

      {/* Actions bar */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 bg-oracle-red hover:bg-oracle-red-dark text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Project
        </button>
        <p className="text-sm text-dark-400">
          {projects.length} project{projects.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Projects grid */}
      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 bg-dark-800 rounded-xl border border-dark-700">
          <div className="w-16 h-16 rounded-2xl bg-dark-700 flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-dark-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No projects yet</h3>
          <p className="text-dark-400 text-sm mb-4">
            Create your first project to start uploading documents and web sources
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-oracle-red hover:bg-oracle-red-dark text-white font-medium rounded-lg transition-colors"
          >
            Create Project
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Create new project card */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-dark-800 rounded-xl border-2 border-dashed border-dark-600 hover:border-oracle-red/50 p-6 flex flex-col items-center justify-center gap-3 transition-all group min-h-[200px]"
          >
            <div className="w-12 h-12 rounded-xl bg-dark-700 group-hover:bg-oracle-red/20 flex items-center justify-center transition-colors">
              <svg className="w-6 h-6 text-dark-400 group-hover:text-oracle-red transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <span className="text-dark-400 group-hover:text-dark-200 font-medium transition-colors">
              New Project
            </span>
          </button>

          {/* Project cards */}
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-dark-800 rounded-xl border border-dark-700 hover:border-dark-500 p-6 flex flex-col transition-all cursor-pointer group relative"
              onClick={() => onProjectSelect(project)}
            >
              {/* Delete button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteConfirmId(project.id);
                }}
                className="absolute top-4 right-4 p-1.5 text-dark-500 hover:text-red-400 hover:bg-dark-700 rounded-md opacity-0 group-hover:opacity-100 transition-all"
                title="Delete project"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>

              {/* Project icon */}
              <div className="w-10 h-10 rounded-lg bg-oracle-red/15 flex items-center justify-center mb-4">
                <svg className="w-5 h-5 text-oracle-red" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>

              {/* Project name & description */}
              <h3 className="text-white font-semibold text-lg mb-1 truncate pr-8">
                {project.name}
              </h3>
              {project.description && (
                <p className="text-dark-400 text-sm mb-2 truncate-2">
                  {project.description}
                </p>
              )}

              {/* Tags */}
              {project.tags && project.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {project.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-0.5 bg-oracle-red/10 text-oracle-red text-xs font-medium rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Stats */}
              <div className="mt-auto pt-4 border-t border-dark-700 flex items-center gap-4">
                <div className="flex items-center gap-1.5 text-sm text-dark-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>{project.document_ids.length} file{project.document_ids.length !== 1 ? 's' : ''}</span>
                </div>
                <div className="flex items-center gap-1.5 text-sm text-dark-400">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <span>{project.web_sources.length} URL{project.web_sources.length !== 1 ? 's' : ''}</span>
                </div>
                <span className="text-xs text-dark-500 ml-auto">
                  {formatDate(project.updated_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="modal-backdrop flex items-center justify-center" onClick={() => setShowCreateModal(false)}>
          <div
            className="bg-dark-800 rounded-xl border border-dark-600 p-6 w-full max-w-md shadow-modal animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold text-white mb-4">Create New Project</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-dark-200 mb-1.5">
                  Project Name
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  placeholder="Enter project name..."
                  className="input-field w-full"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreateProject();
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-200 mb-1.5">
                  Description <span className="text-dark-500">(optional)</span>
                </label>
                <textarea
                  value={newProjectDesc}
                  onChange={(e) => setNewProjectDesc(e.target.value)}
                  placeholder="Brief project description..."
                  rows={3}
                  className="input-field w-full resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-dark-200 mb-1.5">
                  Tags <span className="text-dark-500">(optional)</span>
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    placeholder="Add a tag..."
                    className="input-field flex-1"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    disabled={!tagInput.trim()}
                    className="px-3 py-2 bg-dark-600 hover:bg-dark-500 text-dark-200 text-sm rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Add
                  </button>
                </div>
                {newProjectTags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {newProjectTags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2.5 py-1 bg-oracle-red/15 text-oracle-red text-xs font-medium rounded-full"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="hover:text-white transition-colors"
                        >
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateProject}
                disabled={!newProjectName.trim()}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Create Project
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="modal-backdrop flex items-center justify-center" onClick={() => setDeleteConfirmId(null)}>
          <div
            className="bg-dark-800 rounded-xl border border-dark-600 p-6 w-full max-w-sm shadow-modal animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-lg font-bold text-white mb-2">Delete Project?</h2>
            <p className="text-dark-400 text-sm mb-6">
              This will remove the project and its source associations. Uploaded documents will not be deleted.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteConfirmId(null)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={() => handleDeleteProject(deleteConfirmId)}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-medium rounded-lg transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
