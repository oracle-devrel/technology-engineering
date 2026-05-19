"use client";

import apiClient from './apiClient';

class FlowService {
  /**
   * Listar flujos con filtros y paginación
   */
  async listFlows(params = {}) {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        queryParams.append(key, value);
      }
    });

    return await apiClient.request(`/flows?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Crear un nuevo flujo
   */
  async createFlow(flowData) {
    return await apiClient.request('/flows/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(flowData),
    });
  }

  /**
   * Obtener un flujo por ID
   */
  async getFlow(flowId) {
    return await apiClient.request(`/flows/${flowId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Actualizar un flujo
   */
  async updateFlow(flowId, updateData) {
    return await apiClient.request(`/flows/${flowId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData),
    });
  }

  /**
   * Eliminar un flujo
   */
  async deleteFlow(flowId) {
    return await apiClient.request(`/flows/${flowId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }
}

// Crear instancia singleton
const flowService = new FlowService();

export default flowService;