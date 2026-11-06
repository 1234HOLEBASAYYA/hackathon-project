/**
 * API Service for AI Prescription Reader REST backend.
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export const apiService = {
  getBaseUrl() {
    return API_BASE_URL;
  },

  getImageUrl(id) {
    return `${API_BASE_URL}/api/prescription/image/${id}`;
  },

  getExportUrl(id, format = 'pdf') {
    return `${API_BASE_URL}/api/prescription/export/${id}?format=${format}`;
  },

  async checkHealth() {
    const response = await client.get('/health');
    return response.data;
  },

  async uploadPrescription(file) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/api/prescription/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async analyzePrescription(id, options = {}) {
    const payload = {
      id,
      use_gpu: options.use_gpu !== undefined ? options.use_gpu : true,
      apply_clahe: options.apply_clahe !== undefined ? options.apply_clahe : true,
      apply_deskew: options.apply_deskew !== undefined ? options.apply_deskew : true,
    };
    const response = await client.post('/api/prescription/analyze', payload);
    return response.data;
  },

  async getResult(id) {
    const response = await client.get(`/api/prescription/result/${id}`);
    return response.data;
  },

  async updateResult(id, updatedFields) {
    const response = await client.put(`/api/prescription/result/${id}`, updatedFields);
    return response.data;
  },

  async downloadExport(id, format = 'pdf', filename = 'prescription_export') {
    const response = await client.get(`/api/prescription/export/${id}`, {
      params: { format },
      responseType: 'blob',
    });
    
    // Trigger browser download
    const blob = new Blob([response.data], {
      type: format === 'pdf' ? 'application/pdf' : 'text/csv;charset=utf-8;',
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${filename}.${format}`);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
  },
};
