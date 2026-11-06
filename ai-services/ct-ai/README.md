# MedVision-AI — AI-Powered CT Scan Image Analyzer with Gemini

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![Gemini](https://img.shields.io/badge/AI_Engine-Gemini_3.8_Flash-8b5cf6.svg)](https://ai.google.dev/)
[![Flask](https://img.shields.io/badge/Backend-Flask_3.1-000000.svg)](https://flask.palletsprojects.com/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI_0.141-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_%2B_Vite-61dafb.svg)](https://react.dev/)
[![ReportLab](https://img.shields.io/badge/PDF_Engine-ReportLab_5.1-e11d48.svg)](https://www.reportlab.com/)

An enterprise-grade, clinical decision-support web system for automated CT scan and medical radiograph visual analysis, objective radiological observation extraction, and structured PDF report generation powered by Google's Gemini Multimodal Vision API.

---

## 🌟 Key Features & Architectural Highlights

1. **Gemini Clinical Vision Integration**
   - Utilizes Google's latest multimodal models (`gemini-3.8-flash`, with an automated fallback cascade to `gemini-flash-latest`, `gemini-3.1-flash-lite`, and `gemini-3.5-flash`).
   - Implements a carefully crafted **Zero-Hallucination Radiological Prompt** that restricts evaluation strictly to visible image densities and anatomical features.
   - Enforces a clear distinction between **objective visual observations** and **non-definitive potential clinical considerations**.

2. **Dual-Framework Architecture**
   - **Standalone Flask Server (`app.py`)**: Runs directly on port 5000, serving the complete MedVision-AI glassmorphism dashboard, health check, analysis API, and ReportLab PDF generator without requiring Node.js.
   - **FastAPI Core (`backend/app/main.py`)**: High-throughput REST API on port 8000, supporting asynchronous endpoints, OpenAPI documentation (`/docs`), PyTorch ResNet-18 pneumonia inference, and Grad-CAM explainability heatmaps.
   - **Shared Modular Services (`services/`)**: Unified service layer for image validation, dimension detection, Gemini API client handling, and ReportLab PDF generation.

3. **Secure Image Preprocessing & Ingestion**
   - Validates file integrity, headers, formats (PNG, JPG, JPEG), and enforces 15 MB upload limits.
   - Preserves native contrast and detects image dimensions, color modes, and aspect ratios.
   - Applies high-quality Lanczos antialiased resizing only when dimensions exceed 2048px to prevent GPU/API memory degradation while preserving subtle tissue boundaries.

4. **Structured Decision-Support Reporting**
   - **Image Information**: Observed modality, resolution, screening clarity, and static slice limitations.
   - **Visible Visual Observations**: Tabular/card breakdown of physical densities, opacity patterns, and anatomical locations with "Observed" status.
   - **Potential Findings**: Differential considerations with clinical reasoning and explicit "Uncertain" certainty flags.
   - **Study Limitations & Recommendations**: Actionable guidance for laboratory correlation and formal radiologist review.

5. **ReportLab PDF Medical Report Generator**
   - Generates two-pass multi-page medical PDF reports with dynamic "Page X of Y" counters, hospital-grade headers, embedded scaled scan imaging, and high-contrast tables.
   - Prominently embeds official medical disclaimers to prevent diagnostic misuse.

6. **Healthcare Dashboard UI**
   - Styled with dark navy-blue background (`#0a0f1d`), cyan (`#06b6d4`), and purple (`#8b5cf6`) accents.
   - Smooth glassmorphism panels, drag-and-drop file uploader, real-time scanning reticle animations, and one-click demo scan loader.

---

## 📁 Project Directory Structure

```
CT-Scan-Image-Analyzer/
├── app.py                         # Standalone Flask Application & API Server
├── requirements.txt               # Unified project dependencies
├── .env                           # Server environment & Gemini API configuration
├── .env.example                   # Configuration template
├── .gitignore                     # Git ignore rules (protects API keys & uploads)
├── README.md                      # Documentation & deployment guide
│
├── services/                      # Modular Business & Clinical Logic
│   ├── __init__.py                # Package exports
│   ├── gemini_service.py          # Gemini Vision API client, prompt & schema validator
│   ├── image_preprocessing.py     # Image decoding, validation & dimension handling
│   └── report_service.py          # ReportLab PDF report generation engine
│
├── templates/
│   └── index.html                 # MedVision-AI Standalone Web Dashboard
│
├── static/
│   ├── css/
│   │   └── style.css              # Dark navy & cyan glassmorphism design system
│   └── js/
│       └── script.js              # Client-side upload, stepper & report renderer
│
├── backend/                       # FastAPI Deep Learning Backend
│   ├── app/
│   │   ├── main.py                # FastAPI bootstrapper & router aggregator
│   │   ├── api/
│   │   │   ├── ct_analysis_routes.py # CT analysis & PDF download endpoints
│   │   │   ├── image_routes.py    # ResNet-18 pneumonia detection & Grad-CAM routes
│   │   │   ├── prescription_routes.py # Clinical prescription analysis
│   │   │   └── health_routes.py   # System health and hardware inspection
│   │   └── services/              # ResNet18 & Grad-CAM deep learning pipelines
│   └── requirements.txt
│
├── frontend/                      # React 18 + Vite Healthcare Portal
│   ├── src/
│   │   ├── pages/
│   │   │   ├── CTScanAnalysis.jsx # MedVision-AI React Dashboard
│   │   │   ├── ImageAnalysis.jsx  # Chest Radiography & Grad-CAM viewer
│   │   │   └── DoctorDashboard.jsx
│   │   ├── services/api.js        # Frontend API client
│   │   └── App.jsx
│   └── package.json
│
├── dataset/                       # Clinical evaluation datasets
│   └── chest_xray/
│
├── uploads/                       # Temporary upload storage (auto-generated)
├── generated_reports/             # Generated PDF medical reports (auto-generated)
│
└── tests/                         # Automated Unit & Integration Test Suite
    ├── test_upload.py             # Image validation and preprocessing tests
    ├── test_analysis.py           # Gemini prompt, schema & connectivity tests
    ├── test_report.py             # ReportLab PDF formatting and layout tests
    └── test_api_endpoints.py      # Flask endpoint integration tests
```

---

## ⚙️ Installation & Configuration

### 1. Prerequisites
- Python 3.10 or higher
- Node.js 18+ (optional, only if modifying the React frontend)
- Google Gemini API Key ([Get an API Key](https://aistudio.google.com/))

### 2. Environment Setup
Configure your `.env` file in the project root:

```ini
# Gemini AI Configuration
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
GEMINI_MODEL=gemini-3.8-flash
FALLBACK_MODELS=gemini-flash-latest,gemini-3.1-flash-lite,gemini-3.5-flash,gemini-2.5-pro

# Server Configuration
PORT=5000
HOST=0.0.0.0
FASTAPI_PORT=8000
MAX_CONTENT_LENGTH=15728640
ALLOWED_EXTENSIONS=png,jpg,jpeg,webp
```

> **Security Note:** Never commit your actual API key to GitHub. The `.env` file is ignored by `.gitignore`.

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🚀 Running the Application

### Option A: Standalone MedVision-AI Web App (Recommended)
Launch the unified Flask application serving the web dashboard and APIs:
```powershell
python app.py
```
- Open **[http://localhost:5000](http://localhost:5000)** in any modern browser.
- Instant access to drag-and-drop CT scan upload, live visual analysis, structured report rendering, and PDF report downloads.

### Option B: FastAPI Backend + React Frontend
To run the full decoupled stack with ResNet-18 pneumonia detection and Grad-CAM overlays:

1. **Start the FastAPI Server:**
```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

2. **Start the React Frontend:**
```powershell
cd frontend
npm run dev
```
- Open **[http://localhost:5173](http://localhost:5173)**. Navigate to the **"CT Scan Analyzer"** tab to access the MedVision-AI portal.

---

## 📡 API Reference

### 1. System Health & Gemini Configuration
- **Endpoint:** `GET /api/health`
- **Response:**
```json
{
  "status": "healthy",
  "service": "MedVision-AI CT Scan Image Analyzer",
  "version": "2.0.0",
  "gemini": {
    "api_key_configured": true,
    "configured_model": "gemini-3.8-flash",
    "client_status": "ready"
  }
}
```

### 2. Analyze CT Scan Image
- **Endpoint:** `POST /api/analyze`
- **Request:** `multipart/form-data` with `file: <binary image>`
- **Response:**
```json
{
  "status": "success",
  "data": {
    "report_title": "AI-Assisted CT Image Analysis Report",
    "filename": "axial_slice_042.jpg",
    "image_information": {
      "image_type": "Axial Chest CT Slice",
      "image_dimensions": "512 x 512 px",
      "image_quality": "High diagnostic contrast",
      "limitations": ["Single static slice view"]
    },
    "visual_observations": [
      {
        "observation": "Airspace Opacity",
        "location": "Right lower lung zone",
        "description": "Focal ground-glass attenuation with air bronchograms",
        "certainty": "observed"
      }
    ],
    "potential_findings": [
      {
        "finding": "Possible focal consolidation",
        "location": "Right lower lobe",
        "description": "Visual density pattern consistent with infectious infiltrate",
        "certainty": "uncertain",
        "supporting_visual_observation": "Airspace Opacity"
      }
    ],
    "summary": "Focal opacity observed in right lower lung field. Correlate clinically.",
    "recommendations_for_review": ["Formal radiologist review required"],
    "limitations": ["Evaluation restricted to single slice"],
    "medical_disclaimer": "This report is AI-generated for decision support...",
    "model_used": "gemini-3.8-flash",
    "generated_at": "2026-11-05 21:00:00 UTC"
  }
}
```

### 3. Generate Downloadable PDF Report
- **Endpoint:** `POST /api/generate-report`
- **Payload:**
```json
{
  "report": { ... },
  "server_image_id": "optional_image_id.jpg"
}
```
- **Response:**
```json
{
  "status": "success",
  "filename": "MedVision_Report_a1b2c3d4.pdf",
  "download_url": "/api/reports/download/MedVision_Report_a1b2c3d4.pdf"
}
```

### 4. Download PDF
- **Endpoint:** `GET /api/reports/download/{filename}`
- **Response:** `application/pdf` binary stream attachment.

### 5. Verified Demo Sample Scan
- **Endpoint:** `GET /api/sample`
- **Response:** `image/jpeg` binary for instant one-click demonstration.

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive, automated test suite covering all functional and safety requirements:

```powershell
python -m unittest discover tests -v
```

### Test Coverage Summary:
- **`tests/test_upload.py`**:
  - Valid image decoding and dimension preservation.
  - Aspect-ratio-preserving safe downscaling of oversized scans.
  - Corrupted binary file rejection (`ImageValidationError`).
  - Non-image extension filtering.
- **`tests/test_analysis.py`**:
  - Markdown code block stripping and JSON sanitization.
  - Strict radiological schema normalization and uncertainty enforcement.
  - Missing API key detection (`GeminiConfigurationError`).
  - Live Gemini Vision API connectivity and structured output generation.
- **`tests/test_report.py`**:
  - ReportLab PDF construction, table wrapping, and header checks.
  - Dynamic image aspect-ratio scaling inside PDF margins.
  - Dual-pass canvas with confidential running headers and "Page X of Y" pagination.
- **`tests/test_api_endpoints.py`**:
  - Full client test of `GET /`, `GET /api/health`, `POST /api/analyze`, `POST /api/generate-report`, and `GET /api/reports/download/<filename>`.

---

## ⚖️ Clinical & Legal Disclaimer

> [!IMPORTANT]
> **NOT FOR PRIMARY DIAGNOSIS:** MedVision-AI is an artificial intelligence research and decision-support prototype developed for academic and healthcare hackathon evaluation.
> 
> 1. A single 2D image slice or static radiograph cannot replace a full volumetric, multi-phase clinical CT study.
> 2. Visual observations and differential possibilities generated by the system are non-definitive hypotheses.
> 3. This system must never be used as a standalone diagnostic tool or to delay formal medical care.
> 4. All reports, observations, and recommendations require review, clinical correlation, and formal authorization by a qualified, board-certified radiologist or licensed physician.
