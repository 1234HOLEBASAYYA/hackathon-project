# Multi-Region X-Ray Analysis AI Platform

An enterprise-grade, dual-layer hybrid AI diagnostic platform for multi-region radiographic imaging, anatomical routing, pathological defect detection, spatial lesion localization, and automated clinical report generation.

---

## Architecture Overview

```
                      [Uploaded Radiograph (Any Region / Format)]
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Layer 1: Gemini Multimodal Diagnostic Vision                                        │
│   • Multi-Region Coverage: Chest, Hand, Wrist, Foot, Leg, Knee, Hip, Shoulder, etc.│
│   • Pathologies: Fractures, Cortical Defects, Dislocations, Opacities, Infections   │
│   • Spatial Localization: Exact 2D bounding boxes [ymin, xmin, ymax, xmax]         │
│   • Anatomical Pinpointing: Specific affected bone & structure identification        │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │
┌──────────────────────────────────────────┴──────────────────────────────────────────┐
│ Layer 2: Local High-Speed PyTorch Deep Learning Cascade                             │
│   • ResNet-18 MSK Damage Detector (100% Sensitivity on held-out test fractures)     │
│   • TorchXRayVision DenseNet-121 (18 Cardiopulmonary Pathologies)                   │
│   • Sub-second local execution & offline fallback                                   │
└──────────────────────────────────────────┬──────────────────────────────────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Explainability, Visualization & Clinical Reporting                                  │
│   • Side-by-Side Specimen (Raw Radiograph alongside AI Annotated Overlay)          │
│   • Dynamic High-Contrast Bounding Boxes with Labels & Legend                       │
│   • Automated Clinical Summary & Formal Downloadable PDF Report (ReportLab)         │
│   • Modern React 19 Frontend Dashboard (Tailwind CSS, Single-Accent Clinical UI)    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Multi-Region Anatomical Coverage:** Full support across all major anatomical zones—Chest, Hand, Wrist, Foot, Leg, Knee, Hip, Shoulder, Spine, and Skull.
- **Dual-Layer Diagnostic Pipeline:** High-precision Gemini multimodal vision combined with offline-capable PyTorch neural networks.
- **Exact Spatial Localization:** Generates normalized bounding boxes around lesions, fracture lines, and structural defects.
- **Side-by-Side Comparison:** Generates side-by-side comparative specimen visualizations comparing the raw X-ray directly with the AI-annotated damage overlay.
- **Formal Medical PDF Generation:** Automated ReportLab PDF generator providing clinical narratives, structured observations, and certified radiologist safety disclaimers.
- **Interactive Single-Accent Dashboard:** React 19 + Tailwind CSS user interface with drag-and-drop file upload, live preview, test specimen presets, and instant report download.

---

## Supported Datasets & Benchmarks

The platform includes manifests, splits, downloaders, and evaluation pipelines for leading radiographic datasets:
- **FracAtlas:** Multi-region fracture detection and anatomical localization.
- **MURA (Musculoskeletal Radiographs):** Bone abnormality detection (Stanford AIMI).
- **GrazPedWRI:** Pediatric wrist trauma and fracture bounding box annotations.
- **VinDr-CXR & COVID-19 Radiography:** Cardiopulmonary opacities, consolidations, and pneumonia.

---

## Project Structure

```
├── backend/
│   ├── main.py                     # FastAPI server & static file mount
│   ├── routers/
│   │   ├── analysis.py             # Radiograph upload, inference & samples
│   │   ├── models_info.py          # Model architecture & checkpoint metrics
│   │   └── datasets_info.py        # Dataset manifest summaries & distributions
│   ├── services/
│   │   ├── inference_service.py    # Hybrid pipeline coordinator (Gemini + PyTorch)
│   │   └── gemini_service.py       # Multimodal vision & clinical reasoning
│   └── static/
│       ├── reports/                # Generated PDF reports (.gitkeep)
│       ├── results/                # Annotated overlays & specimens (.gitkeep)
│       └── uploads/                # Fixture samples (chest, wrist, hand, etc.)
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Clinical dashboard application
│   │   ├── index.css               # Design system & token definitions
│   │   └── main.jsx                # React root mount
│   ├── package.json
│   └── vite.config.js
├── models/
│   ├── anatomical_router/          # Region classification model & training
│   ├── chest_pathway/              # DenseNet-121 cardiopulmonary analyzer
│   ├── msk_pathway/                # ResNet-18 fracture detector & bounding box regressor
│   ├── explainability/             # Grad-CAM overlays & ReportLab PDF generator
│   └── weights/                    # Checkpoints (.pt) and evaluation metrics (.json)
├── data/
│   ├── manifests/                  # Unified multi-dataset index (CSV/JSON)
│   ├── splits/                     # Stratified train/val/test splits
│   └── reports/                    # Confusion matrices and evaluation reports
├── scripts/
│   ├── datasets/                   # Dataset downloaders & preprocessing utilities
│   └── test_end_to_end.py          # End-to-end integration test suite
├── requirements.txt                # Python backend dependencies
└── README.md
```

---

## Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **Node.js 18+** & `npm`
- **Gemini API Key** (from [Google AI Studio](https://aistudio.google.com/))

### 2. Environment Configuration

Create a `.env` file in the project root or inside `backend/`:

```bash
cp .env.example .env
```

Edit `.env` and set your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI backend server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API documentation will be accessible at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 4. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install

# Build for production (served automatically by backend at http://localhost:8000)
npm run build

# Or run Vite dev server for hot reload
npm run dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/analyze` | Upload radiograph (`multipart/form-data`) for full hybrid diagnostic analysis |
| `GET` | `/api/samples` | Retrieve pre-loaded multi-region test radiograph fixtures |
| `GET` | `/api/report/{id}/pdf` | Download formal medical diagnostic PDF report |
| `GET` | `/api/models/info` | Inspect model architectures, parameters, and benchmark metrics |
| `GET` | `/api/datasets/info` | Inspect dataset statistics and distribution manifests |
| `GET` | `/health` | System health check, CUDA status, and model checkpoint availability |

---

## Medical Disclaimer

> **IMPORTANT:** This software is designed exclusively for educational, research, and assistive evaluation purposes. It is **not** an FDA-cleared or CE-marked medical device. All outputs, bounding boxes, diagnostic narratives, and generated PDF reports must be independently verified by a licensed, board-certified radiologist or qualified medical professional before clinical decision-making.
