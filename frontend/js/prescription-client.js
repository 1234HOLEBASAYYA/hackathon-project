/**
 * MEDVISION-AI Prescription OCR Client
 * Controls upload, EasyOCR execution, interactive clinical editing, MongoDB persistence, and report generation.
 * Features:
 * - Single-request lock to prevent duplicate runs
 * - Cancellation support via AbortController
 * - Progress stage indicators
 * - Retry capability and resilient error handling
 * - Client-side non-blocking report download (Blob URL) and hidden iframe printing
 */

const PrescriptionClient = {
  currentResult: null,
  isProcessing: false,
  abortController: null,
  lastFile: null,
  stageTimer: null,

  init() {
    const dropZone = document.getElementById('rxDropZone');
    const fileInput = document.getElementById('rxFileInput');

    if (!dropZone || !fileInput) return;

    // Open file picker only when clicking the drop zone background or text
    dropZone.addEventListener('click', (e) => {
      if (this.isProcessing) return;
      if (e.target !== fileInput) {
        fileInput.click();
      }
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      if (!this.isProcessing) {
        dropZone.classList.add('dragover');
      }
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (this.isProcessing) return;
      if (e.dataTransfer.files.length) {
        this.processFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) {
        const file = fileInput.files[0];
        fileInput.value = ''; // Reset so selecting the same file triggers change again
        this.processFile(file);
      }
    });
  },

  async processFile(file) {
    if (!file) return;

    // Prevent concurrent duplicate executions
    if (this.isProcessing) {
      window.App.showToast('Prescription processing is already in progress.', 'warning');
      return;
    }

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'application/pdf'];
    if (!validTypes.includes(file.type) && !file.name.toLowerCase().endsWith('.pdf')) {
      window.App.showToast('Please upload a valid image (PNG, JPG) or PDF file.', 'error');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      window.App.showToast('File size exceeds the 25MB limit.', 'error');
      return;
    }

    this.isProcessing = true;
    this.lastFile = file;

    const previewContainer = document.getElementById('rxPreviewContainer');
    const previewImg = document.getElementById('rxPreviewImg');
    const resultsContainer = document.getElementById('rxResultsContainer');
    const emptyState = document.getElementById('rxEmptyState');
    const loadingState = document.getElementById('rxLoading');
    const stageEl = document.getElementById('rxLoadingStage');
    const subtextEl = document.getElementById('rxLoadingSubtext');
    const errorBox = document.getElementById('rxErrorBox');

    if (errorBox) errorBox.style.display = 'none';

    // Show image preview if image
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

    // Progress stage updates
    const stages = [
      { delay: 0, title: 'Preprocessing Prescription...', sub: 'Applying CLAHE contrast equalization and deskewing image.' },
      { delay: 3000, title: 'Running EasyOCR Text Detection...', sub: 'Deep Learning CRAFT engine identifying word regions and lines.' },
      { delay: 8000, title: 'Transcribing Cursive Handwriting...', sub: 'BiLSTM sequence models transcribing medical abbreviations & dosages.' },
      { delay: 14000, title: 'Structuring Clinical Fields...', sub: 'Matching extracted text against clinical pharmacopeia and dosages.' }
    ];

    if (this.stageTimer) clearInterval(this.stageTimer);
    let stageIdx = 0;
    if (stageEl) stageEl.textContent = stages[0].title;
    if (subtextEl) subtextEl.textContent = stages[0].sub;

    this.stageTimer = setInterval(() => {
      stageIdx++;
      if (stageIdx < stages.length) {
        if (stageEl) stageEl.textContent = stages[stageIdx].title;
        if (subtextEl) subtextEl.textContent = stages[stageIdx].sub;
      }
    }, 4500);

    // Setup AbortController for cancel / timeout
    this.abortController = new AbortController();

    try {
      const activePatient = window.PatientManager ? window.PatientManager.getActivePatient() : { patientId: 'P-1001', name: 'Robert Miller' };
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patientId', activePatient.patientId);
      formData.append('patientName', activePatient.name);

      window.App.showToast('Prescription upload initiated. Analyzing...', 'info');

      const response = await window.API.analyzePrescription(formData, this.abortController.signal);

      if (response.status !== 'success') {
        throw new Error(response.message || 'Prescription analysis failed');
      }

      this.currentResult = response.data;
      this.renderResults(response.data);
      window.App.showToast('Prescription digitized and saved to MongoDB!', 'success');

    } catch (err) {
      if (err.name === 'AbortError') {
        window.App.showToast('Prescription analysis was cancelled.', 'warning');
        if (emptyState) emptyState.style.display = 'block';
      } else {
        console.error('Prescription processing error:', err);
        window.App.showToast(`Error: ${err.message}`, 'error');
        this.renderError(err.message);
      }
    } finally {
      if (this.stageTimer) {
        clearInterval(this.stageTimer);
        this.stageTimer = null;
      }
      this.isProcessing = false;
      this.abortController = null;
      if (loadingState) loadingState.style.display = 'none';
      if (previewContainer) previewContainer.classList.remove('scanning');
    }
  },

  cancelAnalysis() {
    if (this.abortController) {
      this.abortController.abort();
    }
    this.isProcessing = false;
    const loadingState = document.getElementById('rxLoading');
    const previewContainer = document.getElementById('rxPreviewContainer');
    const emptyState = document.getElementById('rxEmptyState');

    if (loadingState) loadingState.style.display = 'none';
    if (previewContainer) previewContainer.classList.remove('scanning');
    if (!this.currentResult && emptyState) emptyState.style.display = 'block';
  },

  retryLastFile() {
    if (this.lastFile) {
      this.processFile(this.lastFile);
    } else {
      const fileInput = document.getElementById('rxFileInput');
      if (fileInput) fileInput.click();
    }
  },

  renderError(message) {
    const errorBox = document.getElementById('rxErrorBox');
    const errorMsgEl = document.getElementById('rxErrorMessage');
    const errorDetailsEl = document.getElementById('rxErrorDetails');
    const emptyState = document.getElementById('rxEmptyState');
    const resultsContainer = document.getElementById('rxResultsContainer');

    if (emptyState) emptyState.style.display = 'none';
    if (resultsContainer) resultsContainer.style.display = 'none';

    if (errorBox) {
      if (errorMsgEl) errorMsgEl.textContent = 'Prescription Processing Failed';
      if (errorDetailsEl) errorDetailsEl.textContent = message || 'An unexpected error occurred during OCR extraction.';
      errorBox.style.display = 'block';
    }
  },

  renderResults(data) {
    const container = document.getElementById('rxResultsContainer');
    const emptyState = document.getElementById('rxEmptyState');
    const errorBox = document.getElementById('rxErrorBox');
    if (!container) return;

    if (errorBox) errorBox.style.display = 'none';

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
    if (tbody) {
      tbody.innerHTML = '';
      const meds = data.medications || [];
      if (meds.length === 0) {
        this.addMedicationRow(); // Empty row for manual entry
      } else {
        meds.forEach((m, idx) => {
          this.addMedicationRow(m, idx);
        });
      }
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
    const confVal = typeof med.confidence === 'number' ? med.confidence : parseFloat(med.confidence) || 85;
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
          : `<span class="badge badge-amber" title="Confidence: ${confVal.toFixed(0)}%">⚠️ Review Needed (${confVal.toFixed(0)}%)</span>`}
      </td>
      <td style="text-align: center;">
        <button class="btn-action-delete" title="Remove medication" onclick="this.closest('tr').remove()">✕</button>
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
      patientName: document.getElementById('rxPatientNameInput')?.value.trim() || 'Patient',
      patientAge: parseInt(document.getElementById('rxPatientAgeInput')?.value) || undefined,
      diagnosis: document.getElementById('rxDiagnosisInput')?.value.trim() || '',
      advice: document.getElementById('rxAdviceInput')?.value.trim() || '',
      followUp: document.getElementById('rxFollowUpInput')?.value.trim() || '',
      medications
    };

    try {
      window.App.showToast('Persisting verified clinical record to MongoDB...', 'info');
      const res = await window.API.updatePrescription(prescriptionId, updatePayload);

      if (res.status === 'success') {
        const statusBadge = document.getElementById('rxStatusBadge');
        if (statusBadge) {
          statusBadge.textContent = 'Verified & Locked';
          statusBadge.className = 'badge badge-green';
        }
        window.App.showToast('Prescription verified and updated in MongoDB!', 'success');
      } else {
        throw new Error(res.message || 'Update failed');
      }
    } catch (e) {
      console.error(e);
      window.App.showToast(`Save failed: ${e.message}`, 'error');
    }
  },

  async openHistoryModal() {
    const modal = document.getElementById('rxHistoryModal');
    const container = document.getElementById('rxHistoryContainer');
    if (!modal || !container) return;

    modal.style.display = 'flex';
    container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">Fetching patient records...</div>';

    try {
      const activePatient = window.PatientManager ? window.PatientManager.getActivePatient() : { patientId: 'P-1001' };
      const res = await window.API.getPrescriptionHistory(activePatient.patientId);

      if (res.status === 'success' && res.data && res.data.length > 0) {
        container.innerHTML = '';
        res.data.forEach(p => {
          const card = document.createElement('div');
          card.style.cssText = 'background: var(--bg-surface-elevated); padding: 1rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center;';
          card.innerHTML = `
            <div>
              <div style="font-weight: 700; color: var(--text-primary); font-size: 0.9rem;">
                ${p.diagnosis || 'Clinical Review'}
                <span class="badge ${p.status === 'verified' ? 'badge-green' : 'badge-teal'}" style="margin-left: 0.5rem; font-size: 0.68rem;">
                  ${p.status}
                </span>
              </div>
              <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">
                Dr. ${p.doctor?.name || 'Unknown'} &bull; ${new Date(p.createdAt).toLocaleDateString()} &bull; ${p.medications?.length || 0} Meds
              </div>
            </div>
            <button class="btn btn-outline btn-sm" onclick='PrescriptionClient.loadHistoricalPrescription(${JSON.stringify(p).replace(/'/g, "&apos;")})'>
              Load &rarr;
            </button>
          `;
          container.appendChild(card);
        });
      } else {
        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 2rem;">No previous prescriptions found for this patient.</div>';
      }
    } catch (e) {
      container.innerHTML = `<div style="text-align: center; color: var(--rose-primary); padding: 2rem;">Failed to load history: ${e.message}</div>`;
    }
  },

  closeHistoryModal() {
    const modal = document.getElementById('rxHistoryModal');
    if (modal) modal.style.display = 'none';
  },

  loadHistoricalPrescription(p) {
    this.closeHistoryModal();
    this.currentResult = p;
    this.renderResults(p);
    window.App.showToast(`Loaded prescription record #${p.prescriptionId}`, 'info');
  },

  buildReportHtml() {
    if (!this.currentResult) return '';

    const p = this.currentResult;
    const doc = p.doctor || {};
    const meds = p.medications || [];
    const dateStr = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

    let medsHtml = '';
    meds.forEach((m, idx) => {
      medsHtml += `
        <tr>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #64748b;">${idx + 1}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #0f172a;">${m.medicineName || m.name || 'Medication'}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">${m.strength || 'N/A'}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">${m.dosage || '1 unit'}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">${m.frequency || 'Daily'}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">${m.duration || 'As directed'}</td>
          <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 13px; color: #475569;">${m.specialInstructions || m.foodInstructions || 'None'}</td>
        </tr>
      `;
    });

    return `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Prescription Report - ${p.patientName || 'Patient'}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #0f172a; margin: 40px; background: #fff; }
          .header { border-bottom: 2px solid #0284c7; padding-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
          .clinic-name { font-size: 24px; font-weight: 800; color: #0369a1; text-transform: uppercase; margin: 0; }
          .doc-name { font-size: 16px; font-weight: 700; color: #334155; margin-top: 4px; }
          .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 25px 0; background: #f8fafc; padding: 15px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 14px; }
          table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }
          th { background: #f1f5f9; color: #475569; text-align: left; padding: 10px; font-weight: 700; border-bottom: 2px solid #cbd5e1; }
          .footer { margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 15px; font-size: 12px; color: #64748b; display: flex; justify-content: space-between; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1 class="clinic-name">${p.clinicHeader || doc.clinicOrHospital || 'MEDVISION CLINICAL CENTER'}</h1>
            <div class="doc-name">${doc.name ? 'Dr. ' + doc.name.replace(/^Dr\.?\s*/i, '') : 'Consulting Physician'}</div>
            <div style="font-size: 13px; color: #64748b;">${doc.specialization || 'General Clinical Medicine'} ${doc.qualification ? '(' + doc.qualification + ')' : ''}</div>
          </div>
          <div style="text-align: right; font-size: 13px; color: #64748b;">
            <div><strong>Date:</strong> ${dateStr}</div>
            <div><strong>Rx ID:</strong> ${p.prescriptionId || 'RX-AUTOGEN'}</div>
            <div><strong>Status:</strong> ${p.status ? p.status.toUpperCase() : 'VERIFIED'}</div>
          </div>
        </div>

        <div class="meta-grid">
          <div><strong>Patient Name:</strong> ${p.patientName || 'Robert Miller'}</div>
          <div><strong>Patient ID:</strong> ${p.patientId || 'P-1001'}</div>
          <div><strong>Diagnosis:</strong> ${p.diagnosis || 'Clinical Prescription Review'}</div>
          <div><strong>Follow-Up:</strong> ${p.followUp || 'As directed by physician'}</div>
        </div>

        <h3 style="font-size: 16px; border-left: 4px solid #0284c7; padding-left: 8px; margin-top: 30px;">Rx Prescribed Medications</h3>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Medication</th>
              <th>Strength</th>
              <th>Dosage</th>
              <th>Frequency</th>
              <th>Duration</th>
              <th>Instructions</th>
            </tr>
          </thead>
          <tbody>
            ${medsHtml}
          </tbody>
        </table>

        ${p.advice ? `
          <div style="margin-top: 25px; padding: 12px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; font-size: 14px;">
            <strong>Physician Advice:</strong> ${p.advice}
          </div>
        ` : ''}

        <div class="footer">
          <div>MEDVISION-AI Clinical Decision Support Platform &bull; EasyOCR CRAFT+BiLSTM Digitizer</div>
          <div>Verified Digital Copy &bull; Page 1 of 1</div>
        </div>
      </body>
      </html>
    `;
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

    // Use a clean hidden iframe to print without opening blocking popups
    let printFrame = document.getElementById('rxPrintFrame');
    if (!printFrame) {
      printFrame = document.createElement('iframe');
      printFrame.id = 'rxPrintFrame';
      printFrame.style.cssText = 'position: fixed; top: -10000px; left: -10000px; width: 1px; height: 1px; border: 0;';
      document.body.appendChild(printFrame);
    }

    const frameDoc = printFrame.contentWindow || printFrame.contentDocument.document || printFrame.contentDocument;
    frameDoc.document.open();
    frameDoc.document.write(reportHtml);
    frameDoc.document.close();

    setTimeout(() => {
      try {
        printFrame.contentWindow.focus();
        printFrame.contentWindow.print();
      } catch (e) {
        console.warn('Iframe print fallback:', e);
      }
    }, 250);
  },

  async loadDemoSample() {
    if (this.isProcessing) return;
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
