import React from 'react';
import { Database, Layers, CheckCircle2, AlertTriangle, Image as ImageIcon, Zap } from 'lucide-react';

export default function Sidebar({ onLoadSample, isAnalyzing }) {
  return (
    <aside style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Quick Demo Controls */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Zap size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>Instant Live Demos</h3>
        </div>
        <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '1rem', lineHeight: '1.4' }}>
          Test the trained ResNet-18 model instantly with validated images from the held-out test split:
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <button
            onClick={() => onLoadSample('NORMAL')}
            disabled={isAnalyzing}
            className="btn-secondary"
            style={{
              width: '100%',
              justifyContent: 'flex-start',
              padding: '0.6rem 0.85rem',
              borderColor: 'rgba(16, 185, 129, 0.3)',
              background: 'rgba(16, 185, 129, 0.08)'
            }}
          >
            <CheckCircle2 size={16} color="#34d399" />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#34d399' }}>Normal Chest X-Ray</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Healthy lung parenchyma sample</div>
            </div>
          </button>

          <button
            onClick={() => onLoadSample('PNEUMONIA')}
            disabled={isAnalyzing}
            className="btn-secondary"
            style={{
              width: '100%',
              justifyContent: 'flex-start',
              padding: '0.6rem 0.85rem',
              borderColor: 'rgba(239, 68, 68, 0.3)',
              background: 'rgba(239, 68, 68, 0.08)'
            }}
          >
            <AlertTriangle size={16} color="#f87171" />
            <div style={{ textAlign: 'left' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#f87171' }}>Pneumonia Chest X-Ray</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>Consolidation & infiltrate sample</div>
            </div>
          </button>
        </div>
      </div>

      {/* Model Spec Card */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Layers size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>Model Specification</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.8rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', paddingBottom: '0.4rem' }}>
            <span style={{ color: '#94a3b8' }}>Architecture</span>
            <span style={{ fontWeight: 600, color: '#f8fafc' }}>ResNet-18 (Deep Residual)</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', paddingBottom: '0.4rem' }}>
            <span style={{ color: '#94a3b8' }}>Transfer Learning</span>
            <span style={{ fontWeight: 600, color: '#38bdf8' }}>ImageNet Weights</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', paddingBottom: '0.4rem' }}>
            <span style={{ color: '#94a3b8' }}>Target Layer (Grad-CAM)</span>
            <span style={{ fontFamily: 'monospace', color: '#f8fafc' }}>model.layer4[-1]</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(51, 65, 85, 0.4)', paddingBottom: '0.4rem' }}>
            <span style={{ color: '#94a3b8' }}>Input Dimension</span>
            <span style={{ fontFamily: 'monospace', color: '#f8fafc' }}>224 × 224 × 3 RGB</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#94a3b8' }}>Output Head</span>
            <span style={{ fontWeight: 600, color: '#f8fafc' }}>Dropout(0.3) + Linear(512, 2)</span>
          </div>
        </div>
      </div>

      {/* Dataset Statistics */}
      <div className="glass-panel" style={{ padding: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <Database size={18} color="#38bdf8" />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>Dataset Distribution</h3>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.8rem' }}>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <span style={{ color: '#94a3b8' }}>Training Set</span>
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>5,216 images</span>
            </div>
            <div style={{ display: 'flex', gap: '4px' }}>
              <div style={{ flex: 1341, height: '4px', background: '#10b981', borderRadius: '2px' }} title="1,341 Normal" />
              <div style={{ flex: 3875, height: '4px', background: '#ef4444', borderRadius: '2px' }} title="3,875 Pneumonia" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: '2px' }}>
              <span>25.7% Normal</span>
              <span>74.3% Pneumonia</span>
            </div>
          </div>

          <div style={{ paddingTop: '0.5rem', borderTop: '1px solid rgba(51, 65, 85, 0.4)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#94a3b8' }}>Held-out Test Split</span>
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>624 images</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b' }}>
              <span>234 Normal</span>
              <span>390 Pneumonia</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
