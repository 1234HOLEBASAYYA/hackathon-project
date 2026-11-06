import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Upload, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  Download, 
  Layers, 
  Database, 
  ShieldAlert, 
  BarChart3, 
  Info,
  ChevronRight,
  Eye,
  RefreshCw,
  Cpu
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('analyze');
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [samples, setSamples] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [datasetsInfo, setDatasetsInfo] = useState(null);
  const [health, setHealth] = useState(null);

  // Load samples, metrics, datasets, health on mount
  useEffect(() => {
    fetchHealth();
    fetchSamples();
    fetchMetrics();
    fetchDatasets();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch('/api/health');
      if (res.ok) setHealth(await res.json());
    } catch (e) {
      console.warn("Health check failed:", e);
    }
  };

  const fetchSamples = async () => {
    try {
      const res = await fetch('/api/samples');
      if (res.ok) {
        const data = await res.json();
        setSamples(data.samples || []);
      }
    } catch (e) {
      console.warn("Failed to load samples:", e);
    }
  };

  const fetchMetrics = async () => {
    try {
      const res = await fetch('/api/metrics');
      if (res.ok) setMetrics(await res.json());
    } catch (e) {
      console.warn("Failed to load metrics:", e);
    }
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch('/api/datasets');
      if (res.ok) setDatasetsInfo(await res.json());
    } catch (e) {
      console.warn("Failed to load datasets:", e);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

  const handleSelectSample = async (sample) => {
    try {
      setAnalyzing(true);
      setError(null);
      setResult(null);
      setPreviewUrl(sample.image_url);
      
      const res = await fetch(sample.image_url);
      if (!res.ok) throw new Error(`Could not load sample image from server (${res.status})`);
      const blob = await res.blob();
      const sampleFile = new File([blob], sample.filename || "sample.jpg", { type: blob.type || 'image/jpeg' });
      setFile(sampleFile);
      
      // Auto analyze sample
      await executeAnalysis(sampleFile);
    } catch (e) {
      console.error("Failed to load sample:", e);
      setError(`Failed to load sample: ${e.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  const executeAnalysis = async (fileToUpload) => {
    const uploadTarget = fileToUpload || file;
    if (!uploadTarget) return;

    setAnalyzing(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append('file', uploadTarget);

      const res = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      console.log("Received AI Analysis Data:", data);
      setResult(data);
    } catch (e) {
      console.error("Execution error:", e);
      setError(e.message || "An unexpected error occurred during radiograph analysis.");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
      {/* Top Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-md bg-sky-700 flex items-center justify-center text-white">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-slate-900 leading-tight">
                Antigravity Multi-Region X-Ray Analysis AI
              </h1>
              <p className="text-xs text-slate-500">
                Two-Stage Anatomical Damage Localization & Pathology Platform
              </p>
            </div>
          </div>

          {/* Engine Status Badge */}
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex items-center text-xs text-slate-600 bg-slate-100 px-2.5 py-1 rounded border border-slate-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
              ResNet-18 Router + MSK Detector + DenseNet-121 Online
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex space-x-1 overflow-x-auto border-t border-slate-100 text-sm">
          {[
            { id: 'analyze', label: 'Upload & Analysis', icon: Upload },
            { id: 'metrics', label: 'Model Performance & Accuracy', icon: BarChart3 },
            { id: 'regions', label: 'Supported Regions', icon: Layers },
            { id: 'datasets', label: 'Datasets & Provenance', icon: Database },
            { id: 'architecture', label: 'System Architecture', icon: Cpu },
            { id: 'disclaimer', label: 'Medical Disclaimer', icon: ShieldAlert },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-3 px-3.5 border-b-2 font-medium transition-colors whitespace-nowrap ${
                  active
                    ? 'border-sky-600 text-sky-700'
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {/* TAB 1: UPLOAD & ANALYSIS */}
        {activeTab === 'analyze' && (
          <div className="space-y-8 fade-in">
            {/* Quick Hero Banner */}
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <div className="max-w-3xl">
                <h2 className="text-xl font-bold text-slate-900 mb-2">
                  Clinical Radiograph Analysis & Damage Localization
                </h2>
                <p className="text-sm text-slate-600 mb-4 leading-relaxed">
                  Upload an X-ray to initiate our two-stage AI cascade. Stage 1 routes the radiograph by anatomical region,
                  and Stage 2 executes specialized damage localization with exact bounding boxes, affected bone identification,
                  and cardiopulmonary pathology screening.
                </p>
                <div className="flex flex-wrap gap-2 text-xs text-slate-600">
                  <span className="bg-slate-100 px-2 py-1 rounded border border-slate-200">Supported: Wrist, Hand, Leg, Hip, Shoulder, Chest</span>
                  <span className="bg-slate-100 px-2 py-1 rounded border border-slate-200">Formats: PNG, JPG, JPEG, DICOM</span>
                  <span className="bg-amber-50 text-amber-800 px-2 py-1 rounded border border-amber-200">Non-Diagnostic Research Aid</span>
                </div>
              </div>
            </div>

            {/* Quick-Test Sample Radiographs */}
            {samples.length > 0 && (
              <div className="bg-white border border-slate-200 rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-900 flex items-center space-x-2">
                    <Eye className="w-4 h-4 text-sky-600" />
                    <span>Quick-Test Verified Sample Radiographs (Held-out Test Cohort)</span>
                  </h3>
                  <span className="text-xs text-slate-400">Click any specimen to run immediate analysis</span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                  {samples.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSelectSample(s)}
                      className="border border-slate-200 hover:border-sky-500 rounded p-2 text-left bg-slate-50 hover:bg-sky-50 transition-colors flex flex-col group"
                    >
                      <div className="w-full h-24 bg-slate-900 rounded overflow-hidden mb-2 relative">
                        <img 
                          src={s.image_url} 
                          alt={s.anatomical_region} 
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform" 
                        />
                      </div>
                      <div className="text-xs font-bold text-slate-900 capitalize truncate">
                        {s.anatomical_region}
                      </div>
                      <div className="text-[10px] text-slate-500 truncate">
                        {s.dataset_source}
                      </div>
                      <div className={`text-[10px] font-semibold mt-1 ${s.fracture_status === 'Fractured' ? 'text-red-600' : 'text-emerald-600'}`}>
                        {s.fracture_status}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Upload Box & Results Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Upload Controls */}
              <div className="lg:col-span-4 space-y-4">
                <div className="bg-white border border-slate-200 rounded-lg p-5">
                  <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center space-x-2">
                    <Upload className="w-4 h-4 text-sky-600" />
                    <span>Upload X-Ray Radiograph</span>
                  </h3>

                  <label className="border-2 border-dashed border-slate-300 hover:border-sky-500 rounded-lg p-6 flex flex-col items-center justify-center cursor-pointer bg-slate-50 hover:bg-slate-100 transition-colors">
                    <Upload className="w-8 h-8 text-slate-400 mb-2" />
                    <span className="text-xs font-semibold text-slate-700">Select file or drop here</span>
                    <span className="text-[11px] text-slate-400 mt-1">PNG, JPG, DICOM (max 25MB)</span>
                    <input type="file" onChange={handleFileChange} accept=".png,.jpg,.jpeg,.dcm,.dicom" className="hidden" />
                  </label>

                  {previewUrl && (
                    <div className="mt-4">
                      <div className="text-xs font-medium text-slate-500 mb-1">Selected Radiograph:</div>
                      <div className="w-full max-h-64 bg-slate-950 rounded-lg overflow-hidden flex items-center justify-center p-2 border border-slate-200">
                        <img src={previewUrl} alt="Preview" className="max-h-60 object-contain" />
                      </div>
                    </div>
                  )}

                  <button
                    disabled={!file || analyzing}
                    onClick={() => executeAnalysis()}
                    className={`w-full mt-4 py-2.5 px-4 rounded font-medium text-sm text-white flex items-center justify-center space-x-2 transition-colors ${
                      !file || analyzing ? 'bg-slate-300 cursor-not-allowed' : 'bg-sky-700 hover:bg-sky-800'
                    }`}
                  >
                    {analyzing ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Running Multi-Stage Pipeline...</span>
                      </>
                    ) : (
                      <>
                        <Activity className="w-4 h-4" />
                        <span>Run AI Analysis</span>
                      </>
                    )}
                  </button>

                  {error && (
                    <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-xs text-red-700 flex items-start space-x-2">
                      <AlertTriangle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
                      <div>{error}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column: Analysis Results */}
              <div className="lg:col-span-8">
                {result ? (
                  result.is_radiograph === false || result.status === "not_an_xray" ? (
                    /* Not an X-Ray Rejection Card */
                    <div className="bg-white border-2 border-red-200 rounded-lg p-6 space-y-5">
                      <div className="flex items-start space-x-3 border-b border-red-100 pb-4">
                        <div className="w-11 h-11 rounded-lg bg-red-100 flex items-center justify-center text-red-700 shrink-0">
                          <ShieldAlert className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <span className="text-xs font-bold uppercase tracking-wider text-red-700 bg-red-50 px-2 py-0.5 rounded border border-red-200">
                            Input Rejection: Not a Medical Radiograph
                          </span>
                          <h3 className="text-lg font-bold text-slate-900 mt-1">
                            Uploaded File is Not an X-Ray Image
                          </h3>
                          <div className="mt-2 inline-flex items-center space-x-2 bg-slate-100 text-slate-800 text-xs px-2.5 py-1 rounded font-medium border border-slate-200">
                            <span>Detected Input Type:</span>
                            <span className="font-bold text-red-700">{result.detected_image_type || "Standard photograph / graphic"}</span>
                          </div>
                          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                            {result.warning || "The uploaded image does not appear to be an authentic medical radiograph displaying bone radiodensity or projection anatomy."}
                          </p>
                        </div>
                      </div>

                      {result.clinical_summary && (
                        <div className="bg-slate-50 border border-slate-200 rounded p-4 text-xs space-y-2">
                          <div className="font-bold text-slate-900">Image Verification Observations:</div>
                          {Array.isArray(result.clinical_summary.key_takeaways) && (
                            <ul className="list-disc list-inside text-slate-600 space-y-1">
                              {result.clinical_summary.key_takeaways.map((point, idx) => (
                                <li key={idx}>{point}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      )}

                      <div className="bg-amber-50 border border-amber-200 rounded p-4 text-xs space-y-1.5 text-amber-950">
                        <div className="font-bold text-amber-900 flex items-center space-x-1.5">
                          <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
                          <span>Medical Quality & Integrity Policy:</span>
                        </div>
                        <p className="text-amber-900 leading-relaxed">
                          To prevent false or misleading diagnostic assertions, this platform strictly evaluates genuine medical projection radiographs
                          (X-rays, fluoroscopy, DICOM studies). Non-radiographic photographs (such as selfies, pets, nature, or graphics) are
                          deliberately rejected and no bone or pulmonary findings are generated.
                        </p>
                        <div className="text-[11px] text-amber-800 pt-1 border-t border-amber-200 font-medium">
                          <b>Required Format:</b> Please upload an authentic medical X-ray of a body region (Chest, Hand, Wrist, Foot, Leg, Knee, Hip, Shoulder, etc.) in PNG, JPG, or DICOM format.
                        </div>
                      </div>
                    </div>
                  ) : result.supported === false || result.status === "unsupported_region" ? (
                    /* Unsupported / Out-of-Distribution Gating Card */
                    <div className="bg-white border border-amber-200 rounded-lg p-6 space-y-5">
                      <div className="flex items-start space-x-3 border-b border-amber-100 pb-4">
                        <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700 shrink-0">
                          <AlertTriangle className="w-6 h-6" />
                        </div>
                        <div className="flex-1">
                          <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Stage 1 Gating: Out-of-Distribution Rejection
                          </span>
                          <h3 className="text-lg font-bold text-slate-900 mt-1">
                            Unsupported or Ambiguous Anatomical Region
                          </h3>
                          <p className="text-xs text-slate-600 mt-1 leading-relaxed">
                            {result.warning || "The uploaded image did not match any of our validated anatomical regions with sufficient diagnostic confidence (threshold &ge; 50.0%)."}
                          </p>
                        </div>
                      </div>

                      <div className="bg-slate-50 border border-slate-200 rounded p-4">
                        <div className="text-xs font-semibold text-slate-700 mb-2">Stage 1 Anatomical Region Probability Breakdown:</div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                          {Object.entries(result.all_region_probabilities || {}).map(([reg, prob]) => (
                            <div key={reg} className="bg-white p-2 rounded border border-slate-200 text-xs flex justify-between items-center">
                              <span className="capitalize font-medium text-slate-700">{reg}:</span>
                              <span className="font-mono font-bold text-slate-900">{(Number(prob || 0) * 100).toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-sky-50 border border-sky-200 rounded p-4 text-xs space-y-1.5 text-sky-950">
                        <div className="font-bold text-sky-900 flex items-center space-x-1.5">
                          <ShieldAlert className="w-4 h-4 text-sky-700 shrink-0" />
                          <span>Clinical Safety Protocol Enforced:</span>
                        </div>
                        <p className="text-sky-900 leading-relaxed">
                          In strict accordance with medical AI safety guidelines, Stage 2 damage localization models were deliberately withheld
                          to avoid generating false positive annotations on an unverified anatomical region.
                        </p>
                        <div className="text-[11px] text-sky-800 pt-1 border-t border-sky-200 font-medium">
                          Supported Regions: <b>Wrist, Hand, Leg, Hip, Shoulder, Chest</b>. Please ensure your image is a clear radiograph in PNG, JPG, or DICOM format.
                        </div>
                      </div>
                    </div>
                  ) : (
                    /* Supported Analysis Result View */
                    <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-6">
                      {/* Header Result Bar */}
                      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
                        <div>
                          <div className="text-xs uppercase font-bold text-slate-400">Analysis Completed</div>
                          <div className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                            <span>{String(result.anatomical_region || 'Unknown').toUpperCase()} RADIOGRAPH</span>
                            <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                              result.is_abnormal ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
                            }`}>
                              {result.is_abnormal ? 'ABNORMALITY / FRACTURE DETECTED' : 'NORMAL / NO ACUTE LESION'}
                            </span>
                          </div>
                          <div className="text-xs text-slate-500 mt-0.5">
                            Inference Pipeline: {result.pipeline_name || "Neural Cascade"} | ID: {result.analysis_id || "N/A"}
                          </div>
                        </div>

                        {result.pdf_report_url && (
                          <a
                            href={result.pdf_report_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center space-x-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold py-2 px-3 rounded transition-colors"
                          >
                            <Download className="w-4 h-4" />
                            <span>Download PDF Report</span>
                          </a>
                        )}
                      </div>

                      {/* Stage 1 & Stage 2 Metric Cards */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-slate-50 border border-slate-200 rounded p-3">
                          <div className="text-[11px] font-semibold text-slate-500 uppercase">Stage 1: Region Confidence</div>
                          <div className="text-xl font-bold text-slate-900 mt-1">
                            {(Number(result.region_confidence ?? result.confidence ?? 0) * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-slate-600 mt-0.5 capitalize">
                            Identified as: <b>{result.anatomical_region || "Unknown"}</b>
                          </div>
                        </div>

                        <div className="bg-slate-50 border border-slate-200 rounded p-3">
                          <div className="text-[11px] font-semibold text-slate-500 uppercase">Stage 2: Model Confidence</div>
                          <div className="text-xl font-bold text-slate-900 mt-1">
                            {(Number(result.confidence ?? 0) * 100).toFixed(1)}%
                          </div>
                          <div className="text-xs text-slate-600 mt-0.5">
                            Status: <b>{result.is_abnormal ? 'Focal lesion localized' : 'Normal alignment'}</b>
                          </div>
                        </div>

                        <div className="bg-slate-50 border border-slate-200 rounded p-3">
                          <div className="text-[11px] font-semibold text-slate-500 uppercase">Affected Bone Structure</div>
                          <div className="text-base font-bold text-slate-900 mt-1 capitalize truncate">
                            {result.affected_bone && result.affected_bone !== "N/A"
                              ? String(result.affected_bone).replace(/_/g, " ")
                              : "Intact Cortical Outline"}
                          </div>
                          <div className="text-xs text-slate-600 mt-0.5">
                            Displacement: <b>{result.displacement_assessment || "N/A"}</b>
                          </div>
                        </div>
                      </div>

                      {/* Side-by-Side Damage Localization Specimen */}
                      {result.visual_specimen_url && (
                        <div className="border border-slate-200 rounded-lg overflow-hidden bg-slate-950">
                          <div className="bg-slate-900 px-4 py-2 text-xs font-semibold text-slate-300 flex items-center justify-between">
                            <span>Side-by-Side Anatomical Damage Specimen</span>
                            <span className="text-[10px] text-slate-400">Left: Raw Image | Right: AI Damage Localization</span>
                          </div>
                          <div className="p-2 flex justify-center">
                            <img
                              src={result.visual_specimen_url}
                              alt="Damage Localization"
                              className="max-h-[460px] object-contain rounded"
                            />
                          </div>
                        </div>
                      )}

                      {/* Findings Table */}
                      <div>
                        <h4 className="text-xs font-bold text-slate-900 uppercase mb-2">Detected Pathologies & Findings</h4>
                        <div className="border border-slate-200 rounded-lg overflow-hidden">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-slate-100 border-b border-slate-200 text-slate-700">
                              <tr>
                                <th className="py-2.5 px-3 font-semibold">Finding Description</th>
                                <th className="py-2.5 px-3 font-semibold">Target Bone / Anatomy</th>
                                <th className="py-2.5 px-3 font-semibold">Confidence</th>
                                <th className="py-2.5 px-3 font-semibold">Damage Box Bounds</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200 bg-white">
                              {Array.isArray(result.findings) && result.findings.length > 0 ? (
                                result.findings.map((f, i) => (
                                  <tr key={i} className="hover:bg-slate-50">
                                    <td className="py-2.5 px-3 font-medium text-slate-900 flex items-center space-x-1.5">
                                      <span className={`w-2 h-2 rounded-full ${result.is_abnormal ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
                                      <span>{f.finding_type || "Observed finding"}</span>
                                    </td>
                                    <td className="py-2.5 px-3 text-slate-600 capitalize">
                                      {f.affected_bone ? String(f.affected_bone).replace(/_/g, " ") : "N/A"}
                                    </td>
                                    <td className="py-2.5 px-3 font-bold text-slate-900">
                                      {(Number(f.confidence ?? 0) * 100).toFixed(1)}%
                                    </td>
                                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">
                                      {Array.isArray(f.bbox_pixels) && f.bbox_pixels.length === 4
                                        ? `[${f.bbox_pixels.join(', ')}]`
                                        : 'None / Non-focal'}
                                    </td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan="4" className="py-4 text-center text-slate-500">
                                    No focal radiographic lesions localized.
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      </div>

                      {/* Educational Clinical Summary (Gemini / Verified Rules) */}
                      {result.clinical_summary && (
                        <div className="bg-sky-50 border border-sky-200 rounded-lg p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-sky-900 uppercase">
                              Clinical Narrative & Educational Explanation
                            </h4>
                            <span className="text-[10px] text-sky-700 bg-sky-100 px-2 py-0.5 rounded font-medium">
                              {result.clinical_summary.gemini_active ? "Powered by Google Gemini" : "Deterministic Clinical Rules Engine"}
                            </span>
                          </div>
                          <p className="text-xs text-sky-950 leading-relaxed">
                            {result.clinical_summary.summary}
                          </p>
                          {Array.isArray(result.clinical_summary.key_takeaways) && result.clinical_summary.key_takeaways.length > 0 && (
                            <ul className="list-disc list-inside text-xs text-sky-900 space-y-1 mt-2">
                              {result.clinical_summary.key_takeaways.map((point, idx) => (
                                <li key={idx}>{point}</li>
                              ))}
                            </ul>
                          )}
                          {result.clinical_summary.patient_guidance && (
                            <div className="text-[11px] font-semibold text-sky-800 pt-1 border-t border-sky-200">
                              Recommendation: {result.clinical_summary.patient_guidance}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Non-Diagnostic Disclaimer */}
                      <div className="p-3 bg-slate-50 border border-slate-200 rounded text-[11px] text-slate-600 flex items-start space-x-2">
                        <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                        <div>
                          <b>Mandatory Medical Disclaimer:</b> This AI platform provides probabilistic screening estimates for research
                          and educational purposes. Heatmaps, bounding boxes, and scores do NOT constitute a verified radiological diagnosis.
                          Consult a licensed medical doctor for clinical care.
                        </div>
                      </div>
                    </div>
                  )
                ) : (
                  <div className="bg-white border border-slate-200 rounded-lg p-12 text-center text-slate-500">
                    <Activity className="w-12 h-12 mx-auto text-slate-300 mb-3" />
                    <h3 className="text-base font-semibold text-slate-700">No Radiograph Analyzed Yet</h3>
                    <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                      Upload an X-ray using the left panel or click one of the verified sample specimens above to inspect AI damage localization.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: MODEL PERFORMANCE & ACCURACY */}
        {activeTab === 'metrics' && (
          <div className="space-y-6 fade-in">
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-1">
                Empirical Model Performance & Test Set Evaluations
              </h2>
              <p className="text-xs text-slate-600">
                All metrics below are computed on independent held-out test splits. We strictly do NOT invent accuracy percentages
                or report combined misleading scores.
              </p>
            </div>

            {metrics ? (
              <div className="space-y-6">
                {/* Stage 1: Router Metrics */}
                {metrics.anatomical_router && (
                  <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">
                          Stage 1: Anatomical Region Router (ResNet-18)
                        </h3>
                        <p className="text-xs text-slate-500">Evaluated on {metrics.anatomical_router.test_samples_count} held-out test radiographs</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-500">Overall Test Accuracy</span>
                        <div className="text-xl font-bold text-sky-700">
                          {(metrics.anatomical_router.overall_accuracy * 100).toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">Macro F1-Score</div>
                        <div className="text-lg font-bold text-slate-900">{metrics.anatomical_router.macro_f1}</div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">Weighted F1-Score</div>
                        <div className="text-lg font-bold text-slate-900">{metrics.anatomical_router.weighted_f1}</div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">Confidence Gate</div>
                        <div className="text-lg font-bold text-slate-900">&ge; 0.50 Threshold</div>
                      </div>
                    </div>

                    {/* Class Metrics Table */}
                    <div className="border border-slate-200 rounded overflow-hidden">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-slate-100 border-b border-slate-200 text-slate-700">
                          <tr>
                            <th className="py-2 px-3 font-semibold">Anatomical Region</th>
                            <th className="py-2 px-3 font-semibold">Precision</th>
                            <th className="py-2 px-3 font-semibold">Recall (Sensitivity)</th>
                            <th className="py-2 px-3 font-semibold">F1-Score</th>
                            <th className="py-2 px-3 font-semibold">Test Support</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 bg-white">
                          {Object.entries(metrics.anatomical_router.class_metrics || {}).map(([reg, m]) => (
                            <tr key={reg} className="hover:bg-slate-50">
                              <td className="py-2 px-3 font-bold text-slate-900 capitalize">{reg}</td>
                              <td className="py-2 px-3 text-slate-700">{(m.precision * 100).toFixed(1)}%</td>
                              <td className="py-2 px-3 text-slate-700">{(m.recall * 100).toFixed(1)}%</td>
                              <td className="py-2 px-3 text-slate-700">{(m['f1-score'] * 100).toFixed(1)}%</td>
                              <td className="py-2 px-3 text-slate-500">{m.support}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Stage 2: MSK Damage Localization Metrics */}
                {metrics.msk_damage_detector && (
                  <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">
                          Stage 2: Musculoskeletal Damage Localization & Fracture Detector
                        </h3>
                        <p className="text-xs text-slate-500">Multi-task ResNet-18 evaluated on held-out test musculoskeletal set</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-500">Classification Accuracy</span>
                        <div className="text-xl font-bold text-emerald-700">
                          {(Number(metrics.msk_damage_detector?.classification?.accuracy ?? 0) * 100).toFixed(2)}%
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">Sensitivity (Recall)</div>
                        <div className="text-base font-bold text-slate-900">
                          {(Number(metrics.msk_damage_detector?.classification?.sensitivity ?? 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">Specificity</div>
                        <div className="text-base font-bold text-slate-900">
                          {(Number(metrics.msk_damage_detector?.classification?.specificity ?? 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">AUROC</div>
                        <div className="text-base font-bold text-slate-900">
                          {metrics.msk_damage_detector?.classification?.auroc ?? "N/A"}
                        </div>
                      </div>
                      <div className="bg-slate-50 p-3 rounded border border-slate-200">
                        <div className="text-[11px] text-slate-500">mAP@50 (Localization)</div>
                        <div className="text-base font-bold text-slate-900">
                          {(Number(metrics.msk_damage_detector?.localization?.mAP_50 ?? 0) * 100).toFixed(1)}%
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                      <div className="p-3 bg-slate-50 rounded border border-slate-200 text-xs">
                        <div className="font-semibold text-slate-700 mb-1">Spatial Damage Localization:</div>
                        <div className="text-slate-600">
                          - Mean Intersection-over-Union (mIoU): <b>{metrics.msk_damage_detector?.localization?.mean_iou ?? "N/A"}</b>
                        </div>
                        <div className="text-slate-600">
                          - Bounding boxes evaluated: <b>{metrics.msk_damage_detector?.localization?.annotated_boxes_evaluated ?? 0}</b>
                        </div>
                      </div>
                      <div className="p-3 bg-slate-50 rounded border border-slate-200 text-xs">
                        <div className="font-semibold text-slate-700 mb-1">Bone Structure Identification:</div>
                        <div className="text-slate-600">
                          - Top-1 Bone Structure Accuracy: <b>{(Number(metrics.msk_damage_detector?.bone_identification?.top1_accuracy ?? 0) * 100).toFixed(1)}%</b>
                        </div>
                        <div className="text-slate-600">
                          - Target bones: Radius, Ulna, Metacarpals, Femur, Tibia, Clavicle
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Stage 2: Chest Pathway Benchmark */}
                {metrics.chest_analyzer && (
                  <div className="bg-white border border-slate-200 rounded-lg p-6 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">
                          Stage 2: Chest Cardiopulmonary Pathway (TorchXRayVision DenseNet-121)
                        </h3>
                        <p className="text-xs text-slate-500">{metrics.chest_analyzer.benchmark_provenance}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-slate-500">Pathologies Supported</span>
                        <div className="text-xl font-bold text-sky-700">
                          {metrics.chest_analyzer.total_pathologies_supported}
                        </div>
                      </div>
                    </div>

                    <div className="text-xs text-slate-600">
                      The chest pathway evaluates 18 validated cardiopulmonary conditions using weights trained on multi-center clinical cohorts.
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                      {metrics.chest_analyzer.supported_pathologies?.map((p) => (
                        <div key={p} className="p-2 bg-slate-50 border border-slate-200 rounded text-center">
                          <div className="text-xs font-semibold text-slate-800 truncate">{p}</div>
                          <div className="text-[10px] text-slate-500">Validated Model</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white border border-slate-200 rounded-lg p-8 text-center text-slate-500 text-sm">
                Loading test evaluation metrics...
              </div>
            )}
          </div>
        )}

        {/* TAB 3: SUPPORTED REGIONS */}
        {activeTab === 'regions' && (
          <div className="space-y-6 fade-in">
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-1">
                Supported Anatomical Regions & Specific Model Capabilities
              </h2>
              <p className="text-xs text-slate-600">
                In strict accordance with medical research standards, we do not claim support for a region unless its model
                has been implemented and evaluated. Unsupported body parts are explicitly flagged by the router.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {[
                {
                  region: 'Wrist',
                  population: 'Pediatric & Adult',
                  dataset: 'GRAZPEDWRI-DX & FracAtlas',
                  model: 'MSK Damage Localization ResNet-18',
                  capabilities: 'Cortical disruption detection, exact bounding box localization, distal radius/ulna identification',
                  supported: true
                },
                {
                  region: 'Hand',
                  population: 'Adult & Pediatric',
                  dataset: 'FracAtlas',
                  model: 'MSK Damage Localization ResNet-18',
                  capabilities: 'Metacarpal & phalangeal fracture detection, spatial box localization, displacement tag',
                  supported: true
                },
                {
                  region: 'Leg',
                  population: 'Adult & Pediatric',
                  dataset: 'FracAtlas',
                  model: 'MSK Damage Localization ResNet-18',
                  capabilities: 'Tibia, fibula, and femoral shaft fracture localization with bounding box',
                  supported: true
                },
                {
                  region: 'Hip',
                  population: 'Adult',
                  dataset: 'FracAtlas',
                  model: 'MSK Damage Localization ResNet-18',
                  capabilities: 'Pelvic and femoral neck fracture detection and focal box localization',
                  supported: true
                },
                {
                  region: 'Shoulder',
                  population: 'Adult & Pediatric',
                  dataset: 'FracAtlas',
                  model: 'MSK Damage Localization ResNet-18',
                  capabilities: 'Clavicle, scapula, and humeral head damage localization',
                  supported: true
                },
                {
                  region: 'Chest',
                  population: 'Adult',
                  dataset: 'TorchXRayVision Ensemble / NIH / CheXpert',
                  model: 'DenseNet-121 Pretrained',
                  capabilities: '18 cardiopulmonary pathologies: Cardiomegaly, Pneumonia, Effusion, Atelectasis, Pneumothorax',
                  supported: true
                },
                {
                  region: 'Elbow, Forearm, Humerus',
                  population: 'Adult',
                  dataset: 'Stanford MURA (DUA Protected)',
                  model: 'Router Identified (Stage 2 in Registration Protocol)',
                  capabilities: 'Region detected by router; full clinical weights require Stanford AIMI agreement approval',
                  supported: false
                },
                {
                  region: 'Knee, Ankle, Foot',
                  population: 'N/A',
                  dataset: 'No validated open training data',
                  model: 'Not Implemented',
                  capabilities: 'Flagged as unsupported out-of-distribution input by Stage 1 router',
                  supported: false
                }
              ].map((r) => (
                <div key={r.region} className={`border rounded-lg p-5 ${r.supported ? 'bg-white border-slate-200' : 'bg-slate-50 border-slate-200 opacity-80'}`}>
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-base font-bold text-slate-900">{r.region}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      r.supported ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'
                    }`}>
                      {r.supported ? 'ACTIVE & EVALUATED' : 'FLAGGED AS UNSUPPORTED'}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mb-2">
                    Cohort: <b>{r.population}</b> | Source: <b>{r.dataset}</b>
                  </div>
                  <div className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100 mb-2">
                    <span className="font-semibold">Pipeline:</span> {r.model}
                  </div>
                  <div className="text-xs text-slate-600 leading-relaxed">
                    <span className="font-semibold">Capabilities:</span> {r.capabilities}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: DATASETS & PROVENANCE */}
        {activeTab === 'datasets' && (
          <div className="space-y-6 fade-in">
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-1">
                Dataset Manifests, Licenses & Leakage-Safe Splitting
              </h2>
              <p className="text-xs text-slate-600">
                Ethical data provenance: all samples are ingested directly from official repositories with strict adherence
                to Data Use Agreements, CITI credentials, and open licenses.
              </p>
            </div>

            {datasetsInfo?.datasets && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {datasetsInfo.datasets.map((d) => (
                  <div key={d.name} className="bg-white border border-slate-200 rounded-lg p-5 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                      <h3 className="text-base font-bold text-slate-900">{d.name}</h3>
                      <span className="text-xs font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                        {d.status}
                      </span>
                    </div>

                    <div className="text-xs text-slate-700 font-medium">
                      {d.full_title}
                    </div>

                    <div className="text-xs text-slate-500 space-y-1">
                      <div>DOI / ID: <span className="font-mono text-slate-800">{d.doi}</span></div>
                      <div>License: <span className="font-semibold text-slate-800">{d.license}</span></div>
                      <div>Sampled Images: <span className="font-bold text-slate-900">{d.selected_samples}</span></div>
                      <div>Regions: <span className="capitalize text-slate-800">{Array.isArray(d.regions_covered) ? d.regions_covered.join(', ') : d.regions_covered}</span></div>
                    </div>

                    <div className="p-2.5 bg-slate-50 rounded border border-slate-100 text-xs text-slate-600">
                      <span className="font-semibold text-slate-700">Patient Separation:</span> {d.patient_separation}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Split Statistics */}
            {datasetsInfo?.global_statistics && (
              <div className="bg-white border border-slate-200 rounded-lg p-6">
                <h3 className="text-sm font-bold text-slate-900 mb-3">Leakage-Safe Partition Summary</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="bg-slate-50 p-4 rounded border border-slate-200">
                    <div className="text-xs text-slate-500">Training Split (70%)</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">{datasetsInfo.global_statistics.split_counts?.train}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Model Optimization</div>
                  </div>
                  <div className="bg-slate-50 p-4 rounded border border-slate-200">
                    <div className="text-xs text-slate-500">Validation Split (15%)</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">{datasetsInfo.global_statistics.split_counts?.val}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Hyperparameter Tuning</div>
                  </div>
                  <div className="bg-slate-50 p-4 rounded border border-slate-200">
                    <div className="text-xs text-slate-500">Held-Out Test Split (15%)</div>
                    <div className="text-2xl font-bold text-slate-900 mt-1">{datasetsInfo.global_statistics.split_counts?.test}</div>
                    <div className="text-[11px] text-slate-400 mt-0.5">Empirical Evaluation Only</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: SYSTEM ARCHITECTURE */}
        {activeTab === 'architecture' && (
          <div className="space-y-6 fade-in">
            <div className="bg-white border border-slate-200 rounded-lg p-6">
              <h2 className="text-lg font-bold text-slate-900 mb-1">
                Modular Multi-Model AI Architecture
              </h2>
              <p className="text-xs text-slate-600">
                A two-stage decoupled neural network cascade. We never force chest models onto musculoskeletal radiographs
                or assume one single model can diagnose all human anatomical structures.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2">
                <div className="w-8 h-8 rounded bg-sky-100 text-sky-800 flex items-center justify-center font-bold text-sm">
                  1
                </div>
                <h3 className="text-sm font-bold text-slate-900">Stage 1: Router</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  ResNet-18 classifier identifies body region (Wrist, Hand, Leg, Hip, Shoulder, Chest) with confidence gating.
                  Inputs with &lt;0.50 score are safely flagged as unsupported.
                </p>
              </div>

              <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2">
                <div className="w-8 h-8 rounded bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-sm">
                  2
                </div>
                <h3 className="text-sm font-bold text-slate-900">Stage 2: MSK Detector</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Multi-task ResNet-18 outputs binary fracture probabilities, 2D damage bounding boxes [xmin, ymin, xmax, ymax],
                  and identifies affected bones (Radius, Ulna, Femur, Tibia, Clavicle).
                </p>
              </div>

              <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2">
                <div className="w-8 h-8 rounded bg-indigo-100 text-indigo-800 flex items-center justify-center font-bold text-sm">
                  3
                </div>
                <h3 className="text-sm font-bold text-slate-900">Stage 2: Chest Pathway</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  DenseNet-121 pretrained on NIH/CheXpert/PadChest cohorts predicts 18 cardiopulmonary pathologies
                  with Grad-CAM visual heatmaps.
                </p>
              </div>

              <div className="bg-white border border-slate-200 rounded-lg p-5 space-y-2">
                <div className="w-8 h-8 rounded bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-sm">
                  4
                </div>
                <h3 className="text-sm font-bold text-slate-900">Stage 3: Report & Safety</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Generates side-by-side specimen comparison, Gemini clinical educational narrative,
                  and compiles a downloadable clinical PDF summary report.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: MEDICAL DISCLAIMER */}
        {activeTab === 'disclaimer' && (
          <div className="space-y-6 fade-in max-w-4xl mx-auto">
            <div className="bg-white border border-red-200 rounded-lg p-8 space-y-4">
              <div className="flex items-center space-x-3 text-red-600">
                <ShieldAlert className="w-7 h-7 shrink-0" />
                <h2 className="text-lg font-bold">Mandatory Medical Safety & Ethical Research Notice</h2>
              </div>

              <div className="text-xs text-slate-700 space-y-3 leading-relaxed">
                <p>
                  <b>1. Investigational & Educational Purpose Only:</b> This software platform is developed exclusively as an
                  academic engineering and medical-imaging research prototype. It has <b>NOT</b> been evaluated or cleared by the
                  U.S. Food and Drug Administration (FDA), European Medicines Agency (EMA), or any other regulatory medical device authority.
                </p>
                <p>
                  <b>2. Not a Medical Device:</b> The outputs, bounding boxes, segmentation masks, confidence values, and AI-generated narratives
                  do <b>NOT</b> constitute medical advice, radiological diagnoses, or clinical treatment plans. Saliency maps and bounding
                  boxes represent probabilistic computer vision activations, not verified pathology contours.
                </p>
                <p>
                  <b>3. Mandatory Professional Verification:</b> Every radiographic finding must be reviewed, interpreted, and verified
                  by a licensed physician, board-certified radiologist, or qualified orthopedic specialist prior to any clinical decision.
                </p>
                <p>
                  <b>4. Privacy and HIPAA / GDPR Compliance:</b> Identifiable patient health information (PHI) must never be transmitted
                  to third-party services. The platform runs local inference without uploading image binaries to external clouds.
                </p>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between text-xs text-slate-500">
          <div>Antigravity Multi-Region X-Ray Analysis AI &bull; Milestone 5 Validated</div>
          <div>Strict Empirical Metrics &bull; Patient-Safe Split Protocols</div>
        </div>
      </footer>
    </div>
  );
}
