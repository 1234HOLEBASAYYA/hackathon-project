import React, { useEffect } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export default function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const typeConfig = {
    success: {
      bgColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: 'var(--accent-success)',
      icon: <CheckCircle size={18} color="var(--accent-success)" />
    },
    warning: {
      bgColor: 'rgba(245, 158, 11, 0.1)',
      borderColor: 'var(--accent-warning)',
      icon: <AlertTriangle size={18} color="var(--accent-warning)" />
    },
    error: {
      bgColor: 'rgba(239, 68, 68, 0.1)',
      borderColor: 'var(--accent-danger)',
      icon: <XCircle size={18} color="var(--accent-danger)" />
    },
    info: {
      bgColor: 'rgba(59, 130, 246, 0.1)',
      borderColor: 'var(--accent-secondary)',
      icon: <Info size={18} color="var(--accent-secondary)" />
    }
  };

  const current = typeConfig[type] || typeConfig.info;

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '14px 20px',
      borderRadius: 'var(--radius-sm)',
      backgroundColor: current.bgColor,
      border: `1px solid ${current.borderColor}`,
      boxShadow: 'var(--shadow-lg)',
      backdropFilter: 'blur(8px)',
      minWidth: '300px',
      maxWidth: '450px',
      color: 'var(--text-primary)',
      position: 'relative',
      animation: 'slide-in 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      zIndex: 9999
    }}>
      <div style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
        {current.icon}
      </div>
      <div style={{ flexGrow: 1, fontSize: '0.875rem', fontWeight: 500, paddingRight: '8px' }}>
        {message}
      </div>
      <button 
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '2px',
          color: 'var(--text-secondary)',
          display: 'flex',
          alignItems: 'center',
          transition: 'color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text-primary)'}
        onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-secondary)'}
      >
        <X size={16} />
      </button>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes slide-in {
          0% { transform: translateY(100%) scale(0.9); opacity: 0; }
          100% { transform: translateY(0) scale(1); opacity: 1; }
        }
      `}} />
    </div>
  );
}
