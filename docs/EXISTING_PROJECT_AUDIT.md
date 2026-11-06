# MedVision-AI: Comprehensive Audit of Existing AI Projects

**Audit Date:** 2026-11-06  
**Auditor:** Antigravity AI Engineering Assistant  
**Scope:** In-depth inspection of the three extracted medical AI projects located in the workspace:
1. `30/` — Doctor Prescription OCR & Clinical Extraction System
2. `X-Ray-Analysis-AI-main/` — Multi-Region X-Ray Analysis AI Platform
3. `CT-Scan-Analysis-main/` — AI-Powered CT Scan Image Analyzer

---

## 1. Project 1 Audit: Doctor Prescription OCR System (`30/`)

### 1.1 Technology Stack & Architecture
- **Primary Framework:** FastAPI (0.115.6 / 0.162.0) with Uvicorn (0.34.0 / 0.54.0)
- **Frontend Stack:** React 19.2.7 + Vite 8.1.1 + Axios + Lucide-React
- **Deep Learning / Vision Engines:**
  - **EasyOCR 1.7.2:** Deep learning CRAFT text detection + BiLSTM text recognition (GPU/CPU-accelerated with PyTorch).
  - **Tesseract OCR (pytesseract 0.3.13):** Fallback OCR engine.
  - **OpenCV 4.10.0 / 5.0.0:** Image preprocessing pipeline with CLAHE contrast enhancement, noise reduction, deskewing, and adaptive thresholding.
  - **RapidFuzz 3.9.3 / 3.14.6:** Fuzzy matching against a clinical pharmacopeia of 60+ known drug names.
  - **Pillow & PyMuPDF / pdf2image:** PDF rasterization at 150/300 DPI.
  - **ReportLab:** PDF prescription summary export.
