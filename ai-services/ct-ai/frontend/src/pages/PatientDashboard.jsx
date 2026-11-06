import React, { useState } from 'react';
import { User, Heart, AlertCircle, CheckCircle, HelpCircle, PhoneCall, ShieldAlert, Sparkles } from 'lucide-react';

export default function PatientDashboard() {
  const [checklist, setChecklist] = useState({
    medication: false,
    fluids: true,
    rest: true,
    temp_check: false,
    followup: false
  });

  const toggleChecklist = (key) => {
    setChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '2rem', paddingBottom: '3rem' }}>
      {/* Welcome Banner */}
      <div className="glass-panel" style={{
        padding: '2.5rem 2rem',
        background: 'radial-gradient(ellipse at top left, rgba(16, 185, 129, 0.15) 0%, rgba(15, 23, 42, 0.8) 70%)',
        borderLeft: '5px solid #10b981'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.75rem' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <User size={24} color="#34d399" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.45rem', fontWeight: 800, color: '#f8fafc' }}>
              Patient Health & Care Guide
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Understanding your radiograph results, symptoms, and recovery steps
            </p>
          </div>
        </div>
        <p style={{ fontSize: '0.95rem', color: '#cbd5e1', lineHeight: 1.6, maxWidth: '850px' }}>
          This portal translates complex radiological findings into straightforward, actionable health information.
          Remember that AI-generated insights support clinical care and should always be discussed with your physician.
        </p>
      </div>

      {/* 2-Column Grid: Explanations + Checklist */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem' }}>
        {/* Understanding Results */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Heart size={20} color="#38bdf8" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              What Does Your Result Mean?
            </h2>
          </div>

          <div className="glass-card" style={{ borderLeft: '3px solid #34d399' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#34d399', marginBottom: '0.25rem' }}>
              Normal Chest Radiograph
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Healthy lungs appear mostly dark on an X-ray because air does not block X-rays. A "Normal" reading means your lungs show clear air passages without abnormal fluid build-up or solid areas.
            </p>
          </div>

          <div className="glass-card" style={{ borderLeft: '3px solid #f87171' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f87171', marginBottom: '0.25rem' }}>
              Pneumonia Finding (Infiltrates / Opacity)
            </h3>
            <p style={{ fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Pneumonia is an infection in one or both lungs causing tiny air sacs (alveoli) to fill with fluid or inflammatory cells. This shows up as lighter cloudy patches (infiltrates) on an X-ray.
            </p>
          </div>
        </div>

        {/* Daily Recovery Checklist */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckCircle size={20} color="#10b981" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              Daily Recovery Checklist
            </h2>
          </div>
          <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
            Track your key home care habits while recovering from respiratory illness:
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { id: 'medication', label: 'Take prescribed antibiotics / medicines on schedule' },
              { id: 'fluids', label: 'Drink at least 8-10 glasses of water or warm fluids' },
              { id: 'rest', label: 'Get 8+ hours of sleep and avoid strenuous physical exertion' },
              { id: 'temp_check', label: 'Record body temperature (morning & evening)' },
              { id: 'followup', label: 'Schedule follow-up appointment with physician' },
            ].map((item) => (
              <label
                key={item.id}
                onClick={() => toggleChecklist(item.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem',
                  borderRadius: '8px',
                  background: checklist[item.id] ? 'rgba(16, 185, 129, 0.1)' : 'rgba(30, 41, 59, 0.4)',
                  border: `1px solid ${checklist[item.id] ? 'rgba(16, 185, 129, 0.3)' : 'rgba(51, 65, 85, 0.4)'}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <input
                  type="checkbox"
                  checked={checklist[item.id]}
                  readOnly
                  style={{ accentColor: '#10b981', width: '16px', height: '16px' }}
                />
                <span style={{
                  fontSize: '0.85rem',
                  color: checklist[item.id] ? '#f8fafc' : '#94a3b8',
                  textDecoration: checklist[item.id] ? 'none' : 'none'
                }}>
                  {item.label}
                </span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Red Flag Warning Box */}
      <div className="glass-panel" style={{
        padding: '1.5rem',
        borderLeft: '5px solid #ef4444',
        background: 'rgba(239, 68, 68, 0.08)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <ShieldAlert size={22} color="#f87171" />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>
            When to Seek Immediate Emergency Medical Care
          </h2>
        </div>
        <p style={{ fontSize: '0.85rem', color: '#cbd5e1', marginBottom: '0.75rem' }}>
          Contact emergency services (or go to nearest emergency department) immediately if you experience:
        </p>
        <ul style={{ paddingLeft: '1.25rem', fontSize: '0.85rem', color: '#94a3b8', lineHeight: 1.6 }}>
          <li>Severe difficulty breathing or rapid shortness of breath while resting.</li>
          <li>Persistent chest pain or pressure when inhaling or coughing.</li>
          <li>Bluish or pale color in lips, nailbeds, or skin (hypoxemia indicator).</li>
          <li>New confusion, disorientation, or difficulty waking up (especially in elderly patients).</li>
          <li>High fever above 39°C (102.2°F) that does not respond to antipyretic medication.</li>
        </ul>
      </div>
    </div>
  );
}
