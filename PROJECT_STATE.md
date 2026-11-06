# MEDVISION-AI — Current Project State & Operational Guide

**System Name:** MEDVISION-AI — Multi-Modal Clinical Intelligence Workspace  
**Status:** **Fully Functional & Verified**  
**Web Application URL:** [http://localhost:3000](http://localhost:3000)  

---

## 1. Architecture Overview

```
                                    +-----------------------+
                                    |     Web Browser       |
                                    | http://localhost:3000 |
                                    +-----------+-----------+
                                                |
                                                v
                              +------------------------------------+
                              |  Central Express Gateway (:3000)   |
                              |  Routes, Controllers, Mongoose DB  |
                              +--------+--------+--------+---------+
                                       |        |        |
                     +-----------------+        |        +-----------------+
                     v                          v                          v
       +---------------------------+ +---------------------+ +---------------------------+
       | Prescription AI (:8001)   | |  X-Ray AI (:8002)   | |   CT-Scan AI (:8003)      |
       | EasyOCR (CRAFT + BiLSTM)  | | PyTorch ResNet-18   | | Gemini Clinical Vision    |
       | Fuzzy Pharmacopeia Parser | | TorchXRay DenseNet  | | Lanczos Multi-Modal Vision|
       +---------------------------+ +---------------------+ +---------------------------+
                     \                          |                          /
                      \                         |                         /
                       +------------------------v------------------------+
                                                |
                                                v
                               +---------------------------------+
                               |   Shared MongoDB Database       |
                               | mongodb://127.0.0.1:27017/      |
                               | medvision_ai                    |
                               +---------------------------------+
```

---

## 2. Directory Structure

```
MEDVISION-AI/
├── frontend/
│   ├── pages/
│   │   ├── index.html          # Main Clinical Hub with live statistics & patient profile
│   │   ├── prescription.html   # EasyOCR digitizer with interactive editing & history
│   │   ├── xray.html           # Multi-region PyTorch radiograph analyzer & side-by-side comparison
│   │   ├── ct-scan.html        # CT Clinical Vision with zero-hallucination observations
│   │   └── dashboard.html      # Unified chronological patient medical timeline
│   ├── css/
│   │   ├── main.css            # Clinical design system & color palette
│   │   └── components.css      # Glassmorphism cards, stat widgets, badges & tables
│   ├── js/
│   │   ├── api.js              # Central fetch wrappers for gateway endpoints
│   │   ├── app.js              # UI alerts, toasts, and system health polling
│   │   ├── patient-manager.js  # Active patient identity management & sync
│   │   ├── prescription-client.js # Upload, OCR transcription, verification & report
│   │   ├── xray-client.js      # Upload, PyTorch inference, dual viewer & PDF
│   │   └── ct-client.js        # Upload, Gemini vision analysis & differential table
│   └── assets/
│       └── images/             # Clinical test fixtures (prescriptions, xrays, CTs)
│
├── backend/
│   ├── config/                 # Ports, MongoDB connection & environments
│   ├── controllers/            # Express request handlers for all modalities
│   ├── routes/                 # API route declarations
│   ├── services/               # Microservice HTTP proxy clients
│   ├── models/                 # Mongoose schemas (Patient, AnalysisResult, Prescription)
│   ├── middleware/             # Multer storage uploads & error handler
│   ├── server.js               # Entrypoint bootstrapping Express gateway
│   └── package.json            # Node.js dependencies
│
├── ai-services/
│   ├── prescription-ai/        # EasyOCR CRAFT+BiLSTM microservice (:8001)
│   ├── xray-ai/                # PyTorch ResNet-18 + DenseNet-121 MSK service (:8002)
│   └── ct-ai/                  # Gemini Clinical Vision microservice (:8003)
│
├── storage/                    # Local persistent file storage for uploaded radiographs
│   ├── prescriptions/
│   ├── xrays/
│   ├── ct-scans/
│   └── reports/
│
├── docs/                       # Complete project architecture & testing reports
├── start-all.bat               # Single-click unified startup script
└── verify_complete_e2e.py      # Automated 7-suite verification script
```

---

## 3. How to Launch All Services

Run the provided batch file in the root directory:
```bash
./start-all.bat
```
Or start each service independently:
1. **Prescription AI**: `cd ai-services/prescription-ai && python adapter/service_adapter.py`
2. **X-Ray AI**: `cd ai-services/xray-ai && python adapter/service_adapter.py`
3. **CT AI**: `cd ai-services/ct-ai && python adapter/service_adapter.py`
4. **Gateway**: `cd backend && node server.js`

Open [http://localhost:3000](http://localhost:3000) in any web browser.
