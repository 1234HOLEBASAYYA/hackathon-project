# MEDVISION-AI: System Architecture & Integration Manual

## 1. High-Level Architectural Diagram

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   Unified Medical Web Frontend                         │
│   (HTML5, CSS3 Glassmorphism #0a0f1d / #06b6d4, Vanilla ES6 Client)    │
│   Served directly on Port 3000 to eliminate cross-origin complexity    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST / Multipart Form-Data
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Central Node.js & Express API Gateway (Port 3000)          │
│   • Multer Multipart Ingestion & Binary Storage to storage/            │
│   • Mongoose 8.x ODM with Connection Pooling & patientId Indexing      │
│   • Multi-Service Microservice Orchestration & Error Boundary          │
└───────────────┬───────────────────┬───────────────────┬────────────────┘
                │                   │                   │
      HTTP/JSON │ Port 8001         │ Port 8002         │ Port 8003
                ▼                   ▼                   ▼
     ┌─────────────────────┐┌─────────────────────┐┌─────────────────────┐
     │   Prescription AI   ││       X-Ray AI      ││      CT-Scan AI     │
     │  (FastAPI / Uvicorn)││  (FastAPI / Uvicorn)││  (FastAPI / Uvicorn)│
     │                     ││                     ││                     │
     │ • EasyOCR (PyTorch) ││ • Anatomical Router ││ • Gemini Multimodal │
     │ • CRAFT Text Detect ││   (10 Body Regions) ││   Vision 3.5/3.8    │
     │ • BiLSTM Recognizer ││ • ResNet-18 MSK     ││ • Zero-Hallucination│
     │ • Fuzzy Pharmacopeia││   Damage Detector   ││   Clinical Schema   │
     │ • OpenCV Preprocess ││ • DenseNet-121      ││ • Negative Document │
     │ • Dosage Regimens   ││   (18 Pathologies)  ││   Guardrail         │
     │ • ReportLab PDF     ││ • ReportLab PDF     ││ • ReportLab PDF     │
     └─────────────────────┘└─────────────────────┘└─────────────────────┘
                │                   │                   │
                └───────────────────┼───────────────────┘
                                    │
                                    ▼
                 ┌─────────────────────────────────────┐
                 │       Shared MongoDB Database       │
                 │     (127.0.0.1:27017/medvision_ai)  │
                 │                                     │
                 │  • patients collection              │
                 │  • analysisresults collection       │
                 │  • prescriptions collection         │
                 └─────────────────────────────────────┘
```

## 2. Core Subsystems

### 2.1 Central Gateway (Node.js / Express)
The gateway coordinates all client requests, handles image disk storage into segregated directories, routes inference payloads to the appropriate microservices, and enforces shared database storage with mandatory `patientId` references.

### 2.2 Storage Layer
Raw diagnostic media (radiographs, scans, prescriptions) and generated PDF reports are persisted to the filesystem in `storage/`:
- `storage/prescriptions/`
- `storage/xrays/`
- `storage/ct-scans/`
- `storage/reports/`
MongoDB stores only the metadata, URI references, and extracted structured JSON findings.

### 2.3 Microservice Adapters
Located in `ai-services/*/adapter/`:
- `service_adapter.py`: Acts as a non-intrusive runtime wrapper binding each service to its designated port without altering original files.
- `run_service.bat`: Enables isolated manual startup and verification for debugging.

