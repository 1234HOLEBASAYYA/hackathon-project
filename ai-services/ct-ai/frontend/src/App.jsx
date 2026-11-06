import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import ImageAnalysis from './pages/ImageAnalysis';
import CTScanAnalysis from './pages/CTScanAnalysis';
import DoctorDashboard from './pages/DoctorDashboard';
import PatientDashboard from './pages/PatientDashboard';
import PrescriptionAnalysis from './pages/PrescriptionAnalysis';
import { Activity, ShieldCheck, Heart } from 'lucide-react';

export default function App() {
  const [activePage, setActivePage] = useState('ct-scan');

  const renderPage = () => {
    switch (activePage) {
      case 'ct-scan':
        return <CTScanAnalysis />;
      case 'home':
        return <Home setActivePage={setActivePage} />;
      case 'image-analysis':
        return <ImageAnalysis />;
      case 'doctor':
        return <DoctorDashboard />;
      case 'patient':
        return <PatientDashboard />;
      case 'prescriptions':
        return <PrescriptionAnalysis />;
      default:
        return <CTScanAnalysis />;
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      <main style={{ flex: 1, padding: '2rem 1.5rem', width: '100%', boxSizing: 'border-box' }}>
        {renderPage()}
      </main>

      <footer style={{
        borderTop: '1px solid var(--border-color)',
        padding: '1.5rem 2rem',
        background: 'rgba(10, 15, 29, 0.95)',
        textAlign: 'center',
        fontSize: '0.8rem',
        color: '#64748b'
      }}>
        <div style={{
          maxWidth: '1280px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={16} color="#38bdf8" />
            <span style={{ color: '#94a3b8', fontWeight: 600 }}>PneumoScan AI Prototype</span>
            <span>• Transfer Learning ResNet-18</span>
          </div>

          <div>
            Built with PyTorch, FastAPI, React & Vite for Medical Image Abnormality Detection
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#94a3b8' }}>
            <span>Clinical AI Decision Support</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
