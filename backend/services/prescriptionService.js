const fs = require('fs');
const axios = require('axios');
const FormData = require('form-data');
const { SERVICES } = require('../config/ports');

async function analyzePrescription(filePath, originalFilename, patientId) {
  // Step 1: Upload prescription to Prescription AI Service (Port 8001)
  const uploadUrl = `${SERVICES.PRESCRIPTION.URL}/api/prescription/upload`;
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath), originalFilename);

  const uploadRes = await axios.post(uploadUrl, form, {
    headers: { ...form.getHeaders() },
    maxContentLength: Infinity,
    maxBodyLength: Infinity,
    timeout: 30000
  });

  const prescriptionId = uploadRes.data.id;

  // Step 2: Trigger structured clinical analysis
  const analyzeUrl = `${SERVICES.PRESCRIPTION.URL}/api/prescription/analyze`;
  const analyzeRes = await axios.post(analyzeUrl, {
    id: prescriptionId,
    apply_clahe: true,
    apply_deskew: false,
    use_gpu: false
  }, {
    timeout: 120000
  });

  const data = analyzeRes.data;
  data.prescription_id = prescriptionId;
  data.patient_id = patientId;
  return data;
}

async function checkHealth() {
  try {
    const res = await axios.get(`${SERVICES.PRESCRIPTION.URL}/health`, { timeout: 3000 });
    return { status: 'healthy', data: res.data };
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

module.exports = {
  analyzePrescription,
  checkHealth
};
