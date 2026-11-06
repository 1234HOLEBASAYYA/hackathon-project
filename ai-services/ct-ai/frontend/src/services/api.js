const API_BASE = 'http://localhost:8000';

export async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('Health check error:', err);
    return { status: 'offline', error: err.message };
  }
}

export async function analyzeImage(file, { generateGradcam = true, alpha = 0.45 } = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('generate_gradcam', generateGradcam);
  formData.append('alpha', alpha);

  const res = await fetch(`${API_BASE}/api/images/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Analysis failed with status ${res.status}`);
  }

  return await res.json();
}

export async function getSampleAnalysis(category = 'PNEUMONIA') {
  const res = await fetch(`${API_BASE}/api/images/sample?category=${category}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Sample request failed`);
  }
  return await res.json();
}

export async function getModelMetrics() {
  const res = await fetch(`${API_BASE}/api/images/metrics`);
  if (!res.ok) {
    throw new Error('Metrics not yet available');
  }
  return await res.json();
}

export async function analyzePrescription(text, patientId = 'guest_patient_001') {
  const res = await fetch(`${API_BASE}/api/prescriptions/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, patient_id: patientId }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Prescription analysis failed');
  }
  return await res.json();
}

export async function analyzePrescriptionFile(file, patientId = 'guest_patient_001') {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('prescription', file);
  formData.append('patient_id', patientId);

  const res = await fetch(`${API_BASE}/api/prescriptions/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `Prescription analysis failed with status ${res.status}`);
  }
  return await res.json();
}

export async function getSamplePrescription() {
  const res = await fetch(`${API_BASE}/api/prescriptions/sample`);
  if (!res.ok) throw new Error('Failed to load sample prescription');
  return await res.json();
}

/**
 * MedVision-AI CT Scan Image Analyzer APIs
 */
export async function analyzeCTScan(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `CT Analysis failed with status ${res.status}`);
  }

  const result = await res.json();
  return result.data;
}

export async function generatePDFReport(reportData, serverImageId = null) {
  const res = await fetch(`${API_BASE}/api/generate-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report: reportData,
      server_image_id: serverImageId
    })
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || 'Failed to generate PDF report');
  }

  return await res.json();
}

export function getReportDownloadUrl(filename) {
  return `${API_BASE}/api/reports/download/${filename}`;
}

export async function getSampleCTScan() {
  const res = await fetch(`${API_BASE}/api/sample`);
  if (!res.ok) throw new Error('Failed to load sample scan');
  return await res.blob();
}