- **Model Files & Weight Locations:**
  - EasyOCR Weights: Downloaded and verified in `C:\Users\HP\.EasyOCR\model\`:
    - `craft_mlt_25k.pth` (83.1 MB) — Text detection network
    - `english_g2.pth` (15.1 MB) — English recognition network
  - Spacy & Regex Extractors: Built-in clinical grammar parser located in `30/ai/extractor.py`.

### 1.2 Execution Entry Points & Startup Commands
- **Standalone Server Command:**
  ```bash
  cd 30
  python main.py --port 8001
  # OR
  python -m uvicorn backend.app:app --host 127.0.0.1 --port 8001
  ```
- **Standalone CLI Analysis:**
  ```bash
  cd 30
  python main.py tests/fixtures/printed_multimed.png
  ```
- **Verified Execution Status:** Successfully executed against `printed_multimed.png`. Accurately parsed:
  - Doctor: Dr. Sarah Jenkins (Cardiologist, Apollo Hospitals)
  - Patient: Robert Miller (58 yrs, Male)
  - Medications: Atorvastatin (20mg, Once daily night, 100% confidence), Metformin (500mg, Twice daily, 100% confidence).

### 1.3 Discovered API Endpoints
| HTTP Method | Route | Description | Request Type | Response Payload |
|---|---|---|---|---|
| `GET` | `/health` | Hardware & engine status | None | `{ status: "ok", device: "cuda"/"cpu", ocr_engine: ... }` |
| `GET` | `/api/samples` | Pre-loaded sample presets | None | List of samples (printed, handwritten, pdf) |
| `POST` | `/api/prescription/upload` | Uploads image/PDF and generates preview | `multipart/form-data` (`file`) | `{ id: "uuid", preview_url: "...", size_bytes: ... }` |
| `GET` | `/api/prescription/image/{id}` | Serves preview of uploaded file | Path parameter `{id}` | Binary image (image/png) |
| `POST` | `/api/prescription/analyze` | Preprocesses, runs EasyOCR and extracts fields | JSON: `{ id, apply_clahe, apply_deskew, use_gpu }` | Full clinical JSON: clinic, doctor, patient, medicines array, bounding boxes, raw text |
| `GET` | `/api/prescription/result/{id}` | Gets stored parsed prescription | Path parameter `{id}` | Prescription result JSON |
| `PUT` | `/api/prescription/result/{id}` | Saves user edits/corrections | JSON payload | Updated prescription JSON |
| `GET` | `/api/prescription/export/pdf/{id}` | Generates PDF summary export | Path parameter `{id}` | Application/pdf binary |
| `GET` | `/api/prescription/export/csv/{id}` | Generates CSV medication table | Path parameter `{id}` | Text/csv binary |

### 1.4 Ports, Environment Variables & Config
- **Original Port:** Port 8000 (Default Uvicorn)
- **Target Unified Port:** **Port 8001** (to avoid port 8000 collision)
- **Environment Variables (`.env.example`):**
  - `MONGO_URI` (Optional in original standalone memory store)
  - `JWT_SECRET` (For optional review authentication)

---

## 2. Project 2 Audit: Multi-Region X-Ray Analysis AI (`X-Ray-Analysis-AI-main/`)

### 2.1 Technology Stack & Architecture
- **Primary Framework:** FastAPI (0.115.0 / 0.162.0) with Uvicorn (0.34.0 / 0.54.0)
- **Frontend Stack:** React 19.3.1 + Vite 8.3.6 + Tailwind CSS v4 + Lucide-React + Recharts
- **Deep Learning / Vision Models:**
  - **PyTorch (2.6.0+cu124) & TorchXRayVision (1.5.7)**
  - **Anatomical Router:** Custom ResNet classifier routing across 10 anatomical regions (Chest, Hand, Wrist, Foot, Leg, Knee, Hip, Shoulder, Spine, Skull).
  - **MSK Damage Detector:** Multi-task ResNet-18 model detecting fractures/cortical defects and outputting smooth L1 bounding box coordinates.
  - **Chest Analyzer:** TorchXRayVision DenseNet-121 pre-trained model covering 18 cardiopulmonary pathologies (Pneumonia, Consolidation, Infiltration, Atelectasis, Effusion, Mass, Nodule, etc.).
  - **Gemini Multimodal Clinical Vision:** `google-genai` (2.34.0) integration for multimodal diagnostic verification with automatic offline PyTorch fallback.
  - **Explainability & Visualizer:** OpenCV damage box annotations, side-by-side comparative specimen generator, and ReportLab PDF generator.
- **Model Files & Weight Locations (Verified Present):**
  - `X-Ray-Analysis-AI-main/models/weights/anatomical_router.pt` (45.3 MB)
  - `X-Ray-Analysis-AI-main/models/weights/msk_damage_detector.pt` (46.1 MB)
  - `X-Ray-Analysis-AI-main/models/weights/densenet121-res224-all.pt` (28.4 MB)
  - Metrics & histories: `anatomical_router_metrics.json`, `msk_damage_detector_metrics.json`, `chest_model_metrics.json`

### 2.2 Execution Entry Points & Startup Commands
- **Standalone Server Command:**
  ```bash
  cd X-Ray-Analysis-AI-main
  python -m uvicorn backend.main:app --host 127.0.0.1 --port 8002
  ```
- **Automated End-to-End Test Suite:**
  ```bash
  cd X-Ray-Analysis-AI-main
  python scripts/test_end_to_end.py
  ```
- **Verified Execution Status:** Successfully executed all 8 test stages:
  - Wrist fracture detected on distal radius with exact pixel bounding box `[252, 389, 313, 445]`.
  - Chest radiograph analyzed for cardiopulmonary opacities.
  - Side-by-side specimen generated (`specimen_*.jpg`).
  - ReportLab PDF successfully generated (50,345 bytes).

### 2.3 Discovered API Endpoints
| HTTP Method | Route | Description | Request Type | Response Payload |
|---|---|---|---|---|
| `GET` | `/api/health` | System diagnostics & model checkpoint status | None | `{ status: "healthy", system: ..., models_status: { anatomical_router: true, msk_damage_detector: true, chest_analyzer: true } }` |
| `GET` | `/api/samples` | Retrieves test specimens for all anatomical regions | None | List of sample images with region metadata |
| `POST` | `/api/analyze` | Complete multi-stage radiograph analysis | `multipart/form-data` (`file`) | `{ analysis_id, anatomical_region, region_confidence, is_abnormal, confidence, affected_bone, bounding_box_pixels, findings, specimen_url, report_pdf_url }` |
| `GET` | `/api/report/{analysis_id}/pdf` | Downloads formal clinical PDF report | Path parameter `{analysis_id}` | Application/pdf binary |
| `GET` | `/api/models` | Registry of active model architectures & parameters | None | Model catalog JSON |
| `GET` | `/api/metrics` | Model accuracy and sensitivity benchmarks | None | JSON metrics |
| `GET` | `/api/datasets` | Manifest of training datasets | None | Dataset metadata JSON |

### 2.4 Ports, Environment Variables & Config
- **Original Port:** Port 8000 (Collides with Prescription AI & CT FastAPI)
- **Target Unified Port:** **Port 8002**
- **Environment Variables (`.env.example`):**
  - `GEMINI_API_KEY`: Google GenAI API Key (fallback PyTorch models engage if absent or offline).

---

## 3. Project 3 Audit: AI-Powered CT Scan Image Analyzer (`CT-Scan-Analysis-main/`)

### 3.1 Technology Stack & Architecture
- **Primary Frameworks:**
  - Standalone Flask 3.1.3 Server (`app.py`, port 5000) with dark glassmorphism dashboard.
  - FastAPI 0.162.0 Core (`backend/app/main.py`, port 8000) with async routers.
- **Frontend Stack:**
  - Native Vanilla HTML5 + CSS3 (Dark glassmorphism `#0a0f1d`, cyan `#06b6d4`, purple `#8b5cf6`) + JavaScript ES6.
  - React 18 + Vite frontend also present in `frontend/`.
