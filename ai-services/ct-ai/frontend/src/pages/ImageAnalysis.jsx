import React, { useState } from 'react';
import ImageUploader from '../components/ImageUploader';
import PredictionCard from '../components/PredictionCard';
import GradCAMViewer from '../components/GradCAMViewer';
import Sidebar from '../components/Sidebar';
import LoadingSpinner from '../components/LoadingSpinner';
import { analyzeImage, getSampleAnalysis } from '../services/api';
import { Sparkles, AlertCircle } from 'lucide-react';

export default function ImageAnalysis() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [rawImageBase64, setRawImageBase64] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleAnalyze = async (file) => {
    if (!file) return;
    setIsAnalyzing(true);
    setErrorMessage(null);

    // Convert file to base64 for preview in GradCAMViewer
    const reader = new FileReader();
    reader.onload = (e) => setRawImageBase64(e.target.result);
    reader.readAsDataURL(file);

    try {
      const data = await analyzeImage(file);
      setAnalysisResult(data);
    } catch (err) {
      console.error('Analysis failed:', err);
      setErrorMessage(err.message || 'Failed to analyze radiograph. Please ensure backend server is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLoadSample = async (category) => {
    setIsAnalyzing(true);
    setErrorMessage(null);
    setAnalysisResult(null);

    try {
      const data = await getSampleAnalysis(category);
      setAnalysisResult(data);
      // For sample, if overlay is present we can use overlay or placeholder
      if (data.gradcam?.overlay_b64) {
        setRawImageBase64(data.gradcam.overlay_b64);
      }
    } catch (err) {
      console.error('Failed to load sample:', err);
      setErrorMessage(err.message || `Failed to load sample ${category} scan.`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div style={{
      maxWidth: '1440px',
      margin: '0 auto',
      display: 'grid',
      gridTemplateColumns: '320px 1fr',
      gap: '2rem',
      paddingBottom: '3rem'
    }}>
      {/* Left Sidebar */}
      <Sidebar onLoadSample={handleLoadSample} isAnalyzing={isAnalyzing} />

      {/* Main Analysis Workspace */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
        {/* Error Notification */}
        {errorMessage && (
          <div style={{
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            borderRadius: '12px',
            padding: '1rem 1.25rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            color: '#f87171',
            fontSize: '0.9rem'
          }}>
            <AlertCircle size={20} />
            <span>{errorMessage}</span>
          </div>
        )}

        {/* Uploader */}
        <ImageUploader
          onAnalyze={handleAnalyze}
          isAnalyzing={isAnalyzing}
          selectedFile={selectedFile}
          setSelectedFile={setSelectedFile}
        />

        {/* Loading Spinner */}
        {isAnalyzing && (
          <div className="glass-panel">
            <LoadingSpinner message="Executing PyTorch ResNet-18 forward pass & generating Grad-CAM heatmaps..." />
          </div>
        )}

        {/* Results Section */}
        {analysisResult && !isAnalyzing && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
            <PredictionCard result={analysisResult} />
            {analysisResult.gradcam && (
              <GradCAMViewer gradcam={analysisResult.gradcam} rawImage={rawImageBase64} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
