const fs = require('fs');
const axios = require('axios');
const FormData = require('form-data');
const { SERVICES } = require('../config/ports');

async function analyzeCTScan(filePath, originalFilename, patientId) {
  const url = `${SERVICES.CT.URL}/api/analyze`;
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), originalFilename);
  form.append('patient_id', patientId || 'guest_patient');

  const response = await axios.post(url, form, {
    headers: {
      ...form.getHeaders()
    },
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    timeout: 120000 // 2 minutes for Gemini clinical analysis
  });

  return response.data.data || response.data;
}

async function checkHealth() {
  try {
    const res = await axios.get(`${SERVICES.CT.URL}/api/health`, { timeout: 3000 });
    return { status: 'healthy', data: res.data };
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

module.exports = {
  analyzeCTScan,
  checkHealth
};

