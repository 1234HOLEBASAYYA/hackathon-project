import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  AlertCircle,
  Download,
  RotateCcw,
  Sparkles,
  CheckCircle2,
  Eye,
  Stethoscope,
  Info,
  ShieldAlert,
  Loader2,
  X,
  FileCheck,
  MapPin,
  AlertOctagon
} from 'lucide-react';
import { analyzeCTScan, generatePDFReport, getReportDownloadUrl, getSampleCTScan } from '../services/api';

export default function CTScanAnalysis() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progressStage, setProgressStage] = useState(1);
  const [progressText, setProgressText] = useState('Initializing scan verification...');
  const [errorMessage, setErrorMessage] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [isGeneratingPdf, setIsGeneratingPdf] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const fileInputRef = useRef(null);

  const handleFileChange = (file) => {
    if (!file) return;

    if (!file.type.startsWith('image/') && !file.name.match(/\.(png|jpe?g|webp)$/i)) {
      setErrorMessage('Unsupported format. Please upload a valid PNG, JPG, or JPEG image of your CT scan or radiograph.');
      return;
    }

    if (file.name.match(/(prescri|priscrition|rx_|prescription|doctor_note)/i)) {
      setErrorMessage("Incompatible image selected: This appears to be a prescription document ('" + file.name + "'). The CT Analysis module is strictly for CT scans. Please use the 'Prescription & Rx' tab to analyze prescription documents.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('File size exceeds 15 MB limit. Please select a smaller or compressed slice.');
      return;
    }

    setErrorMessage(null);
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setReportData(null);
    setErrorMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleLoadSample = async () => {
    try {
      setErrorMessage(null);
      const blob = await getSampleCTScan();
      const sampleFile = new File([blob], 'demo_chest_ct_scan.jpeg', { type: 'image/jpeg' });
      handleFileChange(sampleFile);
    } catch (err) {
      setErrorMessage(err.message || 'Could not load sample scan from server.');
    }
  };

  const runAnalysis = async () => {
    if (!selectedFile) return;

    setIsAnalyzing(true);
    setErrorMessage(null);
    setReportData(null);
    setProgressStage(1);
    setProgressText('Validating image dimensions & density values...');

    const stageTimer1 = setTimeout(() => {
      setProgressStage(2);
      setProgressText('Querying Gemini Clinical Vision API with objective radiological prompt...');
    }, 1200);

    const stageTimer2 = setTimeout(() => {
      setProgressStage(3);
      setProgressText('Validating structured radiological schema & uncertainty guidelines...');
    }, 2800);

    try {
      const data = await analyzeCTScan(selectedFile);
      setReportData(data);
    } catch (err) {
      console.error('CT Analysis Error:', err);
      setErrorMessage(err.message || 'Analysis could not be completed. Please check your backend and retry.');
    } finally {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      setIsAnalyzing(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!reportData) return;

    try {
      setIsGeneratingPdf(true);
      const serverImageId = reportData.image_preprocessing?.server_image_id;
      const res = await generatePDFReport(reportData, serverImageId);
      
      // Trigger download
      const downloadUrl = getReportDownloadUrl(res.filename);
      window.open(downloadUrl, '_blank');
    } catch (err) {
      alert(`PDF Generation failed: ${err.message}`);
    } finally {
      setIsGeneratingPdf(false);
    }
  };

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.75rem', paddingBottom: '3rem' }}>
      
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%)',
        border: '1px solid rgba(56, 189, 248, 0.3)',
        borderRadius: '16px',
        padding: '1.5rem 2rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '1.45rem', fontWeight: 800, color: '#f8fafc' }}>
              MedVision-AI <span style={{ color: '#38bdf8' }}>— CT Image Analyzer</span>
            </span>
            <span className="badge badge-cyan">GEMINI 3.8 FLASH</span>
          </div>
          <p style={{ fontSize: '0.875rem', color: '#94a3b8' }}>
            AI-Assisted Visual Analysis, Objective Anatomic Grounding & Structured Radiological Reporting
          </p>
        </div>

        <button onClick={handleLoadSample} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
          <Sparkles size={16} color="#38bdf8" />
          <span>Load Sample Scan</span>
        </button>
      </div>

      {/* Clinical Warning Bar */}
      <div style={{
        background: 'rgba(245, 158, 11, 0.08)',
        border: '1px solid rgba(245, 158, 11, 0.3)',
        borderRadius: '12px',
        padding: '0.85rem 1.25rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        fontSize: '0.825rem',
        color: '#fde68a'
      }}>
        <ShieldAlert size={20} style={{ flexShrink: 0, color: '#fbbf24' }} />
        <span>
          <strong>CLINICAL DECISION SUPPORT NOTICE:</strong> Uploaded images are evaluated as static 2D image files.
          Visual observations do not constitute a confirmed clinical diagnosis. All findings strictly require correlation with full volumetric series and review by a board-certified radiologist.
        </span>
      </div>

      {/* Main Grid: Upload on Left (380px), Workspace on Right */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(320px, 380px) 1fr',
        gap: '1.75rem'
      }}>
        
        {/* LEFT COLUMN: Upload Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <UploadCloud size={20} color="#38bdf8" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                  Upload CT Image Slice
                </h3>
              </div>
              {selectedFile && (
                <button
                  onClick={handleClear}
                  style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.8rem' }}
                >
                  <X size={14} /> Clear
                </button>
              )}
            </div>

            {/* Dropzone */}
            {!previewUrl ? (
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setIsDragOver(false);
                  if (e.dataTransfer.files?.[0]) handleFileChange(e.dataTransfer.files[0]);
                }}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  border: `2px dashed ${isDragOver ? '#38bdf8' : 'rgba(56, 189, 248, 0.3)'}`,
                  borderRadius: '12px',
                  padding: '2.5rem 1.5rem',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: isDragOver ? 'rgba(56, 189, 248, 0.1)' : 'rgba(15, 23, 42, 0.45)',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.75rem'
                }}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png, image/jpeg, image/jpg, image/webp"
                  onChange={(e) => handleFileChange(e.target.files?.[0])}
                  style={{ display: 'none' }}
                />
                <div style={{
                  width: '56px',
                  height: '56px',
                  borderRadius: '50%',
                  background: 'rgba(56, 189, 248, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid rgba(56, 189, 248, 0.25)',
                  color: '#38bdf8'
                }}>
                  <UploadCloud size={28} />
                </div>
                <div>
                  <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.25rem' }}>
                    Drag & drop CT image slice here
                  </p>
                  <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
                    PNG, JPG, JPEG • Max 15 MB
                  </p>
                </div>
                <button type="button" className="btn-secondary" style={{ fontSize: '0.8rem', padding: '0.45rem 1rem' }}>
                  Browse Local File
                </button>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{
                  position: 'relative',
                  borderRadius: '10px',
                  overflow: 'hidden',
                  background: '#000',
                  maxHeight: '300px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: '1px solid var(--border-color)'
                }}>
                  <img
                    src={previewUrl}
                    alt="CT Scan Preview"
                    style={{ maxHeight: '300px', width: 'auto', objectFit: 'contain' }}
                  />
                  <div style={{
                    position: 'absolute',
                    bottom: '8px',
                    left: '8px',
                    background: 'rgba(0,0,0,0.75)',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                    color: '#38bdf8',
                    fontFamily: 'monospace'
                  }}>
                    {selectedFile?.name}
                  </div>
                </div>

                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.65rem 0.85rem',
                  borderRadius: '8px',
                  background: 'rgba(30, 41, 59, 0.5)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.8rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: '#38bdf8' }}>
                    <FileCheck size={16} />
                    <span style={{ color: '#f8fafc', fontWeight: 600 }}>{(selectedFile.size / 1024).toFixed(1)} KB</span>
                  </div>
                  <button onClick={handleClear} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.75rem' }}>
                    Change Image
                  </button>
                </div>

                <button
                  onClick={runAnalysis}
                  disabled={isAnalyzing}
                  className="btn-primary"
                  style={{ width: '100%', padding: '0.85rem' }}
                >
                  <Sparkles size={18} />
                  <span>{isAnalyzing ? 'Analyzing Image...' : 'Run Visual Analysis'}</span>
                </button>
              </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '1rem', fontSize: '0.725rem', color: '#64748b' }}>
              <Info size={14} />
              <span>Modality identification is visual and non-definitive from a single image.</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Results Workspace */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Error Banner */}
          {errorMessage && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.12)',
              border: '1px solid rgba(239, 68, 68, 0.35)',
              borderRadius: '12px',
              padding: '1rem 1.25rem',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '0.75rem',
              color: '#f87171'
            }}>
              <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
              <div style={{ flex: 1 }}>
                <strong style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.2rem' }}>Analysis Interrupted</strong>
                <p style={{ fontSize: '0.825rem', color: '#fca5a5' }}>{errorMessage}</p>
                <button
                  onClick={runAnalysis}
                  className="btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '0.35rem 0.75rem', marginTop: '0.65rem' }}
                >
                  <RotateCcw size={14} /> Retry Analysis
                </button>
              </div>
            </div>
          )}

          {/* Loading State */}
          {isAnalyzing && (
            <div className="glass-panel" style={{ padding: '3rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '16px',
                background: 'rgba(56, 189, 248, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
                marginBottom: '1.25rem'
              }}>
                <Loader2 size={36} className="spin" />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.35rem' }}>
                Analyzing CT Scan with Gemini Clinical Vision
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.75rem' }}>
                {progressText}
              </p>

              {/* Progress Steps Checklist */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', textAlign: 'left', fontSize: '0.825rem', maxWidth: '380px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: progressStage >= 1 ? '#38bdf8' : '#64748b' }}>
                  {progressStage > 1 ? <CheckCircle2 size={16} color="#34d399" /> : <Loader2 size={16} className="spin" />}
                  <span>Image preprocessing & dimension verification</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: progressStage >= 2 ? '#38bdf8' : '#64748b' }}>
                  {progressStage > 2 ? <CheckCircle2 size={16} color="#34d399" /> : progressStage === 2 ? <Loader2 size={16} className="spin" /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #475569' }} />}
                  <span>Gemini zero-hallucination feature extraction</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: progressStage >= 3 ? '#38bdf8' : '#64748b' }}>
                  {progressStage === 3 ? <Loader2 size={16} className="spin" /> : <div style={{ width: 16, height: 16, borderRadius: '50%', border: '1px solid #475569' }} />}
                  <span>Radiological schema & uncertainty validation</span>
                </div>
              </div>
            </div>
          )}

          {/* Empty State */}
          {!isAnalyzing && !reportData && !errorMessage && (
            <div className="glass-panel" style={{ padding: '4rem 2rem', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                background: 'rgba(56, 189, 248, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#38bdf8',
                marginBottom: '1rem',
                border: '1px solid rgba(56, 189, 248, 0.2)'
              }}>
                <FileText size={28} />
              </div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc', marginBottom: '0.4rem' }}>
                No Image Selected
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', maxWidth: '420px', marginBottom: '1.5rem' }}>
                Upload an axial CT slice, scout view, or radiograph on the left to generate an objective, structured decision-support report.
              </p>
            </div>
          )}

          {/* Structured Report Display */}
          {!isAnalyzing && reportData && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              
              {/* Report Header Bar */}
              <div className="glass-panel" style={{
                padding: '1.25rem 1.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                flexWrap: 'wrap',
                gap: '1rem',
                borderLeft: '4px solid #0284c7'
              }}>
                <div>
                  <div style={{ fontSize: '0.65rem', fontFamily: 'monospace', color: '#38bdf8', letterSpacing: '0.08em', fontWeight: 700 }}>
                    STRUCTURED RADIOLOGICAL REPORT
                  </div>
                  <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#f8fafc', margin: '0.15rem 0 0.35rem 0' }}>
                    {reportData.report_title || 'AI-Assisted CT Image Analysis Report'}
                  </h2>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                    <span>{reportData.filename || 'CT_Scan.jpg'}</span>
                    <span>•</span>
                    <span>{reportData.generated_at}</span>
                    <span className="badge badge-cyan">{reportData.model_used || 'Gemini 3.8 Flash'}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
                  <button
                    onClick={handleDownloadPDF}
                    disabled={isGeneratingPdf}
                    className="btn-primary"
                    style={{ fontSize: '0.85rem', padding: '0.6rem 1.15rem' }}
                  >
                    <Download size={16} />
                    <span>{isGeneratingPdf ? 'Generating PDF...' : 'Download PDF Report'}</span>
                  </button>
                  <button onClick={handleClear} className="btn-secondary" style={{ fontSize: '0.85rem' }}>
                    <span>Analyze Another</span>
                  </button>
                </div>
              </div>

              {/* Section 1: Image Information */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <Info size={18} color="#38bdf8" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    1. Image Characteristics & Modality
                  </h3>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
                  <div className="glass-card">
                    <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '0.2rem' }}>Observed Modality</span>
                    <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{reportData.image_information?.image_type}</strong>
                  </div>
                  <div className="glass-card">
                    <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '0.2rem' }}>Dimensions</span>
                    <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{reportData.image_preprocessing?.original_dimensions?.formatted || reportData.image_information?.image_dimensions}</strong>
                  </div>
                  <div className="glass-card">
                    <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', display: 'block', marginBottom: '0.2rem' }}>Image Quality</span>
                    <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{reportData.image_information?.image_quality}</strong>
                  </div>
                </div>

                {reportData.image_information?.limitations?.length > 0 && (
                  <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                    {reportData.image_information.limitations.map((lim, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.75rem', color: '#fbbf24' }}>
                        <AlertCircle size={13} />
                        <span>{lim}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Section 2: Visual Observations */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                  <Eye size={18} color="#a78bfa" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    2. Visible Visual Observations (Physical Densities)
                  </h3>
                </div>
                <p style={{ fontSize: '0.785rem', color: '#64748b', marginBottom: '1rem' }}>
                  Objective physical features, margins, and densities visibly apparent in this static slice.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  {reportData.visual_observations?.map((obs, idx) => (
                    <div key={idx} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{obs.observation}</strong>
                        <span className="badge badge-cyan" style={{ fontSize: '0.68rem' }}>VISUALLY OBSERVED</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', color: '#a78bfa' }}>
                        <MapPin size={13} />
                        <span>Location: {obs.location}</span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.45 }}>{obs.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 3: Potential Findings */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                  <Stethoscope size={18} color="#fbbf24" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    3. Potential Clinical Considerations (Differential / Uncertain)
                  </h3>
                </div>
                <p style={{ fontSize: '0.785rem', color: '#64748b', marginBottom: '1rem' }}>
                  Non-definitive differentials requiring clinical history, laboratory metrics, and radiologist review.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                  {reportData.potential_findings?.map((f, idx) => (
                    <div key={idx} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <strong style={{ fontSize: '0.95rem', color: '#f8fafc' }}>{f.finding}</strong>
                        <span className="badge badge-warning" style={{ fontSize: '0.68rem' }}>UNCERTAIN / DIFFERENTIAL</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.78rem', color: '#a78bfa' }}>
                        <MapPin size={13} />
                        <span>Location: {f.location}</span>
                      </div>
                      <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.45 }}>{f.description}</p>
                      <div style={{
                        fontSize: '0.75rem',
                        color: '#64748b',
                        background: 'rgba(15, 23, 42, 0.6)',
                        padding: '0.3rem 0.65rem',
                        borderRadius: '6px',
                        display: 'inline-block'
                      }}>
                        <strong>Visual Basis:</strong> {f.supporting_visual_observation}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 4: Summary */}
              <div className="glass-panel" style={{ padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                  <FileText size={18} color="#34d399" />
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
                    4. Clinical Summary
                  </h3>
                </div>
                <p style={{ fontSize: '0.925rem', color: '#e2e8f0', lineHeight: 1.6 }}>
                  {reportData.summary}
                </p>
              </div>

              {/* Section 5: Recommendations & Limitations */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.75rem' }}>
                    Recommendations for Professional Review
                  </h4>
                  <ul style={{ paddingLeft: '1.1rem', fontSize: '0.825rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {reportData.recommendations_for_review?.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>

                <div className="glass-panel" style={{ padding: '1.25rem' }}>
                  <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fbbf24', marginBottom: '0.75rem' }}>
                    Study & Single-Slice Limitations
                  </h4>
                  <ul style={{ paddingLeft: '1.1rem', fontSize: '0.825rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                    {reportData.limitations?.map((l, i) => (
                      <li key={i}>{l}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Section 6: Medical Disclaimer */}
              <div style={{
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.35rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171', fontWeight: 700, fontSize: '0.85rem' }}>
                  <AlertOctagon size={18} />
                  <span>CRITICAL MEDICAL DISCLAIMER</span>
                </div>
                <p style={{ fontSize: '0.8rem', color: '#fca5a5', lineHeight: 1.5 }}>
                  {reportData.medical_disclaimer}
                </p>
              </div>

            </div>
          )}

        </div>
      </div>
    </div>
  );
}
