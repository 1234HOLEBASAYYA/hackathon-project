# MEDVISION-AI API Documentation

Base URL: `http://localhost:3000`

---

## 1. System Health
### `GET /api/health`
Aggregated health check querying MongoDB connection status and pinging all 3 AI microservices.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "platform": "MEDVISION-AI Unified Diagnostic Platform",
  "version": "1.0.0",
  "gateway": { "port": 3000, "status": "active" },
  "database": { "type": "MongoDB", "status": "connected" },
  "services": {
    "prescriptionAi": { "status": "healthy", "url": "http://127.0.0.1:8001" },
    "xrayAi": { "status": "healthy", "url": "http://127.0.0.1:8002" },
    "ctAi": { "status": "healthy", "url": "http://127.0.0.1:8003" }
  }
}
```

---

## 2. Patients API
### `GET /api/patients`
Retrieves registered patients list.

### `POST /api/patients`
Registers or updates patient profile.
**Body (JSON):**
```json
{
  "patientId": "P-1001",
  "name": "Robert Miller",
  "age": 58,
  "gender": "Male",
  "contact": "+1-555-0143",
  "allergies": ["Penicillin"],
  "chronicConditions": ["Type 2 Diabetes"]
}
```

### `GET /api/patients/:patientId/timeline`
Retrieves the complete consolidated longitudinal timeline for a given patient containing all Prescription, X-Ray, and CT Scan studies.

---

## 3. Prescription Analysis API
### `POST /api/analysis/prescription/analyze`
Accepts a prescription scan, executes EasyOCR, parses fields, and saves to MongoDB.
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: Image (PNG, JPG) or PDF file
  - `patientId`: String
  - `patientName`: String (optional)

**Response:**
```json
{
  "status": "success",
  "data": {
    "analysisId": "an_rx_...",
    "prescriptionId": "...",
    "patientId": "P-1001",
    "doctor": { "name": "Dr. Sarah Jenkins", "specialization": "Cardiologist" },
    "medications": [
      {
        "medicineName": "Atorvastatin",
        "strength": "20mg",
        "frequency": "Once daily (Night)",
        "duration": "30 days",
        "confidence": 100.0
      }
    ],
    "rawText": "...",
    "specimenUrl": "/storage/prescriptions/...",
    "savedToDatabase": true
  }
}
```

---

## 4. Multi-Region X-Ray Analysis API
### `POST /api/analysis/xray/analyze`
Ingests radiograph, runs anatomical router, MSK fracture regressor, and saves to MongoDB.
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: PNG, JPG, or DICOM radiograph
  - `patientId`: String

**Response:**
```json
{
  "status": "success",
  "data": {
    "analysisId": "an_xray_...",
    "patientId": "P-1001",
    "modality": "xray",
    "anatomicalRegion": "Wrist",
    "regionConfidence": 0.638,
    "isAbnormal": true,
    "confidence": 0.638,
    "affectedBone": "distal_radius",
    "boundingBoxPixels": [252, 389, 313, 445],
    "specimenUrl": "http://127.0.0.1:8002/static/results/specimen_....jpg",
    "reportPdfUrl": "http://127.0.0.1:8002/static/reports/report_....pdf",
    "savedToDatabase": true
  }
}
```

---

## 5. CT-Scan Clinical Vision API
### `POST /api/analysis/ct/analyze`
Ingests CT scan slice, applies Lanczos antialiased scaling, executes Gemini clinical vision, and saves observations to MongoDB.
- **Content-Type:** `multipart/form-data`
- **Fields:**
  - `file`: PNG or JPG CT slice
  - `patientId`: String

**Response:**
```json
{
  "status": "success",
  "data": {
    "analysisId": "an_ct_...",
    "patientId": "P-1001",
    "modality": "ct_scan",
    "reportTitle": "AI-Assisted CT Image Analysis Report",
    "visualObservations": [
      {
        "density_or_structure": "Pulmonary soft tissue nodule",
        "anatomical_location": "Right upper lobe",
        "observation_summary": "Circumscribed non-calcified density"
      }
    ],
    "potentialFindings": [
      {
        "finding_or_condition": "Indeterminate pulmonary nodule",
        "certainty": "Uncertain / Differential",
        "reasoning": "Visible soft tissue nodular attenuation requiring follow-up."
      }
    ],
    "savedToDatabase": true
  }
}
```

