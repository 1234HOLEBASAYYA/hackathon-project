import React from 'react';
import { FileText, CheckCircle, RefreshCw, Download, AlertTriangle, Eye } from 'lucide-react';
import Card from '../common/Card';

export default function BatchQueue({ items, onSelectItem, onDownloadJSON, onDownloadTXT }) {
  if (!items || items.length === 0) return null;

  const totalCount = items.length;
  const completedCount = items.filter(item => item.status === 'success' || item.status === 'failed').length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <Card 
      title="Asynchronous Batch Processing Queue" 
      subtitle={`Track background OCR processes. Completed: ${completedCount} / ${totalCount}`}
    >
      {/* Aggregated Progress Bar */}
      <div style={{ marginBottom: '20px' }}>
        <div className="flex-between" style={{ marginBottom: '6px', fontSize: '0.85rem' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Batch Progress</span>
          <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>{progressPercent}%</span>
        </div>
        <div style={{ width: '100%', height: '8px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
          <div style={{
            width: `${progressPercent}%`,
            height: '100%',
            background: 'linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%)',
            transition: 'width 0.4s ease'
          }} />
        </div>
      </div>

      {/* Action Buttons for Aggregated Results */}
      {completedCount === totalCount && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <button onClick={onDownloadJSON} className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <Download size={14} /> Download Batch JSON
          </button>
          <button onClick={onDownloadTXT} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <Download size={14} /> Download Summary TXT
          </button>
        </div>
      )}

      {/* Queue Items List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '300px', overflowY: 'auto', paddingRight: '4px' }}>
        {items.map((item) => (
          <div 
            key={item.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              backgroundColor: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              transition: 'background-color 0.2s'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
              <div style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
                <FileText size={18} />
              </div>
              <div style={{ minWidth: 0 }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {item.filename}
                </p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  {(item.file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
              {/* Status Badge */}
              {item.status === 'queued' && (
                <span className="badge badge-primary" style={{ opacity: 0.6 }}>Queued</span>
              )}
              {item.status === 'processing' && (
                <span className="badge badge-primary" style={{ animation: 'pulse 1s infinite alternate' }}>
                  <RefreshCw size={10} className="spin" style={{ animation: 'spin 1s linear infinite' }} /> Processing
                </span>
              )}
              {item.status === 'success' && (
                <span className="badge badge-success">
                  <CheckCircle size={10} /> Success
                </span>
              )}
              {item.status === 'failed' && (
                <span className="badge badge-danger" title={item.error}>
                  <AlertTriangle size={10} /> Failed
                </span>
              )}

              {/* View Results Button */}
              {item.status === 'success' && item.result && (
                <button 
                  onClick={() => onSelectItem(item)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    color: 'var(--accent-primary)',
                    display: 'flex',
                    alignItems: 'center',
                    padding: '4px',
                    borderRadius: '4px',
                    transition: 'background-color 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(101, 184, 181, 0.14)'}
                  onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <Eye size={16} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}} />
    </Card>
  );
}
