import React, { useState } from 'react';
import Card from '../common/Card';

export default function TextHighlight({ rawText, wordBoxes = [] }) {
  const [showLowConfidenceOnly, setShowLowConfidenceOnly] = useState(false);
  const lowConfidenceWords = wordBoxes.filter(box => box.confidence < 70);

  const getWordStyle = (confidence) => {
    if (confidence >= 80) return { color: 'var(--text-primary)' };
    if (confidence >= 60) return { color: 'var(--accent-warning)', borderBottom: '1px dotted var(--accent-warning)', fontWeight: 600 };
    return { color: 'var(--accent-danger)', borderBottom: '1px dashed var(--accent-danger)', fontWeight: 700, backgroundColor: 'rgba(239, 68, 68, 0.05)' };
  };

  return (
    <Card 
      title="Raw Transcription Auditing" 
      subtitle="Examine extracted raw lines and inspect low-confidence characters."
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        
        {/* Toggle options */}
        {wordBoxes.length > 0 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button 
              onClick={() => setShowLowConfidenceOnly(!showLowConfidenceOnly)}
              className={`btn ${showLowConfidenceOnly ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 10px', fontSize: '0.75rem', gap: '4px' }}
            >
              ⚠ 
              {showLowConfidenceOnly ? 'Show Full Transcript' : `Show Low Confidence (${lowConfidenceWords.length})`}
            </button>
          </div>
        )}

        {/* Text Viewport */}
        {!showLowConfidenceOnly ? (
          <div style={{
            backgroundColor: 'rgba(255, 250, 245, 0.38)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px',
            maxHeight: '280px',
            overflowY: 'auto',
            textAlign: 'left',
            fontFamily: 'var(--mono)',
            fontSize: '0.85rem',
            lineHeight: '1.6',
            whiteSpace: 'pre-wrap',
            color: 'var(--text-secondary)'
          }}>
            {rawText || 'No transcription extracted.'}
          </div>
        ) : (
          <div style={{
            backgroundColor: 'rgba(255, 250, 245, 0.38)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            padding: '16px',
            maxHeight: '280px',
            overflowY: 'auto',
          }}>
            {lowConfidenceWords.length === 0 ? (
              <p style={{ color: 'var(--accent-success)', fontSize: '0.85rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                ✨ 100% of characters have excellent confidences!
              </p>
            ) : (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {lowConfidenceWords.map((box, idx) => (
                  <span 
                    key={idx}
                    title={`Confidence: ${Math.round(box.confidence)}%`}
                    style={{
                      padding: '4px 8px',
                      borderRadius: '4px',
                      backgroundColor: box.confidence < 60 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                      border: `1px solid ${box.confidence < 60 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
                      fontSize: '0.8rem',
                      fontFamily: 'var(--mono)',
                      ...getWordStyle(box.confidence)
                    }}
                  >
                    {box.text} ({Math.round(box.confidence)}%)
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </Card>
  );
}
