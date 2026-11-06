# MEDVISION-AI — Unified Clinical Multi-Modal Intelligence Platform

MEDVISION-AI is an enterprise-grade medical imaging and clinical document intelligence platform. It unifies three independently developed AI diagnostic microservices into a centralized Node.js/Express architecture, a shared MongoDB persistence database, and a cohesive, medical-grade web frontend.

---

## 🌟 Integrated AI Microservices

1. **Prescription AI (`ai-services/prescription-ai`)**
   - **Port:** 8001
   - **Engine:** PyTorch EasyOCR (Deep Learning CRAFT + BiLSTM) & OpenCV preprocessing (CLAHE, deskewing).
   - **Capabilities:** Full-page clinical grammar extraction, fuzzy drug name reconciliation against a 60+ compound database, and structured dosage/frequency extraction.
2. **Multi-Region X-Ray Analysis AI (`ai-services/xray-ai`)**
   - **Port:** 8002
   - **Engine:** Custom ResNet Anatomical Router (10 regions), ResNet-18 MSK Damage Detector, and TorchXRayVision DenseNet-121 (18 pathologies).
   - **Capabilities:** Anatomical routing, spatial bounding box damage localization, comparative side-by-side specimen visualization, and certified ReportLab medical PDF report generation.
3. **CT-Scan Clinical Vision (`ai-services/ct-ai`)**
   - **Port:** 8003
   - **Engine:** Google Gemini Multimodal Clinical Vision with zero-hallucination structured prompt and negative document guardrails.
   - **Capabilities:** Objective visual density observation extraction, non-definitive differential consideration generation with explicit uncertainty flags, and hospital-grade PDF reporting.

---

## 🚀 Quick Start

### 1. Prerequisites
- **Node.js 18+** & `npm`
- **Python 3.10+** (with PyTorch, TorchXRayVision, EasyOCR, and Google GenAI SDK)
- **MongoDB** running locally on port `27017`

### 2. One-Click Launch
Double-click `start-all.bat` or run from terminal:
```bat
start-all.bat
```
This script will:
1. Verify the local MongoDB service.
2. Launch Prescription AI on port `8001`.
3. Launch X-Ray AI on port `8002`.
4. Launch CT-Scan AI on port `8003`.
5. Launch the Central Express Gateway on port `3000`.
6. Open `http://localhost:3000` in your default browser.

### 3. Manual Microservice Startup
Each service retains its own standalone runner script in its `adapter/` folder:
```bash
# Prescription AI
cd ai-services/prescription-ai
python adapter/service_adapter.py

# X-Ray AI
cd ai-services/xray-ai
python adapter/service_adapter.py

# CT-Scan AI
cd ai-services/ct-ai
python adapter/service_adapter.py

# Central Express Gateway
cd backend
npm start
```

---

## 📁 System Architecture

```text
MEDVISION-AI/
├── frontend/                   # Unified HTML5, CSS3 Glassmorphism UI
│   ├── pages/                  # Hub, Prescription, X-Ray, CT, Timeline
│   ├── css/                    # Clinical Dark Navy & Cyan Design System
│   └── js/                     # API client, Patient Manager, Modality controllers
├── backend/                    # Central Node.js & Express API Gateway
│   ├── controllers/            # Ingestion, Microservice Forwarding, MongoDB persistence
│   ├── models/                 # Mongoose schemas (Patient, AnalysisResult, Prescription)
│   ├── routes/                 # /api/patients, /api/analysis/*, /api/reports, /api/health
│   └── services/               # HTTP client connectors for AI services
├── ai-services/                # Preserved original AI projects
│   ├── prescription-ai/        # Original project + Port 8001 adapter
│   ├── xray-ai/                # Original project + Port 8002 adapter
│   └── ct-ai/                  # Original project + Port 8003 adapter
├── storage/                    # Physical file storage for medical media
└── docs/                       # Complete architectural and testing documentation
```

