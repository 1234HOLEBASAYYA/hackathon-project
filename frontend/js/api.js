/**
 * MEDVISION-AI Unified API Client
 * Centralized fetch wrappers communicating with the Express Backend (Port 3000)
 */

const API_BASE = window.location.origin;

const API = {
  // Patients
  async getPatients() {
    const res = await fetch(`${API_BASE}/api/patients`);
    return res.json();
  },

  async createPatient(patientData) {
    const res = await fetch(`${API_BASE}/api/patients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patientData)
    });
    return res.json();
  },

  async getPatientTimeline(patientId) {
    const res = await fetch(`${API_BASE}/api/patients/${encodeURIComponent(patientId)}/timeline`);
    return res.json();
  },

  // Prescription Analysis
  async analyzePrescription(formData, signal = null) {
    const res = await fetch(`${API_BASE}/api/analysis/prescription/analyze`, {
      method: 'POST',
      body: formData,
      signal
    });
    return res.json();
  },

  // X-Ray Analysis
  async analyzeXRay(formData, signal = null) {
    const res = await fetch(`${API_BASE}/api/analysis/xray/analyze`, {
      method: 'POST',
      body: formData,
      signal
    });
    return res.json();
  },

  // CT-Scan Analysis
  async analyzeCTScan(formData, signal = null) {
    const res = await fetch(`${API_BASE}/api/analysis/ct/analyze`, {
      method: 'POST',
      body: formData,
      signal
    });
    return res.json();
  },

  // Reports
  async getRecentReports(limit = 20) {
    const res = await fetch(`${API_BASE}/api/reports?limit=${limit}`);
    return res.json();
  },

  async getStats() {
    const res = await fetch(`${API_BASE}/api/reports/stats`);
    return res.json();
  },

  async getReportById(analysisId) {
    const res = await fetch(`${API_BASE}/api/reports/${encodeURIComponent(analysisId)}`);
    return res.json();
  },

  // Prescription Management
  async updatePrescription(prescriptionId, data) {
    const res = await fetch(`${API_BASE}/api/analysis/prescription/${encodeURIComponent(prescriptionId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getPrescriptionHistory(patientId) {
    const res = await fetch(`${API_BASE}/api/analysis/prescription/history/${encodeURIComponent(patientId)}`);
    return res.json();
  },

  // Patient Search
  async searchPatients(query) {
    const res = await fetch(`${API_BASE}/api/patients?search=${encodeURIComponent(query)}`);
    return res.json();
  },

  // System Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
  }
};

window.API = API;