- **Deep Learning / Vision Models:**
  - **Gemini Clinical Vision (`gemini-3.5-flash-lite`, `gemini-3.8-flash`):** Zero-hallucination prompt extracting objective visual observations vs differential potential findings, with a negative document guardrail rejecting non-radiological images.
  - **Local PyTorch ResNet-18 Pneumonia Model:** `backend/model/chest_xray_model.pth` (44.8 MB) with Grad-CAM heatmap generator.
  - **OpenCV Lanczos Preprocessing:** Adaptive antialiased scaling up to 2048px preserving subtle tissue densities.
  - **ReportLab 5.1.0:** Medical PDF generation with multi-page counters and hospital headers.
  - **MongoDB Persistence (`services/mongo_service.py`):** Established MongoDB collections for `analysisresults` and `prescriptions` with `patientId` linkage.
- **Model Files & Weight Locations (Verified Present):**
  - `CT-Scan-Analysis-main/backend/model/chest_xray_model.pth` (44.8 MB)
  - `CT-Scan-Analysis-main/backend/model/class_mapping.json`
  - `CT-Scan-Analysis-main/backend/model/model_config.json`

### 3.2 Execution Entry Points & Startup Commands
- **Standalone Flask Server Command:**
  ```bash
  cd CT-Scan-Analysis-main
  python app.py  # (runs on port 5000)
  ```
- **Standalone FastAPI Server Command:**
  ```bash
  cd CT-Scan-Analysis-main
  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8003
  ```
- **Automated Verification Script:**
  ```bash
  cd CT-Scan-Analysis-main
  python verify_all_modules.py
  ```
