import { Project, WebSource } from '../types';

const PROJECTS_KEY = 'aiq_projects';

const generateId = (): string => {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
};

const loadProjects = (): Project[] => {
  const data = localStorage.getItem(PROJECTS_KEY);
  if (!data) return [];
  const projects: Project[] = JSON.parse(data);
  // Ensure backwards compatibility: add tags if missing
  return projects.map((p) => ({ ...p, tags: p.tags || [] }));
};

const saveProjects = (projects: Project[]): void => {
  localStorage.setItem(PROJECTS_KEY, JSON.stringify(projects));
};

export const projectService = {
  listProjects: (): Project[] => {
    return loadProjects().sort(
      (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
  },

  getProject: (id: string): Project | null => {
    return loadProjects().find((p) => p.id === id) || null;
  },

  createProject: (name: string, description: string, tags: string[] = []): Project => {
    const projects = loadProjects();
    const now = new Date().toISOString();
    const project: Project = {
      id: generateId(),
      name,
      description,
      tags,
      document_ids: [],
      web_sources: [],
      created_at: now,
      updated_at: now,
    };
    projects.push(project);
    saveProjects(projects);
    return project;
  },

  updateProject: (id: string, updates: Partial<Pick<Project, 'name' | 'description' | 'tags'>>): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === id);
    if (index === -1) return null;
    projects[index] = {
      ...projects[index],
      ...updates,
      updated_at: new Date().toISOString(),
    };
    saveProjects(projects);
    return projects[index];
  },

  deleteProject: (id: string): boolean => {
    const projects = loadProjects();
    const filtered = projects.filter((p) => p.id !== id);
    if (filtered.length === projects.length) return false;
    saveProjects(filtered);
    return true;
  },

  addDocumentToProject: (projectId: string, documentId: string): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) return null;
    if (!projects[index].document_ids.includes(documentId)) {
      projects[index].document_ids.push(documentId);
      projects[index].updated_at = new Date().toISOString();
      saveProjects(projects);
    }
    return projects[index];
  },

  removeDocumentFromProject: (projectId: string, documentId: string): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) return null;
    projects[index].document_ids = projects[index].document_ids.filter((id) => id !== documentId);
    projects[index].updated_at = new Date().toISOString();
    saveProjects(projects);
    return projects[index];
  },

  addWebSource: (projectId: string, url: string, title: string): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) return null;
    const webSource: WebSource = {
      id: generateId(),
      url,
      title: title || url,
      added_at: new Date().toISOString(),
    };
    projects[index].web_sources.push(webSource);
    projects[index].updated_at = new Date().toISOString();
    saveProjects(projects);
    return projects[index];
  },

  addWebSourceWithId: (projectId: string, id: string, url: string, title: string, status?: string): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) return null;
    const webSource: WebSource = {
      id,
      url,
      title: title || url,
      status: (status as WebSource['status']) || 'completed',
      added_at: new Date().toISOString(),
    };
    projects[index].web_sources.push(webSource);
    projects[index].updated_at = new Date().toISOString();
    saveProjects(projects);
    return projects[index];
  },

  removeWebSource: (projectId: string, webSourceId: string): Project | null => {
    const projects = loadProjects();
    const index = projects.findIndex((p) => p.id === projectId);
    if (index === -1) return null;
    projects[index].web_sources = projects[index].web_sources.filter((ws) => ws.id !== webSourceId);
    projects[index].updated_at = new Date().toISOString();
    saveProjects(projects);
    return projects[index];
  },
};

export default projectService;
