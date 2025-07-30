"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import Chat from "./components/Chat/Chat";
import ProjectModal from "./components/Settings/ProjectModal";
import { ChatProvider } from "./contexts/ChatContext";
import { useProject } from "./contexts/ProjectsContext";

function HomeContent() {
  const searchParams = useSearchParams();
  const projectId = searchParams.get("projectId");
  const router = useRouter();
  const { switchProject, createProject, updateProject, deleteProject } =
    useProject();

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);

  useEffect(() => {
    if (projectId) {
      switchProject(projectId);
    }
  }, [projectId, switchProject]);

  const handleAddProject = () => {
    setSelectedProject(null);
    setModalOpen(true);
  };

  const handleEditProject = (project) => {
    setSelectedProject(project);
    setModalOpen(true);
  };

  const handleSaveProject = (formData) => {
    if (selectedProject) {
      updateProject(selectedProject.id, formData);
      setModalOpen(false);
      setSelectedProject(null);
    } else {
      const newProjectId = createProject(formData);
      if (newProjectId) {
        switchProject(newProjectId);
        router.push(`/?projectId=${newProjectId}`);
        setModalOpen(false);
        setSelectedProject(null);
      } else {
        alert("Maximum number of projects (8) reached");
      }
    }
  };

  const handleDeleteProject = (projectId) => {
    deleteProject(projectId);
    setModalOpen(false);
    setSelectedProject(null);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedProject(null);
  };

  return (
    <>
      <ChatProvider>
        <Chat
          onAddProject={handleAddProject}
          onEditProject={handleEditProject}
          onDeleteProject={handleDeleteProject}
        />
      </ChatProvider>

      <ProjectModal
        open={modalOpen}
        onClose={handleCloseModal}
        project={selectedProject}
        onSave={handleSaveProject}
        onDelete={handleDeleteProject}
      />
    </>
  );
}

export default function Home() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HomeContent />
    </Suspense>
  );
}
