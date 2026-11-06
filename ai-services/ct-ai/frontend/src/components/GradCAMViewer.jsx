import React, { useState } from 'react';
import { Eye, Sliders, Layers, Target, Download, ZoomIn, Info } from 'lucide-react';

export default function GradCAMViewer({ gradcam, rawImage }) {
  const [viewMode, setViewMode] = useState('overlay'); // 'overlay' | 'heatmap' | 'original'
  const [showRois, setShowRois] = useState(true);
  const [clientAlpha, setClientAlpha] = useState(0.45);

  if (!gradcam) return null;

  const currentImage = viewMode === 'overlay'
    ? gradcam.overlay_b64
    : viewMode === 'heatmap'
    ? gradcam.heatmap_b64
    : rawImage;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Title & Controls Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        paddingBottom: '0.85rem',
        borderBottom: '1px solid var(--border-color)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Eye size={20} color="#38bdf8" />
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
              Grad-CAM Explainability Heatmap
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#64748b' }}>
              ResNet-18 Layer4 Convolutional Feature Activation Mapping
            </p>
          </div>
        </div>

        {/* View Mode Buttons */}
        <div style={{
          display: 'flex',
          background: 'rgba(30, 41, 59, 0.7)',
          padding: '0.2rem',
          borderRadius: '8px',
          border: '1px solid var(--border-color)'
        }}>
          {[
            { id: 'overlay', label: 'CAM Overlay' },
            { id: 'heatmap', label: 'Raw Heatmap' },
            ...(rawImage ? [{ id: 'original', label: 'Original X-Ray' }] : []),
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setViewMode(mode.id)}
              style={{
                background: viewMode === mode.id ? '#0284c7' : 'transparent',
                color: viewMode === mode.id ? '#ffffff' : '#94a3b8',
                border: 'none',
                borderRadius: '6px',
                padding: '0.35rem 0.75rem',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Image Viewport */}
      <div style={{
        position: 'relative',
        background: '#030712',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid rgba(56, 189, 248, 0.2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '340px'
      }}>
        {currentImage ? (
          <div style={{ position: 'relative', display: 'inline-block' }}>
            <img
              src={currentImage}
              alt="Grad-CAM Visualization"
              style={{
                maxWidth: '100%',
                maxHeight: '450px',
                display: 'block',
                borderRadius: '8px'
              }}
            />

            {/* ROI Bounding Boxes */}
            {showRois && viewMode !== 'heatmap' && gradcam.rois?.map((roi, idx) => (
              <div
                key={idx}
                style={{
                  position: 'absolute',
                  left: `${roi.relative_x * 100}%`,
                  top: `${roi.relative_y * 100}%`,
                  width: `${roi.relative_width * 100}%`,
                  height: `${roi.relative_height * 100}%`,
                  border: '2px solid #ef4444',
                  boxShadow: '0 0 10px rgba(239, 68, 68, 0.6)',
                  borderRadius: '4px',
                  pointerEvents: 'none'
                }}
              >
                <span style={{
                  position: 'absolute',
                  top: '-20px',
                  left: '0',
                  background: '#ef4444',
                  color: '#ffffff',
                  fontSize: '0.65rem',
                  fontWeight: 700,
                  padding: '1px 5px',
                  borderRadius: '3px',
                  whiteSpace: 'nowrap'
                }}>
                  ROI #{idx + 1} ({Math.round(roi.relative_width * 100)}% W)
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: '#64748b', fontSize: '0.85rem' }}>No visualization image loaded</div>
        )}

        {/* Badge Indicator in Bottom Corner */}
        <div style={{
          position: 'absolute',
          bottom: '12px',
          right: '12px',
          background: 'rgba(15, 23, 42, 0.85)',
          backdropFilter: 'blur(8px)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '0.35rem 0.65rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.75rem',
          color: '#cbd5e1'
        }}>
          <Target size={14} color="#38bdf8" />
          <span>ROIs Detected: <strong>{gradcam.rois?.length || 0}</strong></span>
          <span style={{ color: '#475569' }}>•</span>
          <span>Opacity Index: <strong>{(gradcam.opacity_score * 100).toFixed(1)}%</strong></span>
        </div>
      </div>

      {/* Controls & Options Bar */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        padding: '0.85rem 1rem',
        background: 'rgba(30, 41, 59, 0.4)',
        borderRadius: '10px',
        border: '1px solid rgba(51, 65, 85, 0.4)'
      }}>
        {/* Toggle ROI bounding boxes */}
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.825rem', color: '#cbd5e1' }}>
          <input
            type="checkbox"
            checked={showRois}
            onChange={(e) => setShowRois(e.target.checked)}
            style={{ accentColor: '#0284c7', width: '15px', height: '15px', cursor: 'pointer' }}
          />
          <span>Highlight Focal ROI Bounding Boxes</span>
        </label>

        {/* Heatmap Spectrum Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', fontSize: '0.75rem', color: '#94a3b8' }}>
          <span>Low Activation</span>
          <div style={{
            width: '90px',
            height: '10px',
            borderRadius: '4px',
            background: 'linear-gradient(to right, #0000ff, #00ffff, #00ff00, #ffff00, #ff0000)'
          }} />
          <span>High (Pneumonia Infiltrate)</span>
        </div>

        {/* Export / Download Button */}
        {currentImage && (
          <a
            href={currentImage}
            download="resnet18_gradcam_analysis.png"
            className="btn-secondary"
            style={{ padding: '0.4rem 0.85rem', fontSize: '0.8rem' }}
          >
            <Download size={14} />
            <span>Export Image</span>
          </a>
        )}
      </div>
    </div>
  );
}
