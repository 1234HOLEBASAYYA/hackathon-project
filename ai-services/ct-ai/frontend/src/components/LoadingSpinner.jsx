import React from 'react';

export default function LoadingSpinner({ message = 'Running deep ResNet18 inference & Grad-CAM analysis...' }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 1.5rem', gap: '1.25rem' }}>
      <div style={{ position: 'relative', width: '70px', height: '70px' }}>
        <div style={{
          position: 'absolute', inset: 0, borderRadius: '50%',
          border: '3px solid rgba(6, 182, 212, 0.2)',
          borderTopColor: '#06b6d4',
          animation: 'spin 1s linear infinite'
        }} />
        <div style={{
          position: 'absolute', inset: '8px', borderRadius: '50%',
          border: '3px solid rgba(59, 130, 246, 0.2)',
          borderBottomColor: '#3b82f6',
          animation: 'spin-reverse 1.5s linear infinite'
        }} />
        <div style={{
          position: 'absolute', inset: '18px', borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(6,182,212,0.4) 0%, transparent 70%)'
        }} />
      </div>
      <p style={{ color: '#94a3b8', fontSize: '0.95rem', fontWeight: 500, textAlign: 'center' }}>
        {message}
      </p>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        @keyframes spin-reverse {
          to { transform: rotate(-360deg); }
        }
      `}</style>
    </div>
  );
}
