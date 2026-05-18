"use client";

import { createContext, useContext, useEffect, useState } from "react";

const ProjectContext = createContext(null);

export const useProject = () => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProject must be used within a ProjectProvider");
  }
  return context;
};

export const ProjectProvider = ({ children }) => {
  const [projects, setProjects] = useState([]);
  const [currentProjectId, setCurrentProjectId] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedProjects = localStorage.getItem("chatProjects");
      const storedCurrentProjectId = localStorage.getItem("currentProjectId");

      if (!storedProjects) {
        const defaultProject = {
          id: "default",
          name: "Oracle Digital Assistant",
          logoUrl: "",
          mainColor: "#007AFF",
          backgroundColor: "#F5F5F5",
          backgroundImage: "/background.png",
          speechProvider: "browser",
        };

        setProjects([defaultProject]);
        setCurrentProjectId("default");

        localStorage.setItem("chatProjects", JSON.stringify([defaultProject]));
        localStorage.setItem("currentProjectId", "default");
      } else {
        const parsedProjects = JSON.parse(storedProjects);
        const migratedProjects = parsedProjects.map((project) => ({
          ...project,
          mainColor: project.mainColor || project.backgroundColor || "#007AFF",
          backgroundColor: project.backgroundColor || "#F5F5F5",
          speechProvider: project.speechProvider || "browser",
        }));

        setProjects(migratedProjects);
        setCurrentProjectId(storedCurrentProjectId || "default");
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined" && projects.length > 0) {
      localStorage.setItem("chatProjects", JSON.stringify(projects));
    }
  }, [projects]);

  useEffect(() => {
    if (typeof window !== "undefined" && currentProjectId) {
      localStorage.setItem("currentProjectId", currentProjectId);
    }
  }, [currentProjectId]);

  const createProject = (projectData) => {
    if (projects.length >= 8) {
      console.warn("Maximum number of projects (8) reached");
      return null;
    }

    const newProject = {
      id: Date.now().toString(),
      mainColor: "#007AFF",
      backgroundColor: "#F5F5F5",
      speechProvider: "browser",
      ...projectData,
    };

    setProjects((prev) => [...prev, newProject]);
    return newProject.id;
  };

  const updateProject = (id, projectData) => {
    setProjects((prev) =>
      prev.map((project) =>
        project.id === id ? { ...project, ...projectData } : project
      )
    );
  };

  const deleteProject = (id) => {
    if (id === "default") return false;

    setProjects((prev) => prev.filter((project) => project.id !== id));

    if (currentProjectId === id) {
      setCurrentProjectId("default");
    }

    return true;
  };

  const getCurrentProject = () => {
    return (
      projects.find((p) => p.id === currentProjectId) ||
      projects[0] || {
        id: "default",
        name: "Oracle Digital Assistant",
        logoUrl: "",
        mainColor: "#007AFF",
        backgroundColor: "#F5F5F5",
        speechProvider: "browser",
      }
    );
  };

  const switchProject = (id) => {
    if (currentProjectId !== id) {
      setCurrentProjectId(id);
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        createProject,
        updateProject,
        deleteProject,
        getCurrentProject,
        switchProject,
        currentProjectId,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
};
