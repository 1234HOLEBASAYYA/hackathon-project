import React from 'react';
import Card from '../common/Card';

export default function ConfidenceGauge({ ocrConfidence, preprocessConfidence }) {
  const roundedOCR = Math.round(ocrConfidence || 0);
  const roundedPrep = Math.round(preprocessConfidence || 0);
  const average = Math.round((roundedOCR + roundedPrep) / 2);

  const getQualityText = (val) => {
    if (val >= 80) return { text: 'EXCELLENT', color: 'var(--accent-success)' };
    if (val >= 60) return { text: 'ACCEPTABLE', color: 'var(--accent-warning)' };
    return { text: 'CRITICAL', color: 'var(--accent-danger)' };
  };

  const ocrQuality = getQualityText(roundedOCR);
  const prepQuality = getQualityText(roundedPrep);

  // SVG Gauge calculations
  const radius = 50;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (average / 100) * circumference;

  return (
    <Card title="Pipeline Confidence Auditing">
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', padding: '10px 0' }}>
        
        {/* SVG Ring */}
        <div style={{ position: 'relative', width: '130px', height: '130px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <svg height="130" width="130" style={{ transform: 'rotate(-90deg)' }}>
            {/* Background Circle */}
            <circle
              stroke="rgba(43, 100, 117, 0.1)"
              fill="transparent"
              strokeWidth={stroke}
              r={normalizedRadius}
              cx="65"
              cy="65"
            />
            {/* Foreground Circle */}
            <circle
              stroke={ocrQuality.color}
              fill="transparent"
              strokeWidth={stroke}
              strokeDasharray={circumference + ' ' + circumference}
              style={{ strokeDashoffset, transition: 'stroke-dashoffset 0.5s ease-in-out' }}
              r={normalizedRadius}
              cx="65"
              cy="65"
              strokeLinecap="round"
            />
          </svg>
          
          {/* Central Percent */}
          <div style={{
            position: 'absolute',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'var(--font-title)', color: 'var(--text-primary)', lineHeight: '1' }}>
              {average}%
            </span>
            <span style={{ fontSize: '0.6rem', fontWeight: 700, color: 'var(--text-secondary)', letterSpacing: '0.05em', marginTop: '2px' }}>
              OVERALL
            </span>
          </div>
        </div>

        {/* Detailed Breakdown */}
        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
          <div className="flex-between">
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>OCR Text Recognition</span>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginRight: '6px' }}>{roundedOCR}%</span>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: ocrQuality.color, backgroundColor: `${ocrQuality.color}15`, padding: '2px 6px', borderRadius: '4px' }}>
                {ocrQuality.text}
              </span>
            </div>
          </div>

          <div className="flex-between">
            <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Image Quality Metrics</span>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', marginRight: '6px' }}>{roundedPrep}%</span>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: prepQuality.color, backgroundColor: `${prepQuality.color}15`, padding: '2px 6px', borderRadius: '4px' }}>
                {prepQuality.text}
              </span>
            </div>
          </div>
        </div>

      </div>
    </Card>
  );
}
