const fs = require('fs');
const axios = require('axios');
const FormData = require('form-data');
const { SERVICES } = require('../config/ports');

async function analyzeXRay(filePath, originalFilename, patientId) {
  const url = `${SERVICES.XRAY.URL}/api/analyze`;
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), originalFilename);

  const response = await axios.post(url, form, {
    headers: { ...form.getHeaders() },
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    timeout: 120000
  });

  const data = response.data;
  data.patient_id = patientId;
  return data;
}

async function checkHealth() {
  try {
    const res = await axios.get(`${SERVICES.XRAY.URL}/api/health`, { timeout: 3000 });
    return { status: 'healthy', data: res.data };
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

module.exports = {
  analyzeXRay,
  checkHealth
};
