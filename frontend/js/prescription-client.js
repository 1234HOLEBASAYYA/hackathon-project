/**
 * MEDVISION-AI Prescription OCR Client
 * Controls upload, EasyOCR execution, interactive clinical editing, MongoDB persistence, and report generation
 */

const PrescriptionClient = {
  currentResult: null,

  init() {
    const dropZone = document.getElementById('rxDropZone');
    const fileInput = document.getElementById('rxFileInput');

    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        this.processFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        this.processFile(fileInput.files[0]);
      }
    });
  },

  async processFile(file) {
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'application/pdf'];
    if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf')) {
      window.App.showToast('Please upload a valid image (PNG, JPG) or PDF file.', 'error');
      return;
    }

    if (file.size > 16 * 1024 * 1024) {
      window.App.showToast('File size exceeds the 16MB limit.', 'error');
      return;
    }

    const previewContainer = document.getElementById('rxPreviewContainer');
    const previewImg = document.getElementById('rxPreviewImg');
    const resultsContainer = document.getElementById('rxResultsContainer');
    const emptyState = document.getElementById('rxEmptyState');
    const loadingState = document.getElementById('rxLoading');

    // Show image preview if not PDF
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (previewImg) previewImg.src = e.target.result;
        if (previewContainer) {
          previewContainer.style.display = 'flex';
          previewContainer.classList.add('scanning');
        }
      };
      reader.readAsDataURL(file);
    } else {
      if (previewContainer) previewContainer.style.display = 'none';
    }

    if (loadingState) loadingState.style.display = 'block';
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';

    try {
      const activePatient = window.PatientManager.getActivePatient();
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patientId', activePatient.patientId);
      formData.append('patientName', activePatient.name);

      window.App.showToast('Executing EasyOCR deep-learning pipeline...', 'info');

      const response = await window.API.analyzePrescription(formData);

      if (response.status !== 'success') {
        throw new Error(response.message || 'Prescription analysis failed');
      }

      this.currentResult = response.data;
      this.renderResults(response.data);
      window.App.showToast('Prescription digitized and saved to MongoDB!', 'success');

    } catch (err) {
      console.error(err);
      window.App.showToast(`Error: ${err.message}`, 'error');
      if (emptyState) emptyState.style.display = 'block';
    } finally {
      if (loadingState) loadingState.style.display = 'none';
      if (previewContainer) previewContainer.classList.remove('scanning');
    }
  },

  renderResults(data) {
    const container = document.getElementById('rxResultsContainer');
    const emptyState = document.getElementById('rxEmptyState');
    if (!container) return;

    // Doctor Details
    const doc = data.doctor || {};
    const docNameInput = document.getElementById('rxDocNameInput');
    const docSpecInput = document.getElementById('rxDocSpecInput');
    const clinicInput = document.getElementById('rxClinicInput');
    const patNameInput = document.getElementById('rxPatientNameInput');
    const patAgeInput = document.getElementById('rxPatientAgeInput');

    if (docNameInput) docNameInput.value = doc.name || '';
    if (docSpecInput) docSpecInput.value = `${doc.specialization || ''} ${doc.qualification ? '(' + doc.qualification + ')' : ''}`.trim();
    if (clinicInput) clinicInput.value = data.clinicHeader || doc.clinicOrHospital || '';
    if (patNameInput) patNameInput.value = (data.patient && data.patient.name) ? data.patient.name : (data.patientName || '');
    if (patAgeInput) patAgeInput.value = (data.patient && data.patient.age) ? data.patient.age : (data.patientAge || '');

    // Clinical Assessment
    const diagInput = document.getElementById('rxDiagnosisInput');
    const adviceInput = document.getElementById('rxAdviceInput');
    const followInput = document.getElementById('rxFollowUpInput');

    if (diagInput) diagInput.value = data.diagnosis || '';
    if (adviceInput) adviceInput.value = data.advice || '';
    if (followInput) followInput.value = data.followUp || '';

    // Status Badge
    const statusBadge = document.getElementById('rxStatusBadge');
    if (statusBadge) {
      if (data.status === 'verified') {
        statusBadge.textContent = 'Verified';
        statusBadge.className = 'badge badge-green';
      } else {
        statusBadge.textContent = 'Extracted (Pending Verification)';
        statusBadge.className = 'badge badge-teal';
      }
    }

    // Medications Table
    const tbody = document.getElementById('rxMedsTableBody');
    tbody.innerHTML = '';

    const meds = data.medications || [];
    if (meds.length === 0) {
      this.addMedicationRow(); // Provide one empty row for manual entry
    } else {
      meds.forEach((m, idx) => {
        this.addMedicationRow(m, idx);
      });
    }

    // Raw OCR text stream
    const rawOcrEl = document.getElementById('rxRawOcr');
    if (rawOcrEl) rawOcrEl.textContent = data.rawText || '(No raw OCR text stream)';

    if (emptyState) emptyState.style.display = 'none';
    container.style.display = 'block';
  },

  addMedicationRow(med = {}, idx = null) {
    const tbody = document.getElementById('rxMedsTableBody');
    if (!tbody) return;

    const rowIdx = idx !== null ? idx + 1 : tbody.children.length + 1;
    const confVal = typeof med.confidence === 'number' ? med.confidence : 85;
    const isHighConf = confVal >= 75;

    const tr = document.createElement('tr');
    tr.className = 'rx-med-row';
    tr.innerHTML = `
      <td style="color: var(--text-muted); font-weight: 700;">${rowIdx}</td>
      <td>
        <input type="text" class="table-input rx-med-name" value="${med.medicineName || med.name || ''}" placeholder="e.g. Amoxicillin">
      </td>
      <td>
        <input type="text" class="table-input rx-med-strength" value="${med.strength || ''}" placeholder="500mg">
      </td>
      <td>
        <input type="text" class="table-input rx-med-dosage" value="${med.dosage || ''}" placeholder="1 tab">
      </td>
      <td>
        <input type="text" class="table-input rx-med-frequency" value="${med.frequency || ''}" placeholder="TDS (3x daily)">
      </td>
      <td>
        <input type="text" class="table-input rx-med-duration" value="${med.duration || ''}" placeholder="5 days">
      </td>
      <td>
        <input type="text" class="table-input rx-med-instructions" value="${med.specialInstructions || med.foodInstructions || ''}" placeholder="After food">
      </td>
      <td>
        ${isHighConf 
          ? `<span class="badge badge-green" title="Confidence: ${confVal.toFixed(0)}%">✅ High (${confVal.toFixed(0)}%)</span>`
          : `<span class="badge badge-amber" title="Confidence: ${confVal.toFixed(0)}%">⚠️ Verify (${confVal.toFixed(0)}%)</span>`}
      </td>
      <td style="text-align: center;">
        <button type="button" class="btn-switch-patient" onclick="this.closest('tr').remove()" title="Delete row" style="color: var(--rose-primary);">✕</button>
      </td>
    `;
    tbody.appendChild(tr);
  },

  async saveVerifiedPrescription() {
    if (!this.currentResult || !this.currentResult.prescriptionId) {
      window.App.showToast('No active prescription loaded to verify.', 'error');
      return;
    }

    const prescriptionId = this.currentResult.prescriptionId;

    // Collect edited medications from table
    const rows = document.querySelectorAll('#rxMedsTableBody tr.rx-med-row');
    const medications = [];

    rows.forEach(r => {
      const name = r.querySelector('.rx-med-name')?.value.trim();
      if (name) {
        medications.push({
          medicineName: name,
          name: name,
          strength: r.querySelector('.rx-med-strength')?.value.trim() || 'Not specified',
          dosage: r.querySelector('.rx-med-dosage')?.value.trim() || 'Not specified',
          frequency: r.querySelector('.rx-med-frequency')?.value.trim() || 'Not specified',
          duration: r.querySelector('.rx-med-duration')?.value.trim() || 'Not specified',
          specialInstructions: r.querySelector('.rx-med-instructions')?.value.trim() || 'None',
          foodInstructions: r.querySelector('.rx-med-instructions')?.value.trim() || 'None',
          confidence: 100.0 // User-verified
        });
      }
    });

    const updatePayload = {
      doctor: {
        name: document.getElementById('rxDocNameInput')?.value.trim() || 'Clinician',
        specialization: document.getElementById('rxDocSpecInput')?.value.trim() || '',
        clinicOrHospital: document.getElementById('rxClinicInput')?.value.trim() || ''
      },
      patientName: document.getElementById('rxPatientNameInput')?.value.trim() || '',
      patientAge: parseInt(document.getElementById('rxPatientAgeInput')?.value, 10) || undefined,
      diagnosis: document.getElementById('rxDiagnosisInput')?.value.trim() || '',
      advice: document.getElementById('rxAdviceInput')?.value.trim() || '',
      followUp: document.getElementById('rxFollowUpInput')?.value.trim() || '',
      medications
    };

    try {
      window.App.showToast('Saving verified prescription to MongoDB...', 'info');
      const res = await window.API.updatePrescription(prescriptionId, updatePayload);

      if (res.status === 'success') {
        window.App.showToast('Prescription verified and saved successfully!', 'success');
        const statusBadge = document.getElementById('rxStatusBadge');
        if (statusBadge) {
          statusBadge.textContent = 'Verified & Locked';
          statusBadge.className = 'badge badge-green';
        }
        this.currentResult = { ...this.currentResult, ...res.data };
      } else {
        throw new Error(res.message || 'Failed to update');
      }
    } catch (e) {
      window.App.showToast(`Error saving prescription: ${e.message}`, 'error');
    }
  },

  async openHistoryModal() {
    const modal = document.getElementById('rxHistoryModal');
    const container = document.getElementById('rxHistoryContainer');
    if (!modal || !container) return;

    modal.style.display = 'flex';
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Fetching patient prescriptions...</div>`;

    const activePatient = window.PatientManager.getActivePatient();
    try {
      const res = await window.API.getPrescriptionHistory(activePatient.patientId);
      if (res.status !== 'success') throw new Error(res.message);

      const list = res.data || [];
      if (list.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
            No previous prescriptions recorded for ${activePatient.name} (${activePatient.patientId}).
          </div>
        `;
        return;
      }

      container.innerHTML = '';
      list.forEach(p => {
        const item = document.createElement('div');
        item.style.cssText = 'background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; gap: 1rem;';
        
        const dateStr = new Date(p.createdAt).toLocaleDateString() + ' ' + new Date(p.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const medsSummary = (p.medications || []).map(m => m.medicineName || m.name).slice(0, 3).join(', ');

        item.innerHTML = `
          <div>
            <div style="font-weight: 700; color: #fff;">${p.doctor?.name ? 'Dr. ' + p.doctor.name : 'Prescription Review'}</div>
            <div style="font-size: 0.8125rem; color: var(--teal-primary);">${p.diagnosis || 'Clinical Assessment'}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">
              Medications: ${medsSummary || 'None extracted'} &bull; ${dateStr}
            </div>
          </div>
          <button class="btn btn-outline btn-sm" onclick='PrescriptionClient.loadHistoryPrescription(${JSON.stringify(p)})'>
            Load Record
          </button>
        `;
        container.appendChild(item);
      });

    } catch (e) {
      container.innerHTML = `<div style="color: var(--rose-primary); padding: 1rem;">Failed to load history: ${e.message}</div>`;
    }
  },

  loadHistoryPrescription(p) {
    this.currentResult = p;
    this.renderResults(p);
    this.closeHistoryModal();
    window.App.showToast(`Loaded prescription from ${new Date(p.createdAt).toLocaleDateString()}`, 'info');
  },

  closeHistoryModal() {
    const modal = document.getElementById('rxHistoryModal');
    if (modal) modal.style.display = 'none';
  },

  buildReportHtml() {
    if (!this.currentResult) return '';
    const doc = this.currentResult.doctor || {};
    const meds = this.currentResult.medications || [];
    const patName = this.currentResult.patientName || (this.currentResult.patient && this.currentResult.patient.name) || 'Patient';
    const patId = this.currentResult.patientId || 'P-1001';
    const dateStr = new Date(this.currentResult.createdAt || Date.now()).toLocaleDateString();

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Prescription Report - ${patName} (${patId})</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; padding: 30px; background: #fff; margin: 0; }
    .rx-card { max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .header { border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
    .doc-name { font-size: 20px; font-weight: bold; color: #0284c7; }
    .clinic { font-size: 13px; color: #64748b; margin-top: 3px; }
    .patient-box { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 20px; }
    th, td { border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; font-size: 12px; }
    th { background: #f1f5f9; color: #334155; font-weight: 600; }
    .rx-symbol { font-size: 28px; font-weight: bold; color: #0284c7; margin: 8px 0; }
    .footer { margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 12px; font-size: 11px; color: #64748b; text-align: center; }
    .no-print { margin-bottom: 15px; text-align: right; }
    @media print {
      body { padding: 0; }
      .rx-card { border: none; box-shadow: none; padding: 0; }
      .no-print { display: none !important; }
    }
  </style>
</head>
<body>
  <div class="rx-card">
    <div class="no-print">
      <button onclick="window.print()" style="padding: 6px 14px; background: #0284c7; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600;">Print / Save as PDF</button>
    </div>
    <div class="header">
      <div>
        <div class="doc-name">${doc.name ? 'Dr. ' + doc.name : 'Authorized Medical Practitioner'}</div>
        <div style="font-size: 13px; color: #475569;">${doc.specialization || 'Clinical Specialist'} ${doc.qualification ? '(' + doc.qualification + ')' : ''}</div>
        <div class="clinic">${this.currentResult.clinicHeader || doc.clinicOrHospital || 'Apollo Health Clinical Network'}</div>
      </div>
      <div style="text-align: right; font-size: 11px; color: #64748b;">
        <div>MEDVISION-AI Verified</div>
        <div>Rx ID: <strong>${this.currentResult.prescriptionId || 'RX-' + Date.now()}</strong></div>
      </div>
    </div>

    <div class="patient-box">
      <div><strong>Patient Name:</strong> ${patName}</div>
      <div><strong>Date:</strong> ${dateStr}</div>
      <div><strong>Patient ID:</strong> ${patId}</div>
      <div><strong>Diagnosis:</strong> ${this.currentResult.diagnosis || 'Clinical Review'}</div>
    </div>

    <div class="rx-symbol">&#8478;</div>

    <table>
      <thead>
        <tr>
          <th style="width: 25px;">#</th>
          <th>Medication Name</th>
          <th>Strength</th>
          <th>Dosage</th>
          <th>Frequency</th>
          <th>Duration</th>
          <th>Instructions</th>
        </tr>
      </thead>
      <tbody>
        ${meds.map((m, idx) => `
          <tr>
            <td>${idx + 1}</td>
            <td><strong>${m.medicineName || m.name}</strong></td>
            <td>${m.strength || '-'}</td>
            <td>${m.dosage || '-'}</td>
            <td>${m.frequency || '-'}</td>
            <td>${m.duration || '-'}</td>
            <td>${m.specialInstructions || m.foodInstructions || '-'}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>

    <div style="margin-bottom: 15px;">
      <strong style="font-size: 13px; color: #334155;">Clinical Advice / Instructions:</strong>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569; line-height: 1.4;">${this.currentResult.advice || 'Follow medication schedule as prescribed.'}</p>
    </div>

    ${this.currentResult.followUp ? `
    <div style="margin-bottom: 15px;">
      <strong style="font-size: 13px; color: #334155;">Follow-Up:</strong>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #475569;">${this.currentResult.followUp}</p>
    </div>` : ''}

    <div class="footer">
      Digitized via MEDVISION-AI Multi-Modal Clinical Workspace. Document verified by licensed practitioner.
    </div>
  </div>
</body>
</html>`;
  },

  downloadClinicalReport() {
    if (!this.currentResult) {
      window.App.showToast('No active prescription to download.', 'error');
      return;
    }

    const reportHtml = this.buildReportHtml();
    const patName = this.currentResult.patientName || 'Patient';
    const patId = this.currentResult.patientId || 'P-1001';

    // Direct client-side file download via Blob (zero window.open, zero freezing!)
    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Prescription_Report_${patName.replace(/\s+/g, '_')}_${patId}.html`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 150);

    window.App.showToast('Prescription Report downloaded successfully!', 'success');
  },

  printClinicalReport() {
    if (!this.currentResult) {
      window.App.showToast('No active prescription to print.', 'error');
      return;
    }

    const reportHtml = this.buildReportHtml();

    // Use a clean hidden iframe to print without opening blank tabs or blocking the parent window
    let iframe = document.getElementById('rxPrintIframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'rxPrintIframe';
      iframe.style.position = 'fixed';
      iframe.style.right = '0';
      iframe.style.bottom = '0';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.style.border = '0';
      document.body.appendChild(iframe);
    }

    const doc = iframe.contentWindow.document;
    doc.open();
    doc.write(reportHtml);
    doc.close();

    // Trigger non-blocking print
    setTimeout(() => {
      try {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (e) {
        console.warn('Iframe print fallback:', e);
      }
    }, 250);
  },

  async loadDemoSample() {
    window.App.showToast('Fetching sample printed prescription...', 'info');
    try {
      const response = await fetch('/assets/images/sample_prescription.png');
      const blob = await response.blob();
      const file = new File([blob], 'printed_multimed.png', { type: 'image/png' });
      this.processFile(file);
    } catch (e) {
      window.App.showToast('Could not load sample fixture automatically.', 'error');
    }
  },

  exportCSV() {
    if (!this.currentResult || !this.currentResult.medications) {
      window.App.showToast('No medication data to export.', 'error');
      return;
    }
    const headers = ['Medicine Name', 'Strength', 'Dosage', 'Frequency', 'Duration', 'Instructions', 'Confidence'];
    const rows = this.currentResult.medications.map(m => [
      `"${m.medicineName || m.name}"`, `"${m.strength}"`, `"${m.dosage}"`, `"${m.frequency}"`, `"${m.duration}"`, `"${m.specialInstructions || ''}"`, `"${m.confidence}%"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `prescription_${this.currentResult.patientId || 'verified'}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }
};

window.PrescriptionClient = PrescriptionClient;
document.addEventListener('DOMContentLoaded', () => PrescriptionClient.init());
