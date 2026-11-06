# MEDVISION-AI Database Schema Specification

**Database:** MongoDB (`mongodb://127.0.0.1:27017/medvision_ai`)  
**ODM:** Mongoose 8.x / PyMongo 4.x

---

## 1. Collection: `patients`
Tracks demographic identity anchors across all modalities.

| Field | Type | Description | Index |
|---|---|---|---|
| `_id` | ObjectId | MongoDB unique identifier | Primary Key |
| `patientId` | String | Unique clinical patient identifier (e.g. `P-1001`) | **Unique Index** |
| `name` | String | Full patient legal name | Indexed |
| `age` | Number | Patient age in years | |
| `gender` | String | Biological gender (`Male`, `Female`, `Other`) | |
| `contact` | String | Phone / contact details | |
| `bloodGroup` | String | Blood type (e.g. `O+`) | |
| `allergies` | Array of String | Documented drug or substance allergies | |
| `chronicConditions` | Array of String | Documented chronic medical conditions | |
| `createdAt` | Date | Timestamp of registration | |
| `updatedAt` | Date | Timestamp of last profile update | |

---

## 2. Collection: `analysisresults`
Consolidates diagnostic imaging studies and analyses across all modalities (Prescription, X-Ray, CT Scan).

| Field | Type | Description | Index |
|---|---|---|---|
| `_id` | ObjectId | MongoDB unique identifier | Primary Key |
| `analysisId` | String | Unique analysis identifier (e.g. `an_xray_...`) | **Unique Index** |
| `patientId` | String | Linked patient identifier | **Index** |
| `patient` | String | Secondary backward-compatible patient link | **Index** |
| `patientName` | String | Cached patient legal name | |
| `modality` | String | Modality: `prescription`, `xray`, `ct_scan` | **Index** |
| `reportTitle` | String | Formal report heading | |
| `status` | String | Analysis status (`completed`, `in-review`) | |
| `modelInfo` | Object | `{ modelName, version, device }` | |
| `fileMetadata` | Object | `{ originalFilename, storedFilename, storedPath, fileSize, mimeType }` | |
| `primaryFinding` | Mixed | Key diagnostic summary or primary condition | |
| `findings` | Mixed | Structured clinical findings, bounding boxes, observations | |
| `report` | Mixed | Full JSON payload returned by AI engine | |
| `specimenUrl` | String | URI pointing to annotated image or specimen | |
| `reportPdfUrl` | String | URI pointing to downloadable ReportLab PDF | |
| `createdAt` | Date | Analysis generation timestamp | **Index (Descending)** |

---

## 3. Collection: `prescriptions`
Stores granular extracted medication regimens from digital prescriptions.

| Field | Type | Description | Index |
|---|---|---|---|
| `_id` | ObjectId | MongoDB unique identifier | Primary Key |
| `prescriptionId` | String | Unique prescription identifier | **Unique Index** |
| `analysisId` | String | Linked analysis record | **Index** |
| `patientId` | String | Linked patient identifier | **Index** |
| `doctor` | Object | `{ name, qualification, specialization, clinicOrHospital }` | |
| `clinicHeader` | String | Extracted clinic / institution banner | |
| `diagnosis` | String | Presumptive clinical diagnosis | |
| `advice` | String | Medical advice and instructions | |
| `medications` | Array of Objects | `[{ medicineName, strength, dosage, route, frequency, duration, specialInstructions, confidence }]` | |
| `rawOcrText` | String | Full raw OCR transcription string | |
| `quality` | Object | DPI and quality gate assessment | |
| `createdAt` | Date | Timestamp of digitization | |

