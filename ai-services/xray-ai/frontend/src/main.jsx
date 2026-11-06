import React, { StrictMode, Component } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#f8fafc',
          padding: '24px',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <div style={{
            maxWidth: '600px',
            width: '100%',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e2e8f0',
            padding: '32px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)'
          }}>
            <div style={{
              display: 'inline-flex',
              padding: '8px 12px',
              backgroundColor: '#fee2e2',
              color: '#b91c1c',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '12px',
              marginBottom: '16px'
            }}>
              Runtime Application Alert
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a', margin: '0 0 8px 0' }}>
              Interface Render Exception
            </h2>
            <p style={{ fontSize: '14px', color: '#64748b', lineHeight: 1.5, margin: '0 0 20px 0' }}>
              The application encountered an unexpected state while rendering. The error has been captured safely.
            </p>
            <div style={{
              backgroundColor: '#0f172a',
              color: '#f8fafc',
              padding: '16px',
              borderRadius: '8px',
              fontFamily: 'monospace',
              fontSize: '12px',
              overflowX: 'auto',
              marginBottom: '24px'
            }}>
              {this.state.error?.toString() || "Unknown error"}
            </div>
            <button
              onClick={this.handleReset}
              style={{
                backgroundColor: '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '6px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Reset & Reload Application
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
)
