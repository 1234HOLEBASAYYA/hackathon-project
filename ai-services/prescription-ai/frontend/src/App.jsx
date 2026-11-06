import React, { useState, useEffect, useRef } from 'react';
import {
  Upload,
  FileText,
  CheckCircle,
  AlertTriangle,
  RefreshCw,
  Download,
  Edit2,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  Check,
  X,
  File,
  AlertCircle,
  Cpu,
  ShieldCheck,
  RotateCcw,
  Building,
  User,
  Stethoscope,
  Activity,
  ClipboardList
} from 'lucide-react';
import { apiService } from './services/api';

const UNCLEAR_MARKER = 'Unclear – Manual verification required';
const NOT_DETECTED = 'Not detected';

export default function App() {
  // Backend health & system info
  const [health, setHealth] = useState(null);
  const [healthError, setHealthError] = useState(null);

  // File & Upload State
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadId, setUploadId] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);

  // Analysis State
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState(null);
  const [result, setResult] = useState(null);

  // View Options
  const [showBoundingBoxes, setShowBoundingBoxes] = useState(true);
  const [showRawText, setShowRawText] = useState(false);
  const [useGpu, setUseGpu] = useState(true);
  const [applyClahe, setApplyClahe] = useState(true);
  const [applyDeskew, setApplyDeskew] = useState(true);

  // Save/Notification
  const [saveStatus, setSaveStatus] = useState(null);
  const fileInputRef = useRef(null);

  // Fetch initial health check
  useEffect(() => {
    async function loadHealth() {
      try {
        const data = await apiService.checkHealth();
        setHealth(data);
        setHealthError(null);
      } catch (err) {
        setHealthError('Backend server is unreachable. Please verify backend is running on port 8000.');
      }
    }
    loadHealth();
  }, []);

  // Handle File Selection
  const handleFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await processFileUpload(file);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    await processFileUpload(file);
  };

  const processFileUpload = async (file) => {
    const validExtensions = ['.jpg', '.jpeg', '.png', '.pdf'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(ext)) {
      setUploadError(`Invalid file format '${ext}'. Please upload JPG, PNG, or PDF.`);
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setUploadError('File size exceeds the 15 MB limit.');
      return;
    }

    if (file.size === 0) {
      setUploadError('Selected file is empty (0 bytes).');
      return;
    }

    setUploadError(null);
    setSelectedFile(file);
    setResult(null);
    setIsUploading(true);

    try {
      const resp = await apiService.uploadPrescription(file);
      setUploadId(resp.id);
      setPreviewUrl(apiService.getImageUrl(resp.id));
      setIsUploading(false);
    } catch (err) {
      setIsUploading(false);
      setUploadError(err.response?.data?.detail || err.message || 'Failed to upload prescription');
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setUploadId(null);
    setPreviewUrl(null);
    setResult(null);
    setUploadError(null);
    setAnalyzeError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Run AI Analysis
  const handleAnalyze = async () => {
    if (!uploadId) return;
    setIsAnalyzing(true);
    setAnalyzeError(null);

    try {
      const resp = await apiService.analyzePrescription(uploadId, {
        use_gpu: useGpu,
        apply_clahe: applyClahe,
        apply_deskew: applyDeskew,
      });
      setResult(resp);
      setIsAnalyzing(false);
    } catch (err) {
      setIsAnalyzing(false);
      setAnalyzeError(err.response?.data?.detail || err.message || 'Prescription analysis failed');
    }
  };

  // Medicine Field Edits
  const handleMedicineChange = (index, field, value) => {
    if (!result) return;
    const updated = [...result.medicines];
    updated[index] = {
      ...updated[index],
      [field]: value,
      is_unclear: field === 'medicine_name' && value === UNCLEAR_MARKER,
    };
    const newResult = { ...result, medicines: updated };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  const handleAddMedicine = () => {
    if (!result) return;
    const newMed = {
      medicine_name: '',
      strength: NOT_DETECTED,
      dosage: NOT_DETECTED,
      frequency: NOT_DETECTED,
      duration: NOT_DETECTED,
      route: 'Oral (Tablet)',
      food_instructions: NOT_DETECTED,
      special_instructions: NOT_DETECTED,
      confidence: 100.0,
      is_unclear: false,
    };
    const newResult = {
      ...result,
      medicines: [...result.medicines, newMed],
    };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  const handleDeleteMedicine = (index) => {
    if (!result) return;
    const updated = result.medicines.filter((_, i) => i !== index);
    const newResult = { ...result, medicines: updated };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  // Patient & Doctor Field Edits
  const handleDoctorChange = (field, value) => {
    if (!result) return;
    const newResult = {
      ...result,
      doctor: { ...result.doctor, [field]: value },
    };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  const handlePatientChange = (field, value) => {
    if (!result) return;
    const newResult = {
      ...result,
      patient: { ...result.patient, [field]: value },
    };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  const handleClinicalChange = (field, value) => {
    if (!result) return;
    const newResult = {
      ...result,
      [field]: value,
    };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  // Toggle Verification State
  const handleToggleVerified = () => {
    if (!result) return;
    const nextState = !result.is_verified;
    const newResult = { ...result, is_verified: nextState };
    setResult(newResult);
    syncResultToBackend(newResult);
  };

  // Sync edits to backend
  const syncResultToBackend = async (dataToSync) => {
    if (!dataToSync?.id) return;
    try {
      await apiService.updateResult(dataToSync.id, {
        clinic_header: dataToSync.clinic_header,
        doctor: dataToSync.doctor,
        patient: dataToSync.patient,
        diagnosis: dataToSync.diagnosis,
        advice: dataToSync.advice,
        follow_up: dataToSync.follow_up,
        medicines: dataToSync.medicines,
        raw_text: dataToSync.raw_text,
        is_verified: dataToSync.is_verified,
        notes: dataToSync.notes,
      });
      setSaveStatus('Changes saved');
      setTimeout(() => setSaveStatus(null), 2500);
    } catch (err) {
      console.error('Failed to sync changes:', err);
    }
  };

  // Export handlers
  const handleExport = async (format) => {
    if (!result?.id) return;
    try {
      await apiService.downloadExport(
        result.id,
        format,
        `prescription_${result.id.slice(0, 8)}`
      );
    } catch (err) {
      alert(`Export failed: ${err.message}`);
    }
  };

  return (
    <div className="app-container">
      {/* Top Navbar */}
      <header className="navbar">
        <div className="nav-brand">
          <FileText className="brand-icon" />
          <span className="brand-title">AI Prescription Reader</span>
          <span className="badge-modular">Full-Page Clinical OCR & Data Extraction</span>
        </div>

        <div className="nav-status">
          {health ? (
            <div className="hardware-pill">
              <Cpu className="pill-icon" />
              <span>{health.gpu_name ? `${health.gpu_name} (CUDA)` : 'CPU Mode'}</span>
            </div>
          ) : healthError ? (
            <div className="hardware-pill error">
              <AlertCircle className="pill-icon" />
              <span>Backend Offline</span>
            </div>
          ) : (
            <div className="hardware-pill">
              <RefreshCw className="pill-icon spin" />
              <span>Connecting...</span>
            </div>
          )}
        </div>
      </header>

      {/* Main Grid Layout */}
      <main className="main-content">
        {/* Left Column: Upload & Prescription Viewer */}
        <section className="column viewer-col">
          <div className="card viewer-card">
            <div className="card-header">
              <h2 className="card-title">Prescription Scan</h2>
              {previewUrl && (
                <div className="view-controls">
                  <button
                    type="button"
                    className={`btn-toggle ${showBoundingBoxes ? 'active' : ''}`}
                    onClick={() => setShowBoundingBoxes(!showBoundingBoxes)}
                    title="Toggle OCR Bounding Boxes"
                  >
                    {showBoundingBoxes ? <Eye className="icon-sm" /> : <EyeOff className="icon-sm" />}
                    <span>Boxes</span>
                  </button>
                  <button
                    type="button"
                    className="btn-text danger"
                    onClick={handleRemoveFile}
                    title="Remove File"
                  >
                    <X className="icon-sm" />
                    <span>Replace</span>
                  </button>
                </div>
              )}
            </div>

            {/* Upload Zone */}
            {!previewUrl ? (
              <div
                className="dropzone"
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  style={{ display: 'none' }}
                  accept=".jpg,.jpeg,.png,.pdf"
                  onChange={handleFileChange}
                />
                <div className="dropzone-inner">
                  <div className="dropzone-icon-wrap">
                    <Upload className="dropzone-icon" />
                  </div>
                  <h3>Select or Drop Prescription</h3>
                  <p className="dropzone-hint">
                    Supports printed & handwritten JPG, PNG, and scanned PDF prescriptions (up to 15 MB)
                  </p>
                  <span className="btn-select">Browse Files</span>
                </div>
              </div>
            ) : (
              /* Image & Bounding Box Viewer */
              <div className="image-viewport-wrapper">
                <div className="image-viewport">
                  <img
                    src={previewUrl}
                    alt="Prescription Scan"
                    className="prescription-img"
                  />
                  {showBoundingBoxes && result?.bounding_boxes && (
                    <div className="bounding-boxes-layer">
                      {result.bounding_boxes.map((box, idx) => {
                        const imgElem = document.querySelector('.prescription-img');
                        const naturalW = result.quality?.width || 1800;
                        const naturalH = result.quality?.height || 2400;
                        const currentW = imgElem ? imgElem.clientWidth : 600;
                        const currentH = imgElem ? imgElem.clientHeight : 800;
                        const scaleX = currentW / naturalW;
                        const scaleY = currentH / naturalH;

                        return (
                          <div
                            key={idx}
                            className="ocr-box"
                            style={{
                              left: `${box.x * scaleX}px`,
                              top: `${box.y * scaleY}px`,
                              width: `${box.width * scaleX}px`,
                              height: `${box.height * scaleY}px`,
                            }}
                            title={`${box.text} (${box.confidence}%)`}
                          >
                            <span className="box-tooltip">{box.text}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {uploadError && (
              <div className="alert-banner error">
                <AlertCircle className="alert-icon" />
                <span>{uploadError}</span>
              </div>
            )}

            {previewUrl && (
              <div className="action-bar">
                <div className="ocr-options">
                  <label className="checkbox-label" title="CLAHE contrast enhancement for faint handwriting">
                    <input
                      type="checkbox"
                      checked={applyClahe}
                      onChange={(e) => setApplyClahe(e.target.checked)}
                    />
                    <span>CLAHE Contrast</span>
                  </label>
                  <label className="checkbox-label" title="Deskew rotation correction">
                    <input
                      type="checkbox"
                      checked={applyDeskew}
                      onChange={(e) => setApplyDeskew(e.target.checked)}
                    />
                    <span>Deskew</span>
                  </label>
                </div>

                <button
                  type="button"
                  className="btn-primary"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                >
                  {isAnalyzing ? (
                    <>
                      <RefreshCw className="icon-sm spin" />
                      <span>Analyzing OCR...</span>
                    </>
                  ) : (
                    <>
                      <RefreshCw className="icon-sm" />
                      <span>{result ? 'Reprocess Prescription' : 'Analyze Entire Prescription'}</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </section>

        {/* Right Column: Full-Page Extracted Details */}
        <section className="column details-col">
          {analyzeError && (
            <div className="alert-banner error">
              <AlertCircle className="alert-icon" />
              <span>{analyzeError}</span>
            </div>
          )}

          {/* Verification Status Banner */}
          {result && (
            <div className={`verification-banner ${result.is_verified ? 'verified' : 'unverified'}`}>
              <div className="banner-left">
                {result.is_verified ? (
                  <>
                    <ShieldCheck className="banner-icon text-success" />
                    <div>
                      <h4 className="banner-title text-success">Prescription Clinically Verified</h4>
                      <p className="banner-desc">All medicines, dosages, and patient details confirmed by human reviewer.</p>
                    </div>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="banner-icon text-warning" />
                    <div>
                      <h4 className="banner-title text-warning">Unverified Extraction &mdash; Human Review Required</h4>
                      <p className="banner-desc">Verify all extracted handwriting fields below before clinical export or dispensing.</p>
                    </div>
                  </>
                )}
              </div>

              <div className="banner-actions">
                <button
                  type="button"
                  className={`btn-action-verify ${result.is_verified ? 'btn-unverify' : 'btn-verify'}`}
                  onClick={handleToggleVerified}
                >
                  {result.is_verified ? (
                    <>
                      <RotateCcw className="icon-sm" />
                      <span>Mark Unverified</span>
                    </>
                  ) : (
                    <>
                      <Check className="icon-sm" />
                      <span>Mark as Verified</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Hospital / Clinic Header */}
          {result && (
            <div className="card sub-card clinic-header-card">
              <div className="form-group-full">
                <label className="section-label">
                  <Building className="icon-xs inline-icon" /> Clinic / Hospital Institution Header
                </label>
                <input
                  type="text"
                  className="input-prominent"
                  value={result.clinic_header || NOT_DETECTED}
                  placeholder="e.g. City Care Clinic"
                  onChange={(e) => handleClinicalChange('clinic_header', e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Doctor & Patient Metadata Grid */}
          {result && (
            <div className="meta-grid">
              {/* Doctor Card */}
              <div className="card sub-card">
                <h3 className="card-subtitle">
                  <Stethoscope className="icon-xs inline-icon" /> Doctor Details
                </h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Doctor Name</label>
                    <input
                      type="text"
                      value={result.doctor?.name || NOT_DETECTED}
                      placeholder="e.g. Dr. S. Kumar"
                      onChange={(e) => handleDoctorChange('name', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Qualification</label>
                    <input
                      type="text"
                      value={result.doctor?.qualification || NOT_DETECTED}
                      placeholder="e.g. MBBS, MD"
                      onChange={(e) => handleDoctorChange('qualification', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Specialization</label>
                    <input
                      type="text"
                      value={result.doctor?.specialization || NOT_DETECTED}
                      placeholder="e.g. Consultant Physician"
                      onChange={(e) => handleDoctorChange('specialization', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Medical Reg. / Lic. #</label>
                    <input
                      type="text"
                      value={result.doctor?.registration_number || NOT_DETECTED}
                      placeholder="e.g. 123456"
                      onChange={(e) => handleDoctorChange('registration_number', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Clinic / Hospital</label>
                    <input
                      type="text"
                      value={result.doctor?.clinic_or_hospital || NOT_DETECTED}
                      placeholder="e.g. City Care Clinic"
                      onChange={(e) => handleDoctorChange('clinic_or_hospital', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Contact Number</label>
                    <input
                      type="text"
                      value={result.doctor?.contact_number || NOT_DETECTED}
                      placeholder="e.g. 080-12345678"
                      onChange={(e) => handleDoctorChange('contact_number', e.target.value)}
                    />
                  </div>
                </div>
              </div>

              {/* Patient Card */}
              <div className="card sub-card">
                <h3 className="card-subtitle">
                  <User className="icon-xs inline-icon" /> Patient Details
                </h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label>Patient Name</label>
                    <input
                      type="text"
                      value={result.patient?.name || NOT_DETECTED}
                      placeholder="e.g. Ramesh K"
                      onChange={(e) => handlePatientChange('name', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Prescription Date</label>
                    <input
                      type="text"
                      value={result.patient?.date || NOT_DETECTED}
                      placeholder="DD/MM/YYYY"
                      onChange={(e) => handlePatientChange('date', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Age</label>
                    <input
                      type="text"
                      value={result.patient?.age || NOT_DETECTED}
                      placeholder="e.g. 42 yrs"
                      onChange={(e) => handlePatientChange('age', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Gender</label>
                    <input
                      type="text"
                      value={result.patient?.gender || NOT_DETECTED}
                      placeholder="Male / Female"
                      onChange={(e) => handlePatientChange('gender', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Patient Address</label>
                    <input
                      type="text"
                      value={result.patient?.address || NOT_DETECTED}
                      placeholder="e.g. Bengaluru"
                      onChange={(e) => handlePatientChange('address', e.target.value)}
                    />
                  </div>
                  <div className="form-group">
                    <label>Patient ID / UHID</label>
                    <input
                      type="text"
                      value={result.patient?.patient_id || NOT_DETECTED}
                      placeholder="e.g. PID-9842"
                      onChange={(e) => handlePatientChange('patient_id', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Clinical Findings Card (Diagnosis, Advice, Follow-up) */}
          {result && (
            <div className="card sub-card">
              <h3 className="card-subtitle">
                <Activity className="icon-xs inline-icon" /> Clinical Diagnosis & Medical Advice
              </h3>
              <div className="form-grid-3">
                <div className="form-group">
                  <label>Clinical Diagnosis</label>
                  <input
                    type="text"
                    value={result.diagnosis || NOT_DETECTED}
                    placeholder="e.g. URTI, Fever"
                    onChange={(e) => handleClinicalChange('diagnosis', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Medical Advice</label>
                  <input
                    type="text"
                    value={result.advice || NOT_DETECTED}
                    placeholder="e.g. Take plenty of fluids, Rest"
                    onChange={(e) => handleClinicalChange('advice', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label>Follow-up Instructions</label>
                  <input
                    type="text"
                    value={result.follow_up || NOT_DETECTED}
                    placeholder="e.g. After 04/11/2025"
                    onChange={(e) => handleClinicalChange('follow_up', e.target.value)}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Prescribed Medications Card */}
          <div className="card">
            <div className="card-header">
              <div>
                <h2 className="card-title">
                  <ClipboardList className="icon-xs inline-icon" /> Prescribed Medications
                </h2>
                <p className="card-caption">
                  {result
                    ? `${result.medicines.length} medication(s) extracted. Click any field to edit or correct values.`
                    : 'Upload and analyze a prescription to inspect extracted medications.'}
                </p>
              </div>

              {result && (
                <div className="table-header-actions">
                  {saveStatus && <span className="save-indicator">{saveStatus}</span>}
                  <button type="button" className="btn-secondary" onClick={handleAddMedicine}>
                    <Plus className="icon-sm" />
                    <span>Add Medicine Row</span>
                  </button>
                </div>
              )}
            </div>

            {/* Medicines List / Table */}
            {result ? (
              result.medicines.length > 0 ? (
                <div className="table-responsive">
                  <table className="med-table">
                    <thead>
                      <tr>
                        <th style={{ width: '35px' }}>#</th>
                        <th>Medicine Name</th>
                        <th>Strength</th>
                        <th>Dosage</th>
                        <th>Frequency</th>
                        <th>Duration</th>
                        <th>Route</th>
                        <th>Food Timing</th>
                        <th>Special Instructions</th>
                        <th style={{ width: '40px' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.medicines.map((med, idx) => {
                        const isUnclear = med.is_unclear || med.medicine_name === UNCLEAR_MARKER;
                        return (
                          <tr key={idx} className={isUnclear ? 'row-unclear' : ''}>
                            <td className="cell-idx">{idx + 1}</td>
                            <td>
                              <div className="cell-input-wrap">
                                <input
                                  type="text"
                                  className={`table-input ${isUnclear ? 'input-unclear' : ''}`}
                                  value={med.medicine_name}
                                  placeholder="Medicine name"
                                  onChange={(e) =>
                                    handleMedicineChange(idx, 'medicine_name', e.target.value)
                                  }
                                />
                                {isUnclear && (
                                  <span className="unclear-badge" title="Manual verification required">
                                    <AlertTriangle className="icon-xs" />
                                    Unclear
                                  </span>
                                )}
                              </div>
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.strength}
                                placeholder="Not detected"
                                onChange={(e) => handleMedicineChange(idx, 'strength', e.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.dosage}
                                placeholder="Not detected"
                                onChange={(e) => handleMedicineChange(idx, 'dosage', e.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.frequency}
                                placeholder="Not detected"
                                onChange={(e) => handleMedicineChange(idx, 'frequency', e.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.duration}
                                placeholder="Not detected"
                                onChange={(e) => handleMedicineChange(idx, 'duration', e.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.route}
                                placeholder="Not detected"
                                onChange={(e) => handleMedicineChange(idx, 'route', e.target.value)}
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.food_instructions}
                                placeholder="Not detected"
                                onChange={(e) =>
                                  handleMedicineChange(idx, 'food_instructions', e.target.value)
                                }
                              />
                            </td>
                            <td>
                              <input
                                type="text"
                                className="table-input"
                                value={med.special_instructions}
                                placeholder="Not detected"
                                onChange={(e) =>
                                  handleMedicineChange(idx, 'special_instructions', e.target.value)
                                }
                              />
                            </td>
                            <td className="cell-actions">
                              <button
                                type="button"
                                className="btn-icon danger"
                                onClick={() => handleDeleteMedicine(idx)}
                                title="Delete row"
                              >
                                <Trash2 className="icon-sm" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">
                  <AlertCircle className="empty-icon" />
                  <p>No distinct medications recognized in this image.</p>
                  <button type="button" className="btn-secondary" onClick={handleAddMedicine}>
                    <Plus className="icon-sm" /> Add Medicine Row Manually
                  </button>
                </div>
              )
            ) : (
              <div className="empty-state">
                <FileText className="empty-icon" />
                <p>Upload a prescription and click <b>Analyze Entire Prescription</b> to extract medications.</p>
              </div>
            )}

            {/* Export and Raw Text Bar */}
            {result && (
              <div className="card-footer">
                <div className="footer-left">
                  <button
                    type="button"
                    className="btn-toggle"
                    onClick={() => setShowRawText(!showRawText)}
                  >
                    <span>{showRawText ? 'Hide Raw OCR Text' : 'View Full OCR Text'}</span>
                  </button>
                </div>

                <div className="footer-right">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => handleExport('csv')}
                  >
                    <Download className="icon-sm" />
                    <span>Export CSV</span>
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => handleExport('pdf')}
                  >
                    <Download className="icon-sm" />
                    <span>Export PDF Report</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Raw OCR Text Accordion */}
          {result && showRawText && (
            <div className="card sub-card">
              <div className="card-header">
                <h3 className="card-subtitle">Full-Page Raw OCR Engine Text</h3>
                <span className="raw-conf">
                  Engine: <b>{result.engine_used}</b>
                </span>
              </div>
              <textarea
                className="raw-textarea"
                rows={12}
                value={result.raw_text}
                onChange={(e) => {
                  const newResult = { ...result, raw_text: e.target.value };
                  setResult(newResult);
                  syncResultToBackend(newResult);
                }}
              />
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
