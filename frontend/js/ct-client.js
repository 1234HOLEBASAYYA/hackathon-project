/**
 * MEDVISION-AI CT Scan Clinical Vision Client
 * Manages CT slice upload, Gemini clinical vision processing,
 * objective observations breakdown, and differential findings.
 */

const CTClient = {
  currentResult: null,

  init() {
    const dropZone = document.getElementById('ctDropZone');
    const fileInput = document.getElementById('ctFileInput');

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
    const validExts = ['.png', '.jpg', '.jpeg', '.webp', '.dcm', '.dicom'];
    const fileNameLower = file.name.toLowerCase();
    const isValid = validExts.some(ext => fileNameLower.endsWith(ext));

    if (!isValid) {
      window.App.showToast('Please upload a valid CT slice image (PNG, JPG, DICOM).', 'error');
      return;
    }

    const previewContainer = document.getElementById('ctPreviewContainer');
    const previewImg = document.getElementById('ctPreviewImg');
    const resultsContainer = document.getElementById('ctResultsContainer');
    const emptyState = document.getElementById('ctEmptyState');
    const loadingState = document.getElementById('ctLoading');
    const rejectionBox = document.getElementById('ctRejectionBox');
    const validFindings = document.getElementById('ctValidFindings');

    // Show preview if image
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
    }

    if (loadingState) loadingState.style.display = 'block';
    if (resultsContainer) resultsContainer.style.display = 'none';
    if (rejectionBox) rejectionBox.style.display = 'none';
    if (validFindings) validFindings.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';

    try {
      const activePatient = window.PatientManager.getActivePatient();
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patientId', activePatient.patientId);
      formData.append('patientName', activePatient.name);

      window.App.showToast('Executing Gemini Clinical Vision zero-hallucination analysis...', 'info');

      const response = await window.API.analyzeCTScan(formData);

      const data = response.data || {};
      if (response.status !== 'success' || data.isCompatibleCtScan === false) {
        const errorMsg = response.message || 'not a proper image to scan';
        this.renderRejection(data, 'not a proper image to scan');
        window.App.showToast(`❌ ${errorMsg}`, 'error');
        return;
      }

      this.currentResult = data;
      this.renderResults(data);
      window.App.showToast('CT scan findings structured and persisted to MongoDB!', 'success');

    } catch (err) {
      console.error(err);
      this.renderRejection({}, 'not a proper image to scan');
      window.App.showToast(`❌ not a proper image to scan`, 'error');
    } finally {
      if (loadingState) loadingState.style.display = 'none';
      if (previewContainer) previewContainer.classList.remove('scanning');
    }
  },

  renderRejection(data = {}, message = 'not a proper image to scan') {
    const container = document.getElementById('ctResultsContainer');
    const emptyState = document.getElementById('ctEmptyState');
    const rejectionBox = document.getElementById('ctRejectionBox');
    const validFindings = document.getElementById('ctValidFindings');
    const rejectMsgEl = document.getElementById('ctRejectionMessage');
    const rejectGuidanceEl = document.getElementById('ctRejectionGuidance');
    const badgeEl = document.getElementById('ctDetectedBadge');
    const actionsEl = document.getElementById('ctRejectionActions');
    const downloadBtn = document.getElementById('ctDownloadBtn');
    const printBtn = document.getElementById('ctPrintBtn');

    if (emptyState) emptyState.style.display = 'none';
    if (downloadBtn) downloadBtn.style.display = 'none';
    if (printBtn) printBtn.style.display = 'none';

    if (rejectionBox) {
      const modality = (data.detectedModality || '').toLowerCase();
      let badgeLabel = 'Specimen Incompatible with CT';
      let badgeClass = 'badge-rose';

      if (modality === 'mri') {
        badgeLabel = 'Magnetic Resonance Imaging (Brain/Spine MRI) Detected';
        badgeClass = 'badge-purple';
      } else if (modality === 'xray') {
        badgeLabel = 'Plain 2D Radiograph (X-Ray) Detected';
        badgeClass = 'badge-teal';
      } else if (modality === 'prescription_doc' || modality.includes('prescription')) {
        badgeLabel = 'Doctor Prescription Document Detected';
        badgeClass = 'badge-amber';
      } else if (modality === 'photograph') {
        badgeLabel = 'Non-Medical Color Photo Detected';
        badgeClass = 'badge-rose';
      }

      if (badgeEl) {
        badgeEl.innerHTML = `<span class="badge ${badgeClass}" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">${badgeLabel}</span>`;
      }

      if (rejectMsgEl) {
        const warning = data.incompatibilityReason || data.warning || 'The uploaded file is not an authentic CT scan slice.';
        rejectMsgEl.innerHTML = `<strong>${warning}</strong>`;
      }

      if (rejectGuidanceEl) {
        rejectGuidanceEl.textContent = data.patientGuidance || 'Please upload an authentic axial CT scan slice, helical reconstruction, or scout view in PNG, JPG, or DICOM format.';
      }

      if (actionsEl) {
        if (modality === 'xray') {
          actionsEl.innerHTML = `
            <a href="/xray.html" class="btn btn-purple btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 600;">
              <span>🔬</span> Switch to Multi-Region X-Ray Diagnostic AI
            </a>
          `;
        } else if (modality === 'prescription_doc' || modality.includes('prescription')) {
          actionsEl.innerHTML = `
            <a href="/prescription.html" class="btn btn-teal btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 600;">
              <span>📝</span> Switch to Doctor Prescription OCR & Digitizer
            </a>
          `;
        } else if (modality === 'mri') {
          actionsEl.innerHTML = `
            <a href="/dashboard.html" class="btn btn-cyan btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem; font-weight: 600;">
              <span>📋</span> View Patient Clinical Timeline
            </a>
          `;
        } else {
          actionsEl.innerHTML = `
            <a href="/xray.html" class="btn btn-outline btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem;">
              <span>🔬</span> X-Ray Diagnostic AI
            </a>
            <a href="/prescription.html" class="btn btn-outline btn-sm" style="display: inline-flex; align-items: center; gap: 0.4rem;">
              <span>📝</span> Prescription Reader
            </a>
          `;
        }
      }

      rejectionBox.style.display = 'block';
    }

    if (validFindings) validFindings.style.display = 'none';
    if (container) container.style.display = 'block';
  },

  renderResults(data) {
    if (!data || data.isCompatibleCtScan === false) {
      this.renderRejection(data, 'not a proper image to scan');
      return;
    }

    const container = document.getElementById('ctResultsContainer');
    const emptyState = document.getElementById('ctEmptyState');
    const rejectionBox = document.getElementById('ctRejectionBox');
    const validFindings = document.getElementById('ctValidFindings');
    if (!container) return;

    if (rejectionBox) rejectionBox.style.display = 'none';
    if (validFindings) validFindings.style.display = 'block';

    // Report Title & Modality
    const titleEl = document.getElementById('ctReportTitle');
    const modalityEl = document.getElementById('ctModalityBadge');
    const summaryEl = document.getElementById('ctSummaryText');
    const limitationsEl = document.getElementById('ctLimitations');
    const recsEl = document.getElementById('ctRecommendations');
    const downloadBtn = document.getElementById('ctDownloadBtn');
    const printBtn = document.getElementById('ctPrintBtn');

    if (titleEl) titleEl.textContent = data.reportTitle || 'AI-Assisted CT Scan Analysis';
    if (modalityEl) modalityEl.textContent = (data.detectedModality || 'CT Scan').toUpperCase();
    if (summaryEl) summaryEl.textContent = data.summary || 'Visual density assessment complete.';

    // Visual Observations Table
    const obsTableBody = document.getElementById('ctObsTableBody');
    if (obsTableBody) {
      obsTableBody.innerHTML = '';
      const obs = data.visualObservations || [];
      if (obs.length === 0) {
        obsTableBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color: var(--text-muted);">No hyperdense or hypodense abnormal lesions recognized.</td></tr>`;
      } else {
        obs.forEach((o, i) => {
          const tr = document.createElement('tr');
          const feature = o.observation || o.density_or_structure || o.feature || 'Visual Feature';
          const loc = o.location || o.anatomical_location || 'Thoracic / Cranial Structure';
          const desc = o.description || o.observation_summary || 'Observed';
          tr.innerHTML = `
            <td><strong>#${i + 1}</strong></td>
            <td><strong style="color: var(--teal-primary);">${feature}</strong></td>
            <td>${loc}</td>
            <td style="font-size: 0.8125rem; color: var(--text-secondary);">${desc}</td>
          `;
          obsTableBody.appendChild(tr);
        });
      }
    }

    // Potential Differential Findings Table
    const findingsTableBody = document.getElementById('ctFindingsTableBody');
    if (findingsTableBody) {
      findingsTableBody.innerHTML = '';
      const findings = data.potentialFindings || [];
      if (findings.length === 0) {
        findingsTableBody.innerHTML = `<tr><td colspan="3" style="text-align:center; color: var(--text-muted);">No suspicious differential considerations identified on this slice.</td></tr>`;
      } else {
        findings.forEach(f => {
          const tr = document.createElement('tr');
          const condition = f.finding || f.finding_or_condition || 'Clinical Condition';
          const cert = f.certainty || 'uncertain';
          const reason = f.description || f.reasoning || f.supporting_visual_observation || 'Correlate with clinical findings.';
          
          let certBadge = `<span class="badge badge-amber">Differential (${cert})</span>`;
          if (cert === 'observed') certBadge = `<span class="badge badge-teal">Observed</span>`;
          if (cert === 'suspicious') certBadge = `<span class="badge badge-rose">Suspicious</span>`;

          tr.innerHTML = `
            <td><strong style="color: var(--amber-primary);">${condition}</strong></td>
            <td>${certBadge}</td>
            <td style="font-size: 0.8125rem; color: var(--text-secondary);">${reason}</td>
          `;
          findingsTableBody.appendChild(tr);
        });
      }
    }

    // Recommendations
    if (recsEl) {
      recsEl.innerHTML = '';
      const recs = data.recommendations || [];
      if (recs.length === 0) {
        recsEl.innerHTML = '<li>Formal interpretation by a qualified neuroradiologist or thoracic specialist.</li>';
      } else {
        recs.forEach(r => {
          const li = document.createElement('li');
          li.textContent = r;
          recsEl.appendChild(li);
        });
      }
    }

    // Study Limitations
    if (limitationsEl) {
      limitationsEl.innerHTML = '';
      const lims = data.limitations || [];
      if (lims.length === 0) {
        limitationsEl.innerHTML = '<li>Single 2D axial slice does not replace full volumetric scan.</li>';
      } else {
        lims.forEach(l => {
          const li = document.createElement('li');
          li.textContent = l;
          limitationsEl.appendChild(li);
        });
      }
    }

    if (downloadBtn) downloadBtn.style.display = 'inline-flex';
    if (printBtn) printBtn.style.display = 'inline-flex';

    if (emptyState) emptyState.style.display = 'none';
    container.style.display = 'block';
  },

  buildReportHtml() {
    if (!this.currentResult) return '';
    const d = this.currentResult;
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>CT Report - ${d.patientId || 'Patient'}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; padding: 30px; margin: 0; background: #fff; }
    .rx-card { max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; }
    .header { border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; }
    .title { font-size: 20px; font-weight: bold; color: #0284c7; }
    .patient-box { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; line-height: 1.5; }
    .summary { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; margin-bottom: 20px; }
    th, td { border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; font-size: 12px; }
    th { background: #f1f5f9; color: #334155; }
    .footer { margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 10px; font-size: 11px; color: #64748b; text-align: center; }
  </style>
</head>
<body>
  <div class="rx-card">
    <div class="header">
      <div class="title">${d.reportTitle || 'CT Clinical Vision Analysis Report'}</div>
      <div style="font-size: 12px; color: #64748b;">Modality: ${d.detectedModality || 'CT Scan'} &bull; Analysis ID: ${d.analysisId}</div>
    </div>
    <div class="patient-box">
      <strong>Patient ID:</strong> ${d.patientId || 'N/A'}<br>
      <strong>Evaluation Date:</strong> ${new Date(d.createdAt || Date.now()).toLocaleString()}
    </div>
    <div class="summary">
      <strong>Evaluation Summary:</strong>
      <p style="margin: 4px 0 0 0; font-size: 13px; color: #334155;">${d.summary || 'Analysis complete.'}</p>
    </div>
    <h4 style="margin-bottom: 6px; font-size: 13px;">Objective Physical Observations:</h4>
    <table>
      <thead><tr><th>#</th><th>Feature / Density</th><th>Location</th><th>Description</th></tr></thead>
      <tbody>
        ${(d.visualObservations || []).map((o, idx) => `
          <tr>
            <td>${idx + 1}</td>
            <td><strong>${o.observation || o.density_or_structure || o.feature}</strong></td>
            <td>${o.location || o.anatomical_location}</td>
            <td>${o.description || o.observation_summary}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
    <h4 style="margin-bottom: 6px; font-size: 13px;">Potential Differential Considerations:</h4>
    <table>
      <thead><tr><th>Condition / Finding</th><th>Certainty</th><th>Clinical Reasoning</th></tr></thead>
      <tbody>
        ${(d.potentialFindings || []).map(f => `
          <tr>
            <td><strong>${f.finding || f.finding_or_condition}</strong></td>
            <td>${f.certainty}</td>
            <td>${f.description || f.reasoning}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
    <div class="footer">
      ${d.medicalDisclaimer || 'This AI-assisted report is for educational and clinical decision support purposes only.'}
    </div>
  </div>
</body>
</html>`;
  },

  downloadClinicalReport() {
    if (!this.currentResult) {
      window.App.showToast('No active CT report to download.', 'error');
      return;
    }

    const reportHtml = this.buildReportHtml();
    const patId = this.currentResult.patientId || 'Patient';

    const blob = new Blob([reportHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `CT_Report_${patId}_${Date.now()}.html`;
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }, 150);

    window.App.showToast('CT Report downloaded successfully!', 'success');
  },

  printReport() {
    if (!this.currentResult) return;
    const reportHtml = this.buildReportHtml();

    let iframe = document.getElementById('ctPrintIframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'ctPrintIframe';
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

    setTimeout(() => {
      try {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (e) {
        console.warn('Iframe print error:', e);
      }
    }, 250);
  },

  async loadDemoSample() {
    window.App.showToast('Fetching sample Brain Cancer CT scan...', 'info');
    try {
      const response = await fetch('/assets/images/sample_ct.jpg');
      const blob = await response.blob();
      const file = new File([blob], 'cranial_ct_slice.jpg', { type: 'image/jpeg' });
      this.processFile(file);
    } catch (e) {
      window.App.showToast('Could not load sample fixture automatically.', 'error');
    }
  }
};

window.CTClient = CTClient;
document.addEventListener('DOMContentLoaded', () => CTClient.init());
