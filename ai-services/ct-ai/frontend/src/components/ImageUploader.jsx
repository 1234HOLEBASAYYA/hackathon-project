import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, Sparkles, CheckCircle2 } from 'lucide-react';

export default function ImageUploader({ onAnalyze, isAnalyzing, selectedFile, setSelectedFile }) {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      alert('Please upload a valid image file (JPEG, PNG, DICOM-derived).');
      return;
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ImageIcon size={20} color="#38bdf8" />
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
            Chest Radiograph Upload
          </h2>
        </div>
        {selectedFile && (
          <button
            onClick={handleClear}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.3rem',
              fontSize: '0.8rem'
            }}
          >
            <X size={14} /> Clear
          </button>
        )}
      </div>

      {!previewUrl ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          style={{
            border: `2px dashed ${dragActive ? '#38bdf8' : 'rgba(56, 189, 248, 0.25)'}`,
            borderRadius: '12px',
            padding: '2.5rem 1.5rem',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragActive ? 'rgba(56, 189, 248, 0.08)' : 'rgba(15, 23, 42, 0.4)',
            transition: 'all 0.2s ease',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '0.85rem'
          }}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png, image/jpeg, image/jpg"
            onChange={(e) => handleFile(e.target.files[0])}
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
            border: '1px solid rgba(56, 189, 248, 0.2)'
          }}>
            <UploadCloud size={28} color="#38bdf8" />
          </div>
          <div>
            <p style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', marginBottom: '0.25rem' }}>
              Drag & drop chest X-ray image here
            </p>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Supports PNG, JPG, JPEG • High-resolution frontal view recommended
            </p>
          </div>
          <button
            type="button"
            className="btn-secondary"
            style={{ fontSize: '0.825rem', padding: '0.45rem 1rem', marginTop: '0.25rem' }}
          >
            Browse Local File
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{
            position: 'relative',
            borderRadius: '10px',
            overflow: 'hidden',
            border: '1px solid var(--border-color)',
            background: '#000000',
            maxHeight: '340px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <img
              src={previewUrl}
              alt="Uploaded Chest Radiograph Preview"
              style={{ maxHeight: '340px', width: 'auto', objectFit: 'contain' }}
            />
            <div style={{
              position: 'absolute',
              bottom: '10px',
              left: '10px',
              background: 'rgba(0, 0, 0, 0.75)',
              padding: '0.25rem 0.6rem',
              borderRadius: '6px',
              fontSize: '0.75rem',
              color: '#38bdf8',
              fontFamily: 'monospace',
              border: '1px solid rgba(56, 189, 248, 0.3)'
            }}>
              {selectedFile?.name || 'Chest Radiograph'}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <button
              onClick={() => onAnalyze(selectedFile)}
              disabled={isAnalyzing}
              className="btn-primary"
              style={{ flex: 1, padding: '0.75rem' }}
            >
              <Sparkles size={18} />
              <span>{isAnalyzing ? 'Analyzing Scan...' : 'Run Abnormality Detection'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
