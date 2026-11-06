import React, { useState, useRef } from 'react';
import { Upload, AlertCircle } from 'lucide-react';
import Card from '../common/Card';

export default function DragDropUpload({
  onFileSelect,
  accept = 'image/*,application/pdf',
  maxSizeBytes = 10485760,
  multiple = false
}) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const validateFile = (file) => {
    if (!file) return false;
    
    // Check type
    const acceptedTypes = accept.split(',').map(t => t.trim());
    const fileType = file.type;
    const fileName = file.name.toLowerCase();
    
    const isValidType = acceptedTypes.some(type => {
      if (type === 'image/*') return fileType.startsWith('image/');
      if (type === 'application/pdf') return fileType === 'application/pdf' || fileName.endsWith('.pdf');
      return false;
    });

    if (!isValidType) {
      setError('Unsupported file format. Please upload an image (PNG, JPG) or PDF.');
      return false;
    }

    // Check size
    if (file.size > maxSizeBytes) {
      const mb = (maxSizeBytes / (1024 * 1024)).toFixed(0);
      setError(`File is too large. Maximum size allowed is ${mb}MB.`);
      return false;
    }

    setError(null);
    return true;
  };

  const getValidFiles = (fileList) => {
    const files = Array.from(fileList || []);
    const validFiles = files.filter(validateFile);
    return multiple ? validFiles : validFiles.slice(0, 1);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    const validFiles = getValidFiles(e.dataTransfer.files);
    if (validFiles.length > 0) {
      onFileSelect(multiple ? validFiles : validFiles[0]);
    }
  };

  const handleFileInput = (e) => {
    const validFiles = getValidFiles(e.target.files);
    if (validFiles.length > 0) {
      onFileSelect(multiple ? validFiles : validFiles[0]);
    }
    e.target.value = '';
  };

  const triggerInputClick = () => {
    fileInputRef.current.click();
  };

  return (
    <Card hoverable>
      <div 
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={triggerInputClick}
        style={{
          border: isDragActive ? '2px dashed var(--accent-primary)' : '2px dashed var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '40px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          backgroundColor: isDragActive ? 'rgba(101, 184, 181, 0.12)' : 'rgba(255, 250, 245, 0.24)',
          transition: 'all 0.25s ease',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '220px'
        }}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileInput}
          accept={accept}
          multiple={multiple}
          style={{ display: 'none' }}
        />

        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: isDragActive ? 'rgba(101, 184, 181, 0.18)' : 'rgba(255, 250, 245, 0.38)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: isDragActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
          marginBottom: '16px',
          boxShadow: isDragActive ? '0 12px 26px -20px rgba(43, 100, 117, 0.48)' : 'none',
          transition: 'all 0.25s ease',
          fontSize: '28px'
        }}>
          ⬆
        </div>

        <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '6px' }}>
          Drag & Drop Prescription{multiple ? 's' : ''}
        </h4>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>
          or click to browse local files
        </p>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Supports JPEG, PNG, or PDF (up to 10MB)
        </span>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginTop: '16px',
            color: 'var(--accent-danger)',
            fontSize: '0.8rem',
            fontWeight: 500,
            backgroundColor: 'rgba(239, 68, 68, 0.08)',
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid rgba(239, 68, 68, 0.2)'
          }}>
            <AlertCircle size={14} />
            <span>{error}</span>
          </div>
        )}
      </div>
    </Card>
  );
}
