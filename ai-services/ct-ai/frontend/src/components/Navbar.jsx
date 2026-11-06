import React, { useEffect, useState } from 'react';
import { Activity, ShieldCheck, Stethoscope, User, FileText, Cpu, AlertCircle, Scan } from 'lucide-react';
import { checkSystemHealth } from '../services/api';

export default function Navbar({ activePage, setActivePage }) {
  const [health, setHealth] = useState({ status: 'checking', device: 'CPU' });

  useEffect(() => {
    checkSystemHealth().then(setHealth);
    const interval = setInterval(() => {
      checkSystemHealth().then(setHealth);
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: 'ct-scan', label: 'CT Scan Analyzer', icon: Scan },
    { id: 'image-analysis', label: 'X-Ray Analysis', icon: ShieldCheck },
    { id: 'doctor', label: 'Doctor Dashboard', icon: Stethoscope },
    { id: 'patient', label: 'Patient Portal', icon: User },
    { id: 'prescriptions', label: 'Prescription & Rx', icon: FileText },
  ];

  return (
    <header style={{
      borderBottom: '1px solid var(--border-color)',
      background: 'rgba(10, 15, 29, 0.85)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0.85rem 2rem'
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem'
      }}>
        {/* Brand */}
        <div
          onClick={() => setActivePage('home')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)',
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)'
          }}>
            <Activity size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>
                Pneumo<span style={{ color: '#38bdf8' }}>Scan</span>
              </span>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.3)',
                padding: '0.1rem 0.4rem',
                borderRadius: '4px'
              }}>
                RESNET-18
              </span>
            </div>
            <p style={{ fontSize: '0.72rem', color: '#64748b' }}>Explainable Clinical X-Ray Abnormality Detection</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem 0.95rem',
                  borderRadius: '8px',
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#38bdf8' : '#94a3b8',
                  background: isActive ? 'rgba(56, 189, 248, 0.12)' : 'transparent',
                  border: isActive ? '1px solid rgba(56, 189, 248, 0.25)' : '1px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Icon size={16} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* System Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.35rem 0.75rem',
            borderRadius: '9999px',
            background: health.status === 'healthy' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
            border: `1px solid ${health.status === 'healthy' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            fontSize: '0.75rem',
            fontWeight: 600,
            color: health.status === 'healthy' ? '#34d399' : '#f87171'
          }}>
            <div style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: health.status === 'healthy' ? '#10b981' : '#ef4444',
              boxShadow: health.status === 'healthy' ? '0 0 8px #10b981' : 'none'
            }} />
            <span>{health.status === 'healthy' ? 'AI Core Online' : 'System Syncing'}</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.75rem',
            color: '#64748b',
            background: 'rgba(30, 41, 59, 0.6)',
            padding: '0.35rem 0.65rem',
            borderRadius: '6px'
          }}>
            <Cpu size={14} color="#94a3b8" />
            <span>{health.device || 'CPU'}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