- **Verified Execution Status:** Successfully executed all 4 verification tests:
  - Prescription Reader extraction saved to MongoDB.
  - Chest X-Ray ResNet-18 predicted Pneumonia (88.7% confidence) with Grad-CAM saved to MongoDB.
  - CT Scan analyzed via Gemini Vision (3 visual observations, 1 potential finding) saved to MongoDB.
  - Negative guardrail test rejected non-radiological document with HTTP 400.

### 3.3 Discovered API Endpoints
| HTTP Method | Route | Description | Request Type | Response Payload |
|---|---|---|---|---|
| `GET` | `/api/health` | Server status and Gemini client readiness | None | `{ status: "healthy", service: "...", gemini: { client_status: "ready" } }` |
| `POST` | `/api/analyze` | CT slice preprocessing and Gemini analysis | `multipart/form-data` (`file`, `patient_id`) | `{ report_title, is_compatible_ct_scan, detected_modality, visual_observations, potential_findings, summary, analysis_id, patient_id }` |
| `POST` | `/api/generate-report` | Generates ReportLab PDF from analysis JSON | JSON payload | Application/pdf binary |
| `POST` | `/api/images/analyze` | ResNet-18 Pneumonia detection + GradCAM | `multipart/form-data` (`file`, `patient_id`) | `{ prediction, confidence, gradcam, analysis_id, patient_id }` |
| `POST` | `/api/prescriptions/analyze` | Prescription analysis router | `multipart/form-data` (`file`, `patient_id`) | `{ report_title, medications, analysis_id, patient_id }` |

### 3.4 Ports, Environment Variables & Config
- **Original Ports:** Flask uses Port 5000; FastAPI uses Port 8000.
- **Target Unified Port:** **Port 8003** (FastAPI service) or Port 5001.
- **Environment Variables (`.env`):**
  - `GEMINI_API_KEY`: Configured and verified functional.
  - `GEMINI_MODEL`: `gemini-3.5-flash-lite` (with fallbacks `gemini-3.5-flash`, `gemini-3.8-flash`).
  - `MONGODB_URI`: `mongodb://127.0.0.1:27017`
  - `MONGODB_DATABASE`: `medvision_ai`

---

## 4. Port Conflict Resolution Matrix

| Service | Original Port | Port Conflict | Unified Allocated Port | Status |
|---|---|---|---|---|
| **Central Node.js / Express Backend** | N/A | None | **Port 3000** | Available |
| **Unified HTML/CSS/JS Frontend** | 5173 / 5000 | None (Served directly by Express on 3000) | **Port 3000** | Available |
| **Prescription AI Service** | Port 8000 | Conflicted with X-Ray & CT FastAPI | **Port 8001** | Available |
| **X-Ray Analysis AI Service** | Port 8000 | Conflicted with Prescription & CT | **Port 8002** | Available |
| **CT-Scan Analysis AI Service** | Port 8000 / 5000 | Conflicted with 8000 | **Port 8003** | Available |
| **Shared MongoDB Database** | Port 27017 | None | **Port 27017** | Verified Running |

---

## 5. Dependency & Environment Audit Summary

1. **Python Environment (Python 3.12.10):**
   - PyTorch `2.6.0+cu124` (with NVIDIA CUDA support)
   - TorchXRayVision `1.5.7`
   - EasyOCR `1.7.2`
   - Google GenAI SDK `2.34.0`
   - FastAPI `0.162.0` & Flask `3.1.3`
   - OpenCV `5.0.0.93` & Pillow `12.3.0`
   - PyMongo `4.19.0`
   - ReportLab `5.1.0`
   - All Python dependencies are already installed and tested.
2. **Node.js Environment (Node v24.14.1, npm 11.11.0):**
   - Ready for building the Central Express backend (`express`, `mongoose`, `multer`, `axios`, `cors`, `dotenv`).
3. **Database Environment:**
   - MongoDB Server is active and listening on `127.0.0.1:27017` (`db.adminCommand('ping')` returned `{ ok: 1 }`).
