import React, { useState, useRef } from 'react';
import { FileText, Pill, AlertTriangle, CheckCircle, Sparkles, Send, ShieldAlert, UploadCloud, Image as ImageIcon } from 'lucide-react';
import { analyzePrescription, analyzePrescriptionFile, getSamplePrescription } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function PrescriptionAnalysis() {
  const [prescriptionText, setPrescriptionText] = useState('');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleAnalyze = async () => {
    if (!prescriptionText.trim() && !selectedFile) return;
    setLoading(true);
    setError(null);
    try {
      let data;
      if (selectedFile) {
        data = await analyzePrescriptionFile(selectedFile);
        if (data.raw_text) setPrescriptionText(data.raw_text);
      } else {
        data = await analyzePrescription(prescriptionText);
      }
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message || 'Prescription analysis failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleLoadSample = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSamplePrescription();
      setPrescriptionText(data.raw_text || '');
      setAnalysisResult(data);
    } catch (err) {
      setError(err.message || 'Failed to load sample prescription.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem', paddingBottom: '3rem' }}>
      {/* Header */}
      <div className="glass-panel" style={{
        padding: '2rem',
        borderLeft: '5px solid #6366f1',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={26} color="#818cf8" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#f8fafc' }}>
              Clinical Prescription & Medical Note Analyzer
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Extracts medications, verifies antimicrobial regimens, and highlights contraindications
            </p>
          </div>
        </div>

        <button
          onClick={handleLoadSample}
          disabled={loading}
          className="btn-secondary"
          style={{ padding: '0.55rem 1rem', fontSize: '0.85rem', borderColor: 'rgba(99, 102, 241, 0.4)' }}
        >
          <Sparkles size={16} color="#818cf8" />
          <span>Load Sample Respiratory Rx</span>
        </button>
      </div>

      {/* Input Box */}
      <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Upload Prescription Image File */}
        <div>
          <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.5rem', display: 'block' }}>
            Upload Prescription Image Document (PNG, JPG, JPEG):
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/png,image/jpeg,image/jpg"
              style={{ display: 'none' }}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
              style={{ padding: '0.6rem 1.2rem', borderColor: 'rgba(99, 102, 241, 0.4)' }}
            >
              <UploadCloud size={16} color="#818cf8" />
              <span>{selectedFile ? 'Change Prescription File' : 'Browse Prescription File'}</span>
            </button>
            {selectedFile && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(99, 102, 241, 0.1)', padding: '0.4rem 0.8rem', borderRadius: '8px' }}>
                <ImageIcon size={16} color="#818cf8" />
                <span style={{ fontSize: '0.85rem', color: '#c7d2fe' }}>{selectedFile.name}</span>
                <button onClick={clearFile} style={{ background: 'none', border: 'none', color: '#f87171', cursor: 'pointer', fontSize: '0.8rem' }}>Remove</button>
              </div>
            )}
          </div>
          {previewUrl && (
            <div style={{ marginTop: '0.75rem', maxHeight: '180px', overflow: 'hidden', borderRadius: '8px', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <img src={previewUrl} alt="Prescription Preview" style={{ maxHeight: '180px', objectFit: 'contain' }} />
            </div>
          )}
        </div>

        <div>
          <label style={{ fontSize: '0.9rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.5rem', display: 'block' }}>
            Or Input Clinical Notes / Electronic Prescription Text:
          </label>
          <textarea
            rows={4}
            value={prescriptionText}
            onChange={(e) => setPrescriptionText(e.target.value)}
            placeholder="Paste doctor prescription text, clinical assessment, or drug orders here..."
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.7)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              color: '#f8fafc',
              padding: '1rem',
              fontSize: '0.9rem',
              lineHeight: 1.5,
              resize: 'vertical',
              fontFamily: 'Inter, sans-serif'
            }}
          />
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button
            onClick={handleAnalyze}
            disabled={loading || (!prescriptionText.trim() && !selectedFile)}
            className="btn-primary"
            style={{ padding: '0.65rem 1.4rem' }}
          >
            <Send size={16} />
            <span>{loading ? 'Analyzing Entities...' : (selectedFile ? 'Extract & Analyze Image' : 'Analyze Prescription')}</span>
          </button>
        </div>
      </div>

      {loading && (
        <div className="glass-panel">
          <LoadingSpinner message="Extracting pharmacological entities & cross-referencing contraindications..." />
        </div>
      )}

      {/* Analysis Output */}
      {analysisResult && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Summary Banner */}
          <div className="glass-card" style={{ borderLeft: '4px solid #38bdf8' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#38bdf8', marginBottom: '0.25rem' }}>
              Entity Extraction Summary
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#e2e8f0' }}>{analysisResult.summary}</p>
          </div>

          {/* Medications Identified */}
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '1rem', color: '#f8fafc' }}>
              Identified Medications & Posology ({analysisResult.detected_medications?.length || 0})
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
              {analysisResult.detected_medications?.map((med, idx) => (
                <div key={idx} className="glass-panel" style={{ padding: '1.25rem', borderLeft: '4px solid #818cf8' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <Pill size={18} color="#818cf8" />
                      <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>{med.name}</span>
                    </div>
                    <span className="badge badge-cyan">{med.dosage}</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
                    <strong>Class:</strong> {med.class}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.4rem' }}>
                    <strong>Indication:</strong> {med.indicated_for}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#34d399', fontWeight: 600 }}>
                    <strong>Frequency:</strong> {med.frequency}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Clinical Warnings if any */}
          {analysisResult.clinical_warnings?.length > 0 && (
            <div className="glass-panel" style={{ padding: '1.25rem', borderLeft: '4px solid #ef4444', background: 'rgba(239, 68, 68, 0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <ShieldAlert size={20} color="#f87171" />
                <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#f87171' }}>
                  Clinical Safety Warnings & Contraindications
                </h3>
              </div>
              <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5 }}>
                {analysisResult.clinical_warnings.map((warn, i) => (
                  <li key={i}>{warn}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Doctor Recommendations */}
          <div className="glass-panel" style={{ padding: '1.25rem', borderLeft: '4px solid #10b981' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
              <CheckCircle size={20} color="#34d399" />
              <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#34d399' }}>
                Clinical Guidance & Recommendations
              </h3>
            </div>
            <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5 }}>
              {analysisResult.doctor_guidance?.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
