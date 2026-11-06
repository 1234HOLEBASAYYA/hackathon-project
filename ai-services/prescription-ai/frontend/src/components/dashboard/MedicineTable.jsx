import React from 'react';
import { AlertCircle, Plus, Trash2, ShieldCheck } from 'lucide-react';
import Card from '../common/Card';

export default function MedicineTable({ 
  medicines = [], 
  validation = { valid: true, flagged: [], suggestions: [], closest_matches: {} },
  onMedicinesChange 
}) {

  const handleCellChange = (index, field, value) => {
    const updated = [...medicines];
    updated[index] = {
      ...updated[index],
      [field]: value
    };
    onMedicinesChange(updated);
  };

  const handleAddRow = () => {
    onMedicinesChange([
      ...medicines,
      {
        name: '',
        dosage: '',
        frequency: '',
        duration: '',
        confidence: 100,
        confidences: { name: 100, dosage: 100, frequency: 100, duration: 100 }
      }
    ]);
  };

  const handleRemoveRow = (index) => {
    const updated = medicines.filter((_, idx) => idx !== index);
    onMedicinesChange(updated);
  };

  const applySuggestion = (index, suggestedName) => {
    handleCellChange(index, 'name', suggestedName);
  };

  const getFdaStatus = (name) => {
    if (!name) return { status: 'empty', badge: null };
    const lowerName = name.trim().toLowerCase();
    
    // Check if flagged or invalid in validation payload
    const isFlagged = validation?.flagged?.some(f => f.toLowerCase() === lowerName) || false;
    const suggestions = validation?.closest_matches?.[name] || [];

    if (isFlagged) {
      return {
        status: 'flagged',
        badge: (
          <span className="badge badge-danger" style={{ fontSize: '0.65rem', gap: '3px' }}>
            <AlertCircle size={10} /> UNVERIFIED
          </span>
        ),
        suggestions
      };
    }

    return {
      status: 'verified',
      badge: (
        <span className="badge badge-success" style={{ fontSize: '0.65rem', gap: '3px' }}>
          <ShieldCheck size={10} /> FDA MATCH
        </span>
      ),
      suggestions: []
    };
  };

  return (
    <Card 
      title="Prescribed Medications & FDA Safety Verification" 
      subtitle="Fuzzy-matches active drug ingredients against OpenFDA drug database catalog."
    >
      <div style={{ overflowX: 'auto', marginBottom: '16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', minWidth: '600px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <th style={{ padding: '12px 8px', fontWeight: 600 }}>Medicine Brand / Active Ingredient</th>
              <th style={{ padding: '12px 8px', fontWeight: 600 }}>Dosage</th>
              <th style={{ padding: '12px 8px', fontWeight: 600 }}>Frequency</th>
              <th style={{ padding: '12px 8px', fontWeight: 600 }}>Duration</th>
              <th style={{ padding: '12px 8px', fontWeight: 600, width: '120px' }}>FDA Status</th>
              <th style={{ padding: '12px 8px', width: '50px' }}></th>
            </tr>
          </thead>
          <tbody>
            {medicines.map((med, idx) => {
              const fda = getFdaStatus(med.name);
              return (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '0.9rem' }}>
                  
                  {/* Name field + suggestions */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top' }}>
                    <input 
                      type="text"
                      value={med.name || ''}
                      onChange={(e) => handleCellChange(idx, 'name', e.target.value)}
                      placeholder="e.g. Paracetamol"
                      className="form-control"
                      style={{ fontSize: '0.85rem', fontWeight: 600, padding: '6px 10px' }}
                    />
                    
                    {fda.status === 'flagged' && fda.suggestions.length > 0 && (
                      <div style={{ marginTop: '6px', fontSize: '0.7rem' }}>
                        <span style={{ color: 'var(--text-muted)', display: 'block', marginBottom: '2px' }}>Did you mean:</span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {fda.suggestions.slice(0, 3).map((sugg, sIdx) => (
                            <button
                              key={sIdx}
                              onClick={() => applySuggestion(idx, sugg)}
                              style={{
                                background: 'rgba(101, 184, 181, 0.13)',
                                border: '1px solid rgba(101, 184, 181, 0.26)',
                                borderRadius: '4px',
                                color: 'var(--accent-primary)',
                                padding: '2px 6px',
                                cursor: 'pointer',
                                fontSize: '0.7rem',
                                fontWeight: 500
                              }}
                            >
                              {sugg}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </td>

                  {/* Dosage */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top' }}>
                    <input 
                      type="text"
                      value={med.dosage || ''}
                      onChange={(e) => handleCellChange(idx, 'dosage', e.target.value)}
                      placeholder="e.g. 500mg"
                      className="form-control"
                      style={{ fontSize: '0.85rem', padding: '6px 10px' }}
                    />
                  </td>

                  {/* Frequency */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top' }}>
                    <input 
                      type="text"
                      value={med.frequency || ''}
                      onChange={(e) => handleCellChange(idx, 'frequency', e.target.value)}
                      placeholder="e.g. Once daily"
                      className="form-control"
                      style={{ fontSize: '0.85rem', padding: '6px 10px' }}
                    />
                  </td>

                  {/* Duration */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top' }}>
                    <input 
                      type="text"
                      value={med.duration || ''}
                      onChange={(e) => handleCellChange(idx, 'duration', e.target.value)}
                      placeholder="e.g. 5 days"
                      className="form-control"
                      style={{ fontSize: '0.85rem', padding: '6px 10px' }}
                    />
                  </td>

                  {/* FDA Status */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top', paddingTop: '16px' }}>
                    {fda.badge}
                  </td>

                  {/* Delete row */}
                  <td style={{ padding: '10px 8px', verticalAlign: 'top', paddingTop: '14px' }}>
                    <button 
                      onClick={() => handleRemoveRow(idx)}
                      style={{
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        color: 'var(--text-muted)',
                        padding: '4px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        transition: 'color 0.2s, background-color 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.color = 'var(--accent-danger)';
                        e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.08)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.color = 'var(--text-muted)';
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              );
            })}

            {medicines.length === 0 && (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                  No medications identified. Click below to manually add.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <button 
        onClick={handleAddRow}
        className="btn btn-secondary"
        style={{ fontSize: '0.8rem', padding: '6px 12px', gap: '4px' }}
      >
        <Plus size={14} /> Add Medication Row
      </button>
    </Card>
  );
}
