import React from 'react';

export default function Loader({ message = 'Analyzing Prescription...', size = 'md' }) {
  const spinnerSize = size === 'sm' ? '24px' : size === 'lg' ? '64px' : '40px';
  const borderWidth = size === 'sm' ? '2px' : '3px';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px' }}>
      <div style={{ position: 'relative', width: spinnerSize, height: spinnerSize, marginBottom: '20px' }}>
        <div style={{
          boxSizing: 'border-box',
          display: 'block',
          position: 'absolute',
          width: spinnerSize,
          height: spinnerSize,
          borderRadius: '50%',
          border: `${borderWidth} solid var(--accent-primary)`,
          borderColor: 'var(--accent-primary) transparent transparent transparent',
          animation: 'spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite'
        }} />
        <div style={{
          boxSizing: 'border-box',
          display: 'block',
          position: 'absolute',
          width: spinnerSize,
          height: spinnerSize,
          borderRadius: '50%',
          border: `${borderWidth} solid rgba(101, 184, 181, 0.16)`,
        }} />
      </div>
      {message && (
        <p style={{
          fontSize: size === 'sm' ? '0.85rem' : '1rem',
          fontWeight: 600,
          color: 'var(--accent-primary)',
          letterSpacing: '0.02em',
          animation: 'pulse-glow 1.5s ease-in-out infinite alternate',
          textAlign: 'center'
        }}>
          {message}
        </p>
      )}

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulse-glow {
          0% { opacity: 0.6; }
          100% { opacity: 1; text-shadow: 0 8px 18px rgba(43, 100, 117, 0.2); }
        }
      `}} />
    </div>
  );
}
