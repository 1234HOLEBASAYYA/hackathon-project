import React from 'react';
import { User, Calendar, Stethoscope, ClipboardList, Info } from 'lucide-react';
import Card from '../common/Card';

export default function StructuredCard({ fields, onFieldChange }) {
  const getConfidenceStyle = (confidence) => {
    if (confidence === undefined) return { borderLeft: '3px solid var(--border-color)' };
    if (confidence >= 80) return { borderLeft: '3px solid var(--accent-success)' };
    if (confidence >= 60) return { borderLeft: '3px solid var(--accent-warning)' };
    return { borderLeft: '3px solid var(--accent-danger)' };
  };

  const handleInputChange = (key, value) => {
    onFieldChange({
      ...fields,
      [key]: value
    });
  };

  return (
    <Card title="EHR Structured Data Entity Extraction" subtitle="Verify and edit parsed medical parameters below.">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        
        {/* Patient Name */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.patient_name)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0 }}>
            <User size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Patient Name</label>
            <input 
              type="text" 
              value={fields.patient_name || ''} 
              onChange={(e) => handleInputChange('patient_name', e.target.value)}
              placeholder="Not found"
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.95rem', fontWeight: 600 }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.patient_name >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.patient_name ? `${Math.round(fields.confidences.patient_name)}%` : 'N/A'}
          </div>
        </div>

        {/* Patient Age */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.patient_age)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0 }}>
            <Calendar size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Patient Age / Age Group</label>
            <input 
              type="text" 
              value={fields.patient_age || ''} 
              onChange={(e) => handleInputChange('patient_age', e.target.value)}
              placeholder="Not found"
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.95rem', fontWeight: 600 }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.patient_age >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.patient_age ? `${Math.round(fields.confidences.patient_age)}%` : 'N/A'}
          </div>
        </div>

        {/* Date */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.date)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0 }}>
            <Calendar size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Prescription Date</label>
            <input 
              type="text" 
              value={fields.date || ''} 
              onChange={(e) => handleInputChange('date', e.target.value)}
              placeholder="Not found"
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.95rem', fontWeight: 600 }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.date >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.date ? `${Math.round(fields.confidences.date)}%` : 'N/A'}
          </div>
        </div>

        {/* Doctor Name */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.doctor_name)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0 }}>
            <Stethoscope size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Prescribing Physician</label>
            <input 
              type="text" 
              value={fields.doctor_name || ''} 
              onChange={(e) => handleInputChange('doctor_name', e.target.value)}
              placeholder="Not found"
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.95rem', fontWeight: 600 }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.doctor_name >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.doctor_name ? `${Math.round(fields.confidences.doctor_name)}%` : 'N/A'}
          </div>
        </div>

        {/* Diagnosis */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.diagnosis)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0 }}>
            <ClipboardList size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Diagnosis / Symptoms</label>
            <input 
              type="text" 
              value={fields.diagnosis || ''} 
              onChange={(e) => handleInputChange('diagnosis', e.target.value)}
              placeholder="Not found"
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.95rem', fontWeight: 600 }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.diagnosis >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.diagnosis ? `${Math.round(fields.confidences.diagnosis)}%` : 'N/A'}
          </div>
        </div>

        {/* Notes */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'start',
            gap: '12px',
            padding: '12px',
            backgroundColor: 'rgba(255,255,255,0.01)',
            borderRadius: 'var(--radius-sm)',
            ...getConfidenceStyle(fields.confidences?.notes)
          }}
        >
          <div style={{ color: 'var(--accent-primary)', flexShrink: 0, marginTop: '4px' }}>
            <Info size={20} />
          </div>
          <div style={{ flexGrow: 1 }}>
            <label className="form-label" style={{ fontSize: '0.75rem', marginBottom: '2px' }}>Additional Notes / Usage Instructions</label>
            <textarea 
              value={fields.notes || ''} 
              onChange={(e) => handleInputChange('notes', e.target.value)}
              placeholder="No notes found"
              rows={2}
              className="form-control"
              style={{ border: 'none', background: 'none', padding: 0, fontSize: '0.9rem', width: '100%', resize: 'none' }}
            />
          </div>
          <div style={{ fontSize: '0.75rem', fontWeight: 700, color: fields.confidences?.notes >= 60 ? 'var(--text-secondary)' : 'var(--accent-danger)' }}>
            {fields.confidences?.notes ? `${Math.round(fields.confidences.notes)}%` : 'N/A'}
          </div>
        </div>

      </div>
    </Card>
  );
}
