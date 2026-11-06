import React from 'react';

export default function Card({ children, title, subtitle, className = '', hoverable = false, style = {} }) {
  const baseClass = hoverable ? 'glass-card glass-card-hover' : 'glass-card';
  return (
    <div className={`${baseClass} ${className}`} style={style}>
      {(title || subtitle) && (
        <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          {title && <h3 style={{ fontSize: '1.25rem', fontWeight: 600 }}>{title}</h3>}
          {subtitle && <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}
