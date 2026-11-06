import React from 'react';
import { Sliders, Eye, EyeOff, BrainCircuit, Key } from 'lucide-react';
import Card from '../common/Card';

export function PreprocessingSandbox({ config, onChange, onReset }) {
  const handleConfigChange = (key, value) => {
    onChange({
      ...config,
      [key]: value
    });
  };

  // Preprocessing Presets
  const applyPreset = (preset) => {
    if (preset === 'default') {
      onReset();
    } else if (preset === 'low-contrast') {
      onChange({
        ...config,
        clahe_clip_limit: 4.0,
        adaptive_block_size: 15,
        adaptive_c: 4,
      });
    } else if (preset === 'high-noise') {
      onChange({
        ...config,
        denoise: true,
        adaptive_block_size: 9,
        adaptive_c: 1,
      });
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
        <button onClick={() => applyPreset('default')} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', flex: 1 }}>Default Preset</button>
        <button onClick={() => applyPreset('low-contrast')} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', flex: 1 }}>Boost Contrast</button>
        <button onClick={() => applyPreset('high-noise')} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem', flex: 1 }}>Denoise Focused</button>
      </div>

      {/* Sliders */}
      <div className="slider-container">
        <div className="slider-header">
          <span className="form-label" style={{ margin: 0 }}>Target Resize Width</span>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>{config.resize_width} px</span>
        </div>
        <input
          type="range"
          min="1000"
          max="2500"
          step="100"
          value={config.resize_width}
          onChange={(e) => handleConfigChange('resize_width', parseInt(e.target.value))}
          className="slider-control"
        />
      </div>

      <div className="slider-container">
        <div className="slider-header">
          <span className="form-label" style={{ margin: 0 }}>CLAHE Contrast Clip Limit</span>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>{config.clahe_clip_limit.toFixed(1)}</span>
        </div>
        <input
          type="range"
          min="1.0"
          max="8.0"
          step="0.5"
          value={config.clahe_clip_limit}
          onChange={(e) => handleConfigChange('clahe_clip_limit', parseFloat(e.target.value))}
          className="slider-control"
        />
      </div>

      <div className="slider-container">
        <div className="slider-header">
          <span className="form-label" style={{ margin: 0 }}>Adaptive Threshold Block Size</span>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>{config.adaptive_block_size} px</span>
        </div>
        <input
          type="range"
          min="3"
          max="31"
          step="2"
          value={config.adaptive_block_size}
          onChange={(e) => handleConfigChange('adaptive_block_size', parseInt(e.target.value))}
          className="slider-control"
        />
      </div>

      <div className="slider-container">
        <div className="slider-header">
          <span className="form-label" style={{ margin: 0 }}>Adaptive Threshold C</span>
          <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>{config.adaptive_c}</span>
        </div>
        <input
          type="range"
          min="-10"
          max="15"
          step="1"
          value={config.adaptive_c}
          onChange={(e) => handleConfigChange('adaptive_c', parseInt(e.target.value))}
          className="slider-control"
        />
      </div>

      {/* Toggles */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '10px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.denoise}
            onChange={(e) => handleConfigChange('denoise', e.target.checked)}
            style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
          />
          <span>Enable Non-Local Means Denoising</span>
        </label>

        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.deskew}
            onChange={(e) => handleConfigChange('deskew', e.target.checked)}
            style={{ width: '16px', height: '16px', accentColor: 'var(--accent-primary)' }}
          />
          <span>Enable Auto Deskew Correction</span>
        </label>
      </div>
    </div>
  );
}

export function LLMConfigPanel({ llmConfig, onLLMChange }) {
  const handleLLMChange = (key, value) => {
    onLLMChange({
      ...llmConfig,
      [key]: value
    });
  };

  return (
    <Card title="LLM Post-Processing Refinement" subtitle="Use advanced LLM endpoints to correct spelling and reconstruct structured entities.">
      <label className="checkbox-label" style={{ marginBottom: '20px' }}>
        <input
          type="checkbox"
          checked={llmConfig.enabled}
          onChange={(e) => handleLLMChange('enabled', e.target.checked)}
          style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)' }}
        />
        <span style={{ display: 'flex', alignItems: 'center', gap: '8px', color: llmConfig.enabled ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
          <BrainCircuit size={18} />
          Enable LLM Post-Processing Layer
        </span>
      </label>

      {llmConfig.enabled && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', animation: 'slide-down 0.25s ease-out' }}>
          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Extraction Pipeline Mode</label>
            <select
              value={llmConfig.mode || 'ocr_refinement'}
              onChange={(e) => {
                const mode = e.target.value;
                handleLLMChange('mode', mode);
                if (mode === 'direct_vision' && llmConfig.provider === 'nvidia') {
                  handleLLMChange('provider', 'openai');
                  handleLLMChange('model', 'gpt-4o-mini');
                } else if (llmConfig.provider === 'ollama') {
                  handleLLMChange('model', mode === 'direct_vision' ? 'llama3.2-vision' : 'llama3.2');
                }
              }}
              className="form-control"
              style={{ backgroundColor: 'var(--bg-primary)' }}
            >
              <option value="ocr_refinement">OCR + LLM Text Refinement (Hybrid)</option>
              <option value="direct_vision">Direct Vision LLM Extraction (No OCR)</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">API Provider</label>
            <select
              value={llmConfig.provider}
              onChange={(e) => {
                const provider = e.target.value;
                handleLLMChange('provider', provider);
                let defaultModel = 'gpt-4o-mini';
                if (provider === 'nvidia') defaultModel = 'meta/llama-3.1-70b-instruct';
                else if (provider === 'ollama') defaultModel = (llmConfig.mode === 'direct_vision' ? 'llama3.2-vision' : 'llama3.2');
                handleLLMChange('model', defaultModel);
              }}
              className="form-control"
              style={{ backgroundColor: 'var(--bg-primary)' }}
            >
              <option value="openai">OpenAI API</option>
              {llmConfig.mode !== 'direct_vision' && <option value="nvidia">NVIDIA NIM (Meta Llama 3.1)</option>}
              <option value="ollama">Ollama (Local Offline)</option>
            </select>
          </div>

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">Model Endpoint</label>
            <input
              type="text"
              value={llmConfig.model}
              onChange={(e) => handleLLMChange('model', e.target.value)}
              placeholder={
                llmConfig.provider === 'openai' 
                  ? 'gpt-4o-mini' 
                  : llmConfig.provider === 'nvidia' 
                    ? 'meta/llama-3.1-70b-instruct' 
                    : llmConfig.mode === 'direct_vision' 
                      ? 'llama3.2-vision' 
                      : 'llama3.2'
              }
              className="form-control"
            />
          </div>

          {llmConfig.provider !== 'ollama' ? (
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Key size={14} /> API Key
              </label>
              <input
                type="password"
                value={llmConfig.api_key}
                onChange={(e) => handleLLMChange('api_key', e.target.value)}
                placeholder={`Enter your ${llmConfig.provider === 'openai' ? 'OpenAI' : 'NVIDIA NIM'} API Key`}
                className="form-control"
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Your key is processed securely in transit and is never stored on disk.
              </span>
            </div>
          ) : (
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Local Ollama API Base URL</label>
              <input
                type="text"
                value={llmConfig.api_url || 'http://localhost:11434/v1'}
                onChange={(e) => handleLLMChange('api_url', e.target.value)}
                placeholder="http://localhost:11434/v1"
                className="form-control"
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
                Ensure Ollama is running locally with CORS enabled (`OLLAMA_ORIGINS=*`).
              </span>
            </div>
          )}

          <div className="form-group" style={{ margin: 0 }}>
            <label className="form-label">
              Patient Symptoms / Clinical Context
            </label>
            <textarea
              value={llmConfig.clinical_context || ''}
              onChange={(e) => handleLLMChange('clinical_context', e.target.value)}
              placeholder="e.g. Patient has acute bronchitis, dry cough and fever"
              className="form-control"
              rows={2}
              style={{ resize: 'none' }}
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>
              Helps the LLM disambiguate poor handwriting using clinical relevance.
            </span>
          </div>

          <div className="slider-container" style={{ margin: 0 }}>
            <div className="slider-header">
              <span className="form-label" style={{ margin: 0 }}>Temperature</span>
              <span style={{ color: 'var(--accent-primary)', fontWeight: 700 }}>{llmConfig.temperature || 0.1}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={llmConfig.temperature || 0.1}
              onChange={(e) => handleLLMChange('temperature', parseFloat(e.target.value))}
              className="slider-control"
            />
          </div>
        </div>
      )}
    </Card>
  );
}

// Default export wrapper to prevent breaking changes if imported blindly
export default function ParameterSliders({ config, onChange, llmConfig, onLLMChange, onReset }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <Card title="Image Preprocessing Sandbox" subtitle="Tweak OpenCV image optimization parameters in real time.">
        <PreprocessingSandbox config={config} onChange={onChange} onReset={onReset} />
      </Card>
      <LLMConfigPanel llmConfig={llmConfig} onLLMChange={onLLMChange} />
    </div>
  );
}
