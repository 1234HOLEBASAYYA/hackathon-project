import React, { useState } from 'react';
import { Split, Layers, RefreshCw } from 'lucide-react';
import Card from '../common/Card';

export default function ImageComparer({ originalFile, processedImageUrl, isProcessing }) {
  const [viewMode, setViewMode] = useState('side-by-side'); // 'side-by-side' | 'tabs' | 'single'
  const [activeTab, setActiveTab] = useState('original'); // 'original' | 'processed'

  if (!originalFile) {
    return (
      <Card title="Visual Inspection Sandbox" className="flex-center" style={{ height: '350px' }}>
        <p style={{ color: 'var(--text-muted)' }}>Upload an image to inspect the CV preprocessing output.</p>
      </Card>
    );
  }

  const originalUrl = URL.createObjectURL(originalFile);

  return (
    <Card 
      title="Visual Inspection Sandbox" 
      subtitle="Examine how deskewing, CLAHE grid-contrast, and adaptive binarization affect image clarity."
    >
      {/* Controls */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => setViewMode('side-by-side')}
            className={`btn ${viewMode === 'side-by-side' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            <Split size={14} /> Side-by-Side
          </button>
          <button 
            onClick={() => setViewMode('tabs')}
            className={`btn ${viewMode === 'tabs' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            <Layers size={14} /> Tabs Toggle
          </button>
        </div>

        {viewMode === 'tabs' && (
          <div style={{ display: 'flex', gap: '4px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '4px', padding: '2px' }}>
            <button 
              onClick={() => setActiveTab('original')}
              style={{
                background: activeTab === 'original' ? 'var(--accent-primary)' : 'none',
                color: activeTab === 'original' ? '#14333A' : 'var(--text-primary)',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Original
            </button>
            <button 
              onClick={() => setActiveTab('processed')}
              style={{
                background: activeTab === 'processed' ? 'var(--accent-primary)' : 'none',
                color: activeTab === 'processed' ? '#14333A' : 'var(--text-primary)',
                border: 'none',
                padding: '4px 10px',
                borderRadius: '4px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
              disabled={!processedImageUrl}
            >
              Binarized Mask
            </button>
          </div>
        )}
      </div>

      {/* Main Viewport */}
      <div style={{
        backgroundColor: 'rgba(255, 250, 245, 0.34)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-sm)',
        padding: '12px',
        minHeight: '300px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
        position: 'relative'
      }}>
        {isProcessing && (
          <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(8, 11, 16, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 10
          }}>
            <RefreshCw size={24} className="spin" style={{ color: 'var(--accent-primary)', animation: 'spin 1.5s linear infinite' }} />
          </div>
        )}

        {/* Side by Side */}
        {viewMode === 'side-by-side' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', width: '100%', height: '100%' }}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>Original Upload</span>
              <div style={{ border: '1px solid rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', maxHeight: '350px' }}>
                <img src={originalUrl} alt="Original Prescription" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain' }} />
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '6px', fontWeight: 600, textTransform: 'uppercase' }}>Binarized (OCR Input)</span>
              {processedImageUrl ? (
                <div style={{ border: '1px solid rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden', maxHeight: '350px' }}>
                  <img src={processedImageUrl} alt="Preprocessed" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain' }} />
                </div>
              ) : (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  Awaiting analysis...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tabs Toggle */}
        {viewMode === 'tabs' && (
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center', maxHeight: '350px' }}>
            {activeTab === 'original' ? (
              <img src={originalUrl} alt="Original Prescription" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain' }} />
            ) : (
              processedImageUrl && <img src={processedImageUrl} alt="Preprocessed" style={{ maxWidth: '100%', maxHeight: '340px', objectFit: 'contain' }} />
            )}
          </div>
        )}
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}} />
    </Card>
  );
}
