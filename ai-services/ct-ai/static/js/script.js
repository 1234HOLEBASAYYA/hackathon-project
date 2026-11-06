/**
 * MedVision-AI — CT Scan Image Analyzer Client Script
 * Handles image upload, visual progress simulation, API requests,
 * dynamic rendering of structured reports, and PDF download.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  if (window.lucide) {
    lucide.createIcons();
  }

  // DOM Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const previewContainer = document.getElementById('preview-container');
  const dropzonePrompt = document.getElementById('dropzone-prompt');
  const imagePreview = document.getElementById('image-preview');
  const clearBtn = document.getElementById('clear-btn');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const fileMetaBar = document.getElementById('file-meta-bar');
  const metaFilename = document.getElementById('meta-filename');
  const metaFilesize = document.getElementById('meta-filesize');
  const analyzeBtn = document.getElementById('analyze-btn');
  const analyzeBtnText = document.getElementById('analyze-btn-text');
  const loadSampleBtn = document.getElementById('load-sample-btn');

  // States
  const emptyState = document.getElementById('empty-state');
  const loadingState = document.getElementById('loading-state');
  const errorState = document.getElementById('error-state');
  const reportSection = document.getElementById('report-section');

  const progressHeading = document.getElementById('progress-heading');
  const progressStatus = document.getElementById('progress-status');
  const progressFill = document.getElementById('progress-fill');
  const step1 = document.getElementById('step-1');
  const step2 = document.getElementById('step-2');
  const step3 = document.getElementById('step-3');

  const errorTitle = document.getElementById('error-title');
  const errorDetail = document.getElementById('error-detail');
  const retryBtn = document.getElementById('retry-btn');
  const dismissErrorBtn = document.getElementById('dismiss-error-btn');

  const downloadPdfBtn = document.getElementById('download-pdf-btn');
  const analyzeAnotherBtn = document.getElementById('analyze-another-btn');
  const sysStatusIndicator = document.getElementById('system-status-indicator');
  const sysStatusText = document.getElementById('system-status-text');

  // In-memory state
  let currentSelectedFile = null;
  let currentReportData = null;
  let currentServerImageId = null;
  let progressInterval = null;

  // 1. Health Check
  async function performHealthCheck() {
    try {
      const res = await fetch('/api/health');
      if (!res.ok) throw new Error('Health endpoint returned error');
      const data = await res.json();
      
      if (data.gemini && data.gemini.api_key_configured) {
        sysStatusIndicator.innerHTML = `
          <span class="status-dot" style="background: #10b981; box-shadow: 0 0 8px #10b981;"></span>
          <span class="status-text">${data.gemini.configured_model || 'Gemini 3.8 Flash'} Online</span>
        `;
      } else {
        sysStatusIndicator.innerHTML = `
          <span class="status-dot" style="background: #f59e0b; box-shadow: 0 0 8px #f59e0b;"></span>
          <span class="status-text" style="color: #fbbf24;">API Key Missing</span>
        `;
      }
    } catch (err) {
      console.warn('Backend health check error:', err);
      sysStatusIndicator.innerHTML = `
        <span class="status-dot" style="background: #ef4444; box-shadow: 0 0 8px #ef4444;"></span>
        <span class="status-text" style="color: #f87171;">Backend Offline</span>
      `;
    }
  }
  performHealthCheck();

  // 2. File Selection & Drag-and-Drop
  browseBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropzone.addEventListener('click', () => {
    if (!currentSelectedFile) {
      fileInput.click();
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleSelectedFile(e.target.files[0]);
    }
  });

  ['dragenter', 'dragover'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('drag-active');
    });
  });

  ['dragleave', 'drop'].forEach(evt => {
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('drag-active');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleSelectedFile(e.dataTransfer.files[0]);
    }
  });

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function handleSelectedFile(file) {
    if (!file) return;

    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
    if (!validTypes.includes(file.type) && !file.name.match(/\.(png|jpe?g|webp)$/i)) {
      showError('Unsupported File Format', 'Please upload a PNG, JPG, or JPEG image of your CT scan or radiograph.');
      return;
    }

    if (file.name.match(/(prescri|priscrition|prescription|rx_|doctor_note)/i)) {
      showError(
        'Incompatible Image Type',
        'This file appears to be a medical prescription document ("' + file.name + '"). The CT Analysis module is strictly reserved for CT scans. Please upload a valid CT scan or radiograph.'
      );
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      showError('File Too Large', 'Maximum image upload size is 15 MB. Please select a smaller slice or compress the image.');
      return;
    }

    currentSelectedFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      imagePreview.src = e.target.result;
      dropzonePrompt.style.display = 'none';
      previewContainer.style.display = 'flex';
      fileMetaBar.style.display = 'flex';
      metaFilename.textContent = file.name;
      metaFilesize.textContent = formatBytes(file.size);
      analyzeBtn.disabled = false;
      analyzeBtnText.textContent = 'Run Visual Analysis';

      // Hide error if present
      errorState.style.display = 'none';
      if (window.lucide) lucide.createIcons();
    };
    reader.readAsDataURL(file);
  }

  function clearSelectedFile() {
    currentSelectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewContainer.style.display = 'none';
    fileMetaBar.style.display = 'none';
    dropzonePrompt.style.display = 'flex';
    analyzeBtn.disabled = true;
    analyzeBtnText.textContent = 'Run Visual Analysis';
  }

  clearBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  removeFileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearSelectedFile();
  });

  // 3. Load Sample Demo Image
  loadSampleBtn.addEventListener('click', async () => {
    try {
      loadSampleBtn.disabled = true;
      loadSampleBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Loading...';
      if (window.lucide) lucide.createIcons();

      const res = await fetch('/api/sample');
      if (!res.ok) throw new Error('Sample scan not found on server');
      const blob = await res.blob();
      const sampleFile = new File([blob], 'demo_chest_ct_sample.jpeg', { type: 'image/jpeg' });
      handleSelectedFile(sampleFile);
    } catch (err) {
      showError('Sample Load Error', err.message);
    } finally {
      loadSampleBtn.disabled = false;
      loadSampleBtn.innerHTML = '<i data-lucide="sparkles"></i> Load Verified Test Case';
      if (window.lucide) lucide.createIcons();
    }
  });

  // 4. Progress Stepper
  function startProgressSimulation() {
    emptyState.style.display = 'none';
    reportSection.style.display = 'none';
    errorState.style.display = 'none';
    loadingState.style.display = 'flex';

    let progress = 10;
    progressFill.style.width = '10%';
    progressHeading.textContent = 'Analyzing CT Scan Image...';
    progressStatus.textContent = 'Validating file integrity & image density values...';

    step1.className = 'check-item active';
    step1.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Image validation & format normalization';
    step2.className = 'check-item pending';
    step2.innerHTML = '<i data-lucide="circle"></i> Gemini AI clinical vision feature extraction';
    step3.className = 'check-item pending';
    step3.innerHTML = '<i data-lucide="circle"></i> Structured radiological schema verification';
    if (window.lucide) lucide.createIcons();

    progressInterval = setInterval(() => {
      progress += Math.floor(Math.random() * 8) + 3;
      if (progress >= 35 && progress < 70) {
        progressStatus.textContent = 'Querying Gemini Clinical Vision API with zero-hallucination prompt...';
        step1.className = 'check-item done';
        step1.innerHTML = '<i data-lucide="check-circle-2"></i> Image validated and normalized';
        step2.className = 'check-item active';
        step2.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Gemini AI clinical vision feature extraction';
      } else if (progress >= 70 && progress < 92) {
        progressStatus.textContent = 'Verifying structured radiological schema & clinical uncertainty standards...';
        step2.className = 'check-item done';
        step2.innerHTML = '<i data-lucide="check-circle-2"></i> Clinical features extracted';
        step3.className = 'check-item active';
        step3.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Structured radiological schema verification';
      } else if (progress >= 92) {
        progress = 92; // hold at 92% until API response completes
      }
      progressFill.style.width = progress + '%';
      if (window.lucide) lucide.createIcons();
    }, 450);
  }

  function stopProgressSimulation() {
    if (progressInterval) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }

  // 5. Error Handling
  function showError(title, message) {
    stopProgressSimulation();
    loadingState.style.display = 'none';
    reportSection.style.display = 'none';
    emptyState.style.display = 'none';
    errorState.style.display = 'block';

    errorTitle.textContent = title || 'Analysis Interrupted';
    errorDetail.textContent = message || 'An unexpected error occurred during processing.';
    if (window.lucide) lucide.createIcons();
  }

  dismissErrorBtn.addEventListener('click', () => {
    errorState.style.display = 'none';
    if (!currentReportData) {
      emptyState.style.display = 'flex';
    } else {
      reportSection.style.display = 'flex';
    }
  });

  retryBtn.addEventListener('click', () => {
    if (currentSelectedFile) {
      runAnalysis();
    } else {
      showError('No Image Selected', 'Please upload a CT scan image to analyze.');
    }
  });

  // 6. Analyze Action
  analyzeBtn.addEventListener('click', runAnalysis);

  async function runAnalysis() {
    if (!currentSelectedFile) return;

    startProgressSimulation();
    analyzeBtn.disabled = true;

    const formData = new FormData();
    formData.append('file', currentSelectedFile);

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok) {
        const errorMsg = result.message || result.error || 'Server returned an error status.';
        throw new Error(errorMsg);
      }

      // Finish progress
      progressFill.style.width = '100%';
      step3.className = 'check-item done';
      step3.innerHTML = '<i data-lucide="check-circle-2"></i> Schema verified';
      if (window.lucide) lucide.createIcons();

      setTimeout(() => {
        stopProgressSimulation();
        loadingState.style.display = 'none';
        renderReport(result.data);
      }, 500);

    } catch (err) {
      console.error('Analysis failed:', err);
      showError('Analysis Failed', err.message);
    } finally {
      analyzeBtn.disabled = false;
    }
  }

  // 7. Render Report
  function renderReport(report) {
    currentReportData = report;
    currentServerImageId = report.image_preprocessing ? report.image_preprocessing.server_image_id : null;

    // Report Header
    document.getElementById('report-title-text').textContent = report.report_title || 'AI-Assisted CT Image Analysis Report';
    document.getElementById('chip-filename').innerHTML = `<i data-lucide="file"></i> ${report.filename || 'CT_Scan.jpg'}`;
    document.getElementById('chip-timestamp').innerHTML = `<i data-lucide="clock"></i> ${report.generated_at || 'Just now'}`;
    const modelUsed = report.model_used || 'Gemini 3.8 Flash';
    document.getElementById('chip-model').innerHTML = `<i data-lucide="sparkles"></i> ${modelUsed}`;

    // Section 1: Image Info
    const info = report.image_information || {};
    document.getElementById('rep-image-type').textContent = info.image_type || 'CT Scan Slice';
    
    let dims = info.image_dimensions;
    if (report.image_preprocessing && report.image_preprocessing.original_dimensions) {
      dims = report.image_preprocessing.original_dimensions.formatted;
    }
    document.getElementById('rep-dimensions').textContent = dims || 'Unknown';
    document.getElementById('rep-quality').textContent = info.image_quality || 'Adequate';

    const limitsCallout = document.getElementById('rep-image-limitations');
    limitsCallout.innerHTML = '';
    const imgLimits = info.limitations || [];
    imgLimits.forEach(l => {
      const chip = document.createElement('div');
      chip.className = 'limit-chip';
      chip.innerHTML = `<i data-lucide="alert-circle" style="width:13px; height:13px;"></i> <span>${escapeHtml(l)}</span>`;
      limitsCallout.appendChild(chip);
    });

    // Section 2: Visual Observations
    const obsContainer = document.getElementById('rep-visual-observations');
    obsContainer.innerHTML = '';
    const visualObs = report.visual_observations || [];
    if (visualObs.length === 0) {
      obsContainer.innerHTML = '<p class="obs-desc">No focal visual opacities detected on screening view.</p>';
    } else {
      visualObs.forEach(obs => {
        const card = document.createElement('div');
        card.className = 'obs-item-card';
        card.innerHTML = `
          <div class="obs-header-row">
            <span class="obs-title">${escapeHtml(obs.observation || 'Visible density pattern')}</span>
            <span class="badge-observed">VISUALLY OBSERVED</span>
          </div>
          <div class="obs-location"><i data-lucide="map-pin" style="width:13px; height:13px;"></i> Location: ${escapeHtml(obs.location || 'Indeterminate')}</div>
          <p class="obs-desc">${escapeHtml(obs.description || '')}</p>
        `;
        obsContainer.appendChild(card);
      });
    }

    // Section 3: Potential Findings
    const findingsContainer = document.getElementById('rep-potential-findings');
    findingsContainer.innerHTML = '';
    const findings = report.potential_findings || [];
    if (findings.length === 0) {
      findingsContainer.innerHTML = '<p class="finding-desc">No anomalous focal findings identified for differential consideration.</p>';
    } else {
      findings.forEach(f => {
        const card = document.createElement('div');
        card.className = 'finding-item-card';
        card.innerHTML = `
          <div class="finding-header-row">
            <span class="finding-title">${escapeHtml(f.finding || 'Differential Consideration')}</span>
            <span class="badge-uncertain">NON-DEFINITIVE / UNCERTAIN</span>
          </div>
          <div class="finding-location"><i data-lucide="map-pin" style="width:13px; height:13px;"></i> Location: ${escapeHtml(f.location || 'Indeterminate')}</div>
          <p class="finding-desc">${escapeHtml(f.description || '')}</p>
          <div class="supporting-badge"><strong>Visual Evidence:</strong> ${escapeHtml(f.supporting_visual_observation || 'Density contrast in slice')}</div>
        `;
        findingsContainer.appendChild(card);
      });
    }

    // Section 4: Summary
    document.getElementById('rep-summary').textContent = report.summary || 'Image-based visual evaluation completed.';

    // Section 5: Recommendations & Limitations
    const recList = document.getElementById('rep-recommendations');
    recList.innerHTML = '';
    (report.recommendations_for_review || []).forEach(r => {
      const li = document.createElement('li');
      li.textContent = r;
      recList.appendChild(li);
    });

    const limList = document.getElementById('rep-limitations');
    limList.innerHTML = '';
    (report.limitations || []).forEach(l => {
      const li = document.createElement('li');
      li.textContent = l;
      limList.appendChild(li);
    });

    // Disclaimer
    if (report.medical_disclaimer) {
      document.getElementById('rep-disclaimer').textContent = report.medical_disclaimer;
    }

    // Display report
    reportSection.style.display = 'flex';
    if (window.lucide) lucide.createIcons();
    reportSection.scrollIntoView({ behavior: 'smooth' });
  }

  // 8. Download PDF Report
  downloadPdfBtn.addEventListener('click', async () => {
    if (!currentReportData) return;

    try {
      downloadPdfBtn.disabled = true;
      downloadPdfBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Generating PDF...';
      if (window.lucide) lucide.createIcons();

      const res = await fetch('/api/generate-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          report: currentReportData,
          server_image_id: currentServerImageId
        })
      });

      const result = await res.json();
      if (!res.ok) throw new Error(result.message || 'Failed to generate PDF');

      // Trigger download
      window.location.href = result.download_url;

    } catch (err) {
      alert('PDF Generation Error: ' + err.message);
    } finally {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.innerHTML = '<i data-lucide="download"></i> <span>Download PDF Report</span>';
      if (window.lucide) lucide.createIcons();
    }
  });

  // 9. Analyze Another Image
  analyzeAnotherBtn.addEventListener('click', () => {
    reportSection.style.display = 'none';
    clearSelectedFile();
    emptyState.style.display = 'flex';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});
