/**
 * MEDVISION-AI Multi-Region X-Ray Analysis Client
 * Coordinates radiograph upload, PyTorch MSK damage localization,
 * side-by-side specimen comparison, non-X-ray rejection, and report retrieval.
 */

const XRayClient = {
  currentResult: null,

  init() {
    const dropZone = document.getElementById('xrayDropZone');
    const fileInput = document.getElementById('xrayFileInput');

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
    const validExts = ['.png', '.jpg', '.jpeg', '.dcm', '.dicom'];
    const fileNameLower = file.name.toLowerCase();
    const isValid = validExts.some(ext => fileNameLower.endsWith(ext));

    if (!isValid) {
      window.App.showToast('Please upload a valid radiograph image (PNG, JPG, DICOM).', 'error');
      return;
    }

    const previewContainer = document.getElementById('xrayPreviewContainer');
    const rawPreviewImg = document.getElementById('xrayRawImg');
    const resultsContainer = document.getElementById('xrayResultsContainer');
    const emptyState = document.getElementById('xrayEmptyState');
    const loadingState = document.getElementById('xrayLoading');
    const rejectionBox = document.getElementById('xrayRejectionBox');
    const validFindings = document.getElementById('xrayValidFindings');

    // Show preview if image
    if (file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (rawPreviewImg) rawPreviewImg.src = e.target.result;
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

      window.App.showToast('Executing ResNet-18 anatomical router & TorchXRayVision DenseNet-121...', 'info');

      const response = await window.API.analyzeXRay(formData);

      // Check for backend rejection of non-X-ray images
      if (response.status !== 'success') {
        const errorMsg = response.message || 'not a proper image to scan';
        this.renderRejection(response.data || {}, errorMsg);
        window.App.showToast(`❌ ${errorMsg}`, 'error');
        return;
      }

      const data = response.data || {};
      if (data.isRadiograph === false || data.anatomicalRegion === 'Not a Medical X-Ray') {
        this.renderRejection(data, 'not a proper image to scan');
        window.App.showToast('❌ not a proper image to scan', 'error');
        return;
      }

      this.currentResult = data;
      this.renderResults(data);
      window.App.showToast('X-Ray analyzed and persisted to MongoDB!', 'success');

    } catch (err) {
      console.error(err);
      this.renderRejection({}, err.message || 'not a proper image to scan');
      window.App.showToast(`Error: ${err.message}`, 'error');
    } finally {
      if (loadingState) loadingState.style.display = 'none';
      if (previewContainer) previewContainer.classList.remove('scanning');
    }
  },

  renderRejection(data = {}, message = 'not a proper image to scan') {
    const container = document.getElementById('xrayResultsContainer');
    const emptyState = document.getElementById('xrayEmptyState');
    const rejectionBox = document.getElementById('xrayRejectionBox');
    const validFindings = document.getElementById('xrayValidFindings');
    const rejectMsgEl = document.getElementById('xrayRejectionMessage');
    const rejectGuidanceEl = document.getElementById('xrayRejectionGuidance');
    const pdfBtn = document.getElementById('xrayPdfBtn');
    const printBtn = document.getElementById('xrayPrintBtn');

    if (emptyState) emptyState.style.display = 'none';
    if (pdfBtn) pdfBtn.style.display = 'none';
    if (printBtn) printBtn.style.display = 'none';

    if (rejectionBox) {
      const detected = data.detectedImageType || 'Clinical document or non-radiological photo';
      const warningText = data.warning || 'The uploaded file does not exhibit radiographic characteristics (bone attenuation, skeletal projection).';
      if (rejectMsgEl) {
        rejectMsgEl.innerHTML = `<strong>${warningText}</strong><br><span style="font-size: 0.82rem; color: var(--text-muted); margin-top: 4px; display: inline-block;">Detected content: <span style="color: var(--amber-primary); font-weight: 600;">${detected}</span></span>`;
      }
      if (rejectGuidanceEl) {
        rejectGuidanceEl.textContent = data.patientGuidance || 'Please upload an authentic medical X-ray radiograph in PNG, JPG, or DICOM format (e.g. Chest, Hand, Wrist, Knee, Hip, Shoulder). For prescriptions, please use the Prescription Digitizer.';
      }
      rejectionBox.style.display = 'block';
    }

    if (validFindings) validFindings.style.display = 'none';
    if (container) container.style.display = 'block';
  },

  renderResults(data) {
    const container = document.getElementById('xrayResultsContainer');
    const emptyState = document.getElementById('xrayEmptyState');
    const rejectionBox = document.getElementById('xrayRejectionBox');
    const validFindings = document.getElementById('xrayValidFindings');
    if (!container) return;

    if (rejectionBox) rejectionBox.style.display = 'none';
    if (validFindings) validFindings.style.display = 'block';

    // Badges & Overview
    const regionEl = document.getElementById('xrayRegion');
    const regionConfEl = document.getElementById('xrayRegionConf');
    const regionConfBadge = document.getElementById('xrayRegionConfBadge');
    const statusEl = document.getElementById('xrayStatus');
    const modelBadge = document.getElementById('xrayModelBadge');
    const affectedBoneEl = document.getElementById('xrayBone');
    const impressionEl = document.getElementById('xrayImpression');
    const originalImg = document.getElementById('xrayOriginalImg');
    const specimenImg = document.getElementById('xraySpecimenImg');
    const pdfBtn = document.getElementById('xrayPdfBtn');
    const printBtn = document.getElementById('xrayPrintBtn');

    if (regionEl) regionEl.textContent = data.anatomicalRegion || 'General';

    // Confidence badge calculation (Never use fallback 85% on 0!)
    const hasConf = typeof data.confidence === 'number' && data.confidence > 0;
    const hasRegionConf = typeof data.regionConfidence === 'number' && data.regionConfidence > 0;

    if (regionConfEl && regionConfBadge) {
      if (hasRegionConf || hasConf) {
        const confNum = (hasRegionConf ? data.regionConfidence : data.confidence) * 100;
        regionConfEl.textContent = `${confNum.toFixed(1)}% confidence`;
        regionConfBadge.style.display = 'inline-flex';
      } else {
        regionConfBadge.style.display = 'none';
      }
    }
    
    if (modelBadge) {
      modelBadge.textContent = data.anatomicalRegion === 'Chest' ? 'TorchXRayVision DenseNet-121' : 'Multi-Task ResNet-18 MSK';
    }

    if (statusEl) {
      if (data.isAbnormal) {
        statusEl.className = 'badge badge-rose';
        statusEl.textContent = 'ABNORMALITY / DEFECT IDENTIFIED';
      } else {
        statusEl.className = 'badge badge-green';
        statusEl.textContent = 'NORMAL RADIOGRAPHIC STUDY';
      }
    }

    if (affectedBoneEl) {
      affectedBoneEl.textContent = data.affectedBone ? data.affectedBone.replace(/_/g, ' ') : 'General structure';
    }

    if (impressionEl) {
      impressionEl.textContent = data.clinicalImpression || 'Radiological evaluation completed with deep-learning feature regression.';
    }

    // Specimen split view
    const rawPreviewImg = document.getElementById('xrayRawImg');
    if (originalImg && rawPreviewImg) {
      originalImg.src = rawPreviewImg.src;
    }
    if (specimenImg) {
      specimenImg.src = data.specimenUrl || (rawPreviewImg ? rawPreviewImg.src : '');
    }

    // Findings Table
    const tbody = document.getElementById('xrayFindingsTableBody');
    if (tbody) {
      tbody.innerHTML = '';
      const findings = data.findings || [];
      if (findings.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td>1</td>
            <td>${data.isAbnormal ? 'Cortical Discontinuity / Fracture' : 'Normal Physiological Structure'}</td>
            <td>${data.affectedBone || data.anatomicalRegion || 'Skeletal region'}</td>
            <td>${data.boundingBoxPixels && data.boundingBoxPixels.length ? `[${data.boundingBoxPixels.join(', ')}]` : 'Global anatomical ROI'}</td>
            <td><span class="badge ${data.isAbnormal ? 'badge-rose' : 'badge-green'}">${hasConf ? (data.confidence * 100).toFixed(1) + '%' : 'Observed'}</span></td>
          </tr>
        `;
      } else {
        findings.forEach((f, idx) => {
          const row = document.createElement('tr');
          const fConf = typeof f.confidence === 'number' ? (f.confidence * 100).toFixed(1) + '%' : 'Observed';
          row.innerHTML = `
            <td>${idx + 1}</td>
            <td><strong style="color: var(--teal-primary);">${f.finding_type || f.pathology_type || 'Lesion / Opacity'}</strong></td>
            <td>${f.affected_bone || f.damage_location || 'Bone'}</td>
            <td style="font-family: var(--font-mono); font-size: 0.75rem;">${f.bbox_pixels ? `[${f.bbox_pixels.join(', ')}]` : 'N/A'}</td>
            <td><span class="badge badge-purple">${fConf}</span></td>
          `;
          tbody.appendChild(row);
        });
      }
    }

    // PDF Download & Print Buttons
    if (pdfBtn) {
      if (data.reportPdfUrl) {
        pdfBtn.style.display = 'inline-flex';
        pdfBtn.href = data.reportPdfUrl;
      } else {
        pdfBtn.style.display = 'none';
      }
    }
    if (printBtn) {
      printBtn.style.display = 'inline-flex';
    }

    if (emptyState) emptyState.style.display = 'none';
    container.style.display = 'block';
  },

  printReport() {
    if (!this.currentResult) return;
    const d = this.currentResult;

    const reportHtml = `<!DOCTYPE html>
<html>
<head>
  <title>Radiology Report - ${d.patientName || 'Patient'}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; padding: 30px; margin: 0; background: #fff; }
    .rx-card { max-width: 800px; margin: 0 auto; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; }
    .header { border-bottom: 2px solid #0284c7; padding-bottom: 12px; margin-bottom: 20px; }
    .title { font-size: 20px; font-weight: bold; color: #0284c7; }
    .patient-box { background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; line-height: 1.5; }
    .finding { background: #fef2f2; border: 1px solid #fecaca; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; }
    .normal { background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; }
    .footer { margin-top: 30px; border-top: 1px solid #cbd5e1; padding-top: 10px; font-size: 11px; color: #64748b; text-align: center; }
  </style>
</head>
<body>
  <div class="rx-card">
    <div class="header">
      <div class="title">MEDVISION-AI Multi-Region Radiography Assessment</div>
      <div style="font-size: 13px; color: #64748b;">Clinical Decision Support Report</div>
    </div>
    <div class="patient-box">
      <strong>Patient:</strong> ${d.patientName || 'Patient'} (${d.patientId})<br>
      <strong>Study:</strong> X-Ray Radiograph (${d.anatomicalRegion || 'General'})<br>
      <strong>Date:</strong> ${new Date(d.createdAt || Date.now()).toLocaleString()}<br>
      <strong>Analysis ID:</strong> ${d.analysisId}
    </div>
    <div class="${d.isAbnormal ? 'finding' : 'normal'}">
      <strong>Diagnostic Result:</strong> ${d.isAbnormal ? 'ABNORMALITY / DEFECT IDENTIFIED' : 'NORMAL RADIOGRAPH'}<br>
      <strong>Identified Structure:</strong> ${d.affectedBone || d.anatomicalRegion}<br>
      <strong>Impression:</strong> ${d.clinicalImpression || 'Evaluation complete'}
    </div>
    <div class="footer">
      Deep learning decision support output generated by PyTorch Multi-Task Networks. Must be correlated with licensed clinical examination.
    </div>
  </div>
</body>
</html>`;

    // Non-blocking hidden iframe print
    let iframe = document.getElementById('xrayPrintIframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.id = 'xrayPrintIframe';
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
    window.App.showToast('Fetching sample wrist fracture radiograph...', 'info');
    try {
      const response = await fetch('/assets/images/sample_wrist.png');
      const blob = await response.blob();
      const file = new File([blob], 'sample_wrist_trauma.png', { type: 'image/png' });
      this.processFile(file);
    } catch (e) {
      window.App.showToast('Could not load sample fixture automatically.', 'error');
    }
  }
};

window.XRayClient = XRayClient;
document.addEventListener('DOMContentLoaded', () => XRayClient.init());
