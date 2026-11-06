import React from 'react';
import { AlertTriangle, CheckCircle2, ShieldAlert, HeartPulse, FileText, Stethoscope, User } from 'lucide-react';

export default function PredictionCard({ result }) {
  if (!result) return null;

  const isPneumonia = result.prediction === 'PNEUMONIA';
  const confidencePct = (result.confidence * 100).toFixed(1);
  const normalProb = ((result.probabilities?.NORMAL || 0) * 100).toFixed(1);
  const pneumoniaProb = ((result.probabilities?.PNEUMONIA || 0) * 100).toFixed(1);

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top Banner */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: '1rem',
        borderBottom: '1px solid var(--border-color)',
        flexWrap: 'wrap',
        gap: '0.75rem'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: isPneumonia ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            border: `1px solid ${isPneumonia ? 'rgba(239, 68, 68, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            {isPneumonia ? (
              <AlertTriangle size={24} color="#f87171" />
            ) : (
              <CheckCircle2 size={24} color="#34d399" />
            )}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h2 style={{
                fontSize: '1.25rem',
                fontWeight: 800,
                color: isPneumonia ? '#f87171' : '#34d399',
                letterSpacing: '-0.01em'
              }}>
                {isPneumonia ? 'PNEUMONIA DETECTED' : 'NORMAL CHEST RADIOGRAPH'}
              </h2>
              <span className={isPneumonia ? 'badge badge-pneumonia' : 'badge badge-normal'}>
                {result.severity && result.severity !== 'None' ? `${result.severity} Risk` : 'Clear'}
              </span>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
              {isPneumonia
                ? 'Parenchymal consolidation / opacification identified'
                : 'No focal consolidation, effusion, or active infiltrate'}
            </p>
          </div>
        </div>

        {/* Confidence Percentage */}
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.75rem', fontWeight: 800, color: '#f8fafc', lineHeight: 1 }}>
            {confidencePct}%
          </div>
          <div style={{ fontSize: '0.725rem', color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>
            Diagnostic Confidence
          </div>
        </div>
      </div>

      {/* Probabilities Breakdown */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
          <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#34d399' }} />
            Normal (Healthy):
          </span>
          <span style={{ fontWeight: 600, color: '#f8fafc' }}>{normalProb}%</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${normalProb}%`, background: '#10b981' }} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginTop: '0.25rem' }}>
          <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f87171' }} />
            Pneumonia (Infection):
          </span>
          <span style={{ fontWeight: 600, color: '#f8fafc' }}>{pneumoniaProb}%</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${pneumoniaProb}%`, background: '#ef4444' }} />
        </div>
      </div>

      {/* Clinical Finding */}
      <div className="glass-card" style={{ borderLeft: '4px solid #38bdf8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
          <HeartPulse size={16} color="#38bdf8" />
          <span style={{ fontSize: '0.825rem', fontWeight: 700, color: '#38bdf8', textTransform: 'uppercase' }}>
            Radiographic Finding
          </span>
        </div>
        <p style={{ fontSize: '0.875rem', color: '#e2e8f0', lineHeight: 1.5 }}>
          {result.clinical_finding}
        </p>
      </div>

      {/* Dual Perspective: Doctor vs Patient */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
        {/* Doctor Note */}
        <div className="glass-card" style={{ borderLeft: '4px solid #818cf8' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
            <Stethoscope size={16} color="#818cf8" />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase' }}>
              Doctor Recommendation
            </span>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#cbd5e1', lineHeight: 1.45 }}>
            {result.doctor_recommendation}
          </p>
        </div>

        {/* Patient Explanation */}
        <div className="glass-card" style={{ borderLeft: '4px solid #34d399' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.35rem' }}>
            <User size={16} color="#34d399" />
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', textTransform: 'uppercase' }}>
              Patient-Friendly Summary
            </span>
          </div>
          <p style={{ fontSize: '0.825rem', color: '#cbd5e1', lineHeight: 1.45 }}>
            {result.patient_explanation}
          </p>
        </div>
      </div>
    </div>
  );
}
