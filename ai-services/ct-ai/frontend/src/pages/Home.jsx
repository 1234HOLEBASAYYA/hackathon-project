import React from 'react';
import { Activity, ShieldCheck, Cpu, Eye, BarChart3, Stethoscope, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Home({ setActivePage }) {
  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2.5rem', paddingBottom: '3rem' }}>
      {/* Hero Section */}
      <div className="glass-panel" style={{
        padding: '3.5rem 2.5rem',
        background: 'radial-gradient(ellipse at top right, rgba(6, 182, 212, 0.15) 0%, rgba(15, 23, 42, 0.8) 70%)',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ maxWidth: '780px', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span className="badge badge-cyan">Hackathon Finalist Prototype</span>
            <span className="badge badge-normal">ResNet-18 Transfer Learning</span>
          </div>

          <h1 style={{ fontSize: '2.8rem', fontWeight: 800, lineHeight: 1.15, letterSpacing: '-0.025em', color: '#f8fafc' }}>
            Medical Image-Based <br />
            <span style={{
              background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Abnormality Detection & Visualization
            </span>
          </h1>

          <p style={{ fontSize: '1.05rem', color: '#94a3b8', lineHeight: 1.6 }}>
            A clinical-grade diagnostic assistance prototype leveraging deep transfer learning with ResNet-18
            and Gradient-weighted Class Activation Mapping (Grad-CAM) to pinpoint, explain, and quantify
            pneumonia abnormalities in chest radiographs with verified held-out evaluation.
          </p>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
            <button
              onClick={() => setActivePage('image-analysis')}
              className="btn-primary"
              style={{ padding: '0.8rem 1.6rem', fontSize: '1rem' }}
            >
              <ShieldCheck size={20} />
              <span>Launch X-Ray Analysis</span>
              <ArrowRight size={18} />
            </button>

            <button
              onClick={() => setActivePage('doctor')}
              className="btn-secondary"
              style={{ padding: '0.8rem 1.4rem', fontSize: '1rem' }}
            >
              <Stethoscope size={20} />
              <span>Doctor Dashboard & Metrics</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4 Pillars of Evaluation (Originality, Feasibility, Value Addition, Presentation) */}
      <div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '1.25rem', color: '#f8fafc' }}>
          System Capabilities & Hackathon Pillars
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={22} color="#38bdf8" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>ResNet-18 Transfer Learning</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Fine-tuned on 5,856 Kaggle Chest X-Rays with weighted loss to handle clinical class imbalance and prevent false-negative pneumonia misses.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Eye size={22} color="#818cf8" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Explainable Grad-CAM</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Hooks directly into layer4 convolution features to generate color-coded spatial heatmaps and bounding box regions of interest (ROI) over opacities.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BarChart3 size={22} color="#34d399" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Held-out Test Evaluation</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Strictly evaluated on 624 un-seen test radiographs, providing real accuracy, precision, recall, F1-score, and confusion matrix data.
            </p>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: '10px', background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Stethoscope size={22} color="#fbbf24" />
            </div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>Dual Doctor & Patient Flow</h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Physicians receive technical radiological interpretations and ROI dimensions, while patients receive clear, jargon-free health guidance.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
