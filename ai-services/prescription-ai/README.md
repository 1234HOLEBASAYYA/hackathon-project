# Doctor Prescription OCR System

Production-minded prescription digitization pipeline that converts prescription images or PDFs into structured, validated clinical data using computer vision, OCR, NLP, medicine validation, and an interactive React review workspace.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)
![OpenCV](https://img.shields.io/badge/OpenCV-Image_Processing-5C3EE8?style=flat&logo=opencv&logoColor=white)
![Tesseract](https://img.shields.io/badge/Tesseract-OCR-red?style=flat)
![OpenFDA](https://img.shields.io/badge/OpenFDA-Drug_Validation-blue?style=flat)
![Tests](https://img.shields.io/badge/Tests-pytest-0A7EA4?style=flat)

> Medical safety note: this is an engineering prototype for OCR-assisted prescription review. It is not a clinical decision system and should not be used for patient care without professional validation, privacy review, audit logging, security hardening, and regulatory assessment.

## Why This Project Stands Out

Paper prescriptions are still common in healthcare workflows, but the downstream process is usually manual: pharmacists, front-desk teams, and clinical staff read the image, transcribe medication details, and reconcile drug names by hand. This project demonstrates how that workflow can be converted into an auditable software pipeline:

1. Accept image or PDF uploads.
2. Normalize noisy scans with OpenCV preprocessing.
3. Extract text with Tesseract and confidence-aware EasyOCR fallback.
4. Parse prescription fields into structured JSON.
5. Validate medicine names with OpenFDA plus local fuzzy matching.
6. Let a reviewer inspect, edit, and export the result from a React workspace.

The result is not just OCR text. It is a full-stack document intelligence workflow with quality checks, API boundaries, batch processing, confidence metadata, and human review built in.

## Core Capabilities

| Area | Implementation |
| --- | --- |
| Input handling | JPG, PNG, JPEG, and first-page PDF upload support |
| Image preparation | EXIF orientation correction, resizing, grayscale conversion, CLAHE contrast enhancement, denoising, deskewing, adaptive thresholding, morphology |
| OCR | Tesseract primary engine with automatic EasyOCR fallback when confidence is low |
| Quality gates | Minimum DPI checks, blur warnings, black-image rejection, preprocessing confidence score |
| Field extraction | Regex and spaCy-assisted parsing for patient, doctor, date, diagnosis, notes, medicines, dosage, frequency, and duration |
| Medicine validation | OpenFDA lookup, disk cache, fuzzy correction suggestions, flagged unknown medicines |
| LLM augmentation | Optional OpenAI, NVIDIA NIM, or Ollama refinement; optional direct vision extraction for OpenAI/Ollama vision-capable models |
| API | FastAPI endpoints for health checks, single OCR, synchronous batch OCR, and asynchronous batch jobs |
| Review UI | React/Vite workspace with upload, parameter controls, image comparison, editable structured cards, medicine table, confidence gauges, raw OCR highlighting, and JSON/text exports |
| Reliability | Request IDs, rate limiting, upload size limits, batch size limits, typed response shapes, pytest coverage |

## Architecture

```text
Image/PDF Upload
    |
    v
FastAPI Validation & Auth Layer
    - JWT token authorization (Depends)
    - file type and size checks
    - request ID middleware
    - rate limiting
    - EXIF/PDF decoding
    |
    v
OpenCV Preprocessing
    - resize
    - CLAHE contrast
    - denoise
    - deskew
    - adaptive threshold
    - morphology
    |
    v
OCR Pipeline
    - Tesseract primary OCR
    - EasyOCR fallback on low confidence
    - word boxes and confidence scores
    |
    v
Extraction Layer
    - patient/doctor/date extraction
    - medicine instruction parsing
    - confidence scoring
    - optional LLM refinement
    |
    v
Validation Layer
    - OpenFDA search
    - disk-backed cache
    - fuzzy suggestions
    |
    v
Database Persistence (MongoDB Atlas)
    - Save validated OCR extractions per user
    |
    v
React Review Workspace / JSON API Response
```

## Example API Response

```json
{
  "request_id": "7e9f6e9a-1c58-45c8-9c4b-7c3c38edb29e",
  "extracted_fields": {
    "patient_name": "John Doe",
    "patient_age": "45",
    "date": "12/05/2026",
    "doctor_name": "Dr. Alice Smith",
    "diagnosis": "Hypertension",
    "notes": "Review after one month",
    "medicines": [
      {
        "name": "Amlodipine",
        "dosage": "5mg",
        "frequency": "Once daily",
        "duration": "30 days",
        "confidence": 0.7,
        "confidences": {
          "name": 0.9,
          "dosage": 0.95,
          "frequency": 0.95,
          "duration": 0.0
        }
      }
    ],
    "confidences": {
      "patient_name": 0.9,
      "patient_age": 0.95,
      "date": 0.95,
      "doctor_name": 0.9,
      "diagnosis": 0.85,
      "notes": 0.85,
      "medicines": 0.7
    }
  },
  "ocr": {
    "raw_text": "Patient: John Doe\nAge: 45\nRx Tab Amlodipine 5mg OD for 30 days",
    "confidence": 86.4,
    "engine_used": "tesseract",
    "word_boxes": []
  },
  "medicine_validation": {
    "valid": true,
    "suggestions": ["AMLODIPINE"],
    "flagged": [],
    "closest_matches": {}
  },
  "confidence": {
    "ocr": 86.4,
    "preprocessing": 0.82
  }
}
```

## Repository Structure

```text
.
+-- src/
|   +-- api.py                 # FastAPI app, upload validation, batch jobs, static frontend mounting
|   +-- preprocessor.py        # OpenCV preprocessing and quality metadata
|   +-- ocr_engine.py          # Tesseract/EasyOCR engine abstraction and fallback logic
|   +-- extractor.py           # Structured field extraction and confidence scoring
|   +-- validator.py           # OpenFDA validation, caching, fuzzy suggestions
|   +-- llm.py                 # Optional OpenAI, NVIDIA NIM, and Ollama extraction helpers
|   +-- tesseract_config.py    # Local Tesseract path configuration helper
+-- frontend/
|   +-- src/App.jsx            # Main React review workspace
|   +-- src/components/        # Upload, dashboard, sandbox, and common UI components
|   +-- src/services/api.js    # API client
|   +-- package.json           # Vite/React scripts and dependencies
+-- tests/
|   +-- test_api.py            # FastAPI behavior tests
|   +-- test_extractor.py      # Field extraction tests
|   +-- test_preprocessor.py   # Image preprocessing tests
+-- main.py                    # Basic CLI pipeline
+-- main_enhanced.py           # Enhanced CLI with confidence/comparison output
+-- create_sample_prescription.py
+-- config.yaml                # Runtime OCR, preprocessing, API, validation, and LLM settings
+-- requirements.txt           # Python dependencies
+-- QUICK_START.md             # Short setup guide
+-- SETUP.md                   # Detailed environment setup
+-- PROJECT_GUIDE.md           # Learning-oriented architecture notes
```

## Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and configure MongoDB Atlas and JWT signing:
```bash
cp .env.example .env
# Edit .env with your MONGO_URI and JWT_SECRET settings
```

### 3. Install Tesseract OCR

```bash
# Windows
# Install from: https://github.com/UB-Mannheim/tesseract/wiki

# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

### 4. Verify the Environment

```bash
python test_project.py
pytest
```

### 5. Run the API

```bash
uvicorn src.api:app --reload
```

Open `http://127.0.0.1:8000/health` to confirm the backend is running.

### 6. Run the Frontend in Development

```bash
cd frontend
npm install
npm run dev
```

The React app runs through Vite during development. For single-port deployment through FastAPI, build the frontend first:

```bash
cd frontend
npm run build
cd ..
uvicorn src.api:app --reload
```

FastAPI will serve `frontend/dist` at the root path when the build directory exists.

## API Usage

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Single Prescription OCR

```bash
curl -X POST http://127.0.0.1:8000/ocr \
  -F "file=@images/sample_prescription.png"
```

### Single OCR With Runtime Settings

```bash
curl -X POST http://127.0.0.1:8000/ocr \
  -F "file=@images/sample_prescription.png" \
  -F "settings={\"preprocessing\":{\"resize_width\":1600,\"deskew\":true},\"llm\":{\"provider\":\"local\"}}"
```

### Synchronous Batch OCR

```bash
curl -X POST http://127.0.0.1:8000/ocr/batch \
  -F "files=@images/rx_1.png" \
  -F "files=@images/rx_2.png"
```

### Asynchronous Batch Job

```bash
curl -X POST http://127.0.0.1:8000/batch \
  -F "files=@images/rx_1.png" \
  -F "files=@images/rx_2.png"

curl http://127.0.0.1:8000/batch/<job_id>
```

## CLI Usage

Generate a sample prescription image:

```bash
python create_sample_prescription.py
```

Run the basic local OCR flow:

```bash
python main.py
```

Run the enhanced CLI flow with confidence reporting and before/after comparison output:

```bash
python main_enhanced.py
```

## Configuration

Most behavior is controlled from `config.yaml`:

```yaml
ocr:
  confidence_threshold: 60
  fallback_engine: easyocr
preprocessing:
  resize_width: 1600
  deskew: true
  denoise: true
api:
  max_file_size_mb: 10
  allowed_formats: [jpg, png, pdf]
  rate_limit_per_minute: 20
validation:
  fuzzy_threshold: 80
  cache_ttl_hours: 24
quality_check:
  min_dpi: 150
  blur_threshold: 100
llm:
  provider: local
  api_key_env: OPENAI_API_KEY
```

The API also accepts a `settings` form field containing JSON, so preprocessing and LLM behavior can be adjusted per request without editing code.

## Optional LLM Modes

The default mode is local and deterministic: OpenCV, OCR, spaCy, regex extraction, and OpenFDA validation. LLM calls are disabled unless configured.

Supported providers:

| Provider | Use case |
| --- | --- |
| `local` | No external LLM calls |
| `openai` | JSON-schema extraction refinement and direct vision extraction |
| `nvidia` | Text-based extraction refinement through NVIDIA NIM-compatible chat completions |
| `ollama` | Local OpenAI-compatible text or vision model endpoint |

Example request-time settings:

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "YOUR_KEY",
    "mode": "ocr_refinement",
    "clinical_context": "Patient reports fever and throat pain"
  }
}
```

For direct image-to-JSON extraction with a vision-capable model:

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-4o-mini",
    "mode": "direct_vision"
  }
}
```

## Testing

```bash
pytest
```

Current automated coverage focuses on:

- API health, request IDs, invalid format rejection, black-image rejection, and batch response shape
- Prescription field extraction across representative OCR text samples
- Confidence score bounds and null handling
- Optional OpenAI refinement behavior through mocked API calls
- Image preprocessing behavior

## Authentication & Persistence

This project features user authentication and persistent database storage utilizing MongoDB Atlas. 

### Features:
- **JWT-Based Authentication**: Registration and login endpoints secure the workspace environment.
- **MongoDB Atlas Persistence**: Extracted prescription OCR results are automatically associated with the authenticated user ID and archived in the `extractions` collection.
- **Review History**: Users can fetch their full history of prescription scans.

### MongoDB Atlas Setup Steps:
1. **Create an Account/Cluster**: Sign up on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and deploy a free-tier M0 database cluster.
2. **Configure Network Security**: Add `0.0.0.0/0` or your current IP address to the Atlas Network Access list to authorize remote client connections.
3. **Database Access User**: Create a database user with read and write permissions (Username & Password authentication).
4. **Acquire Connection URI**: Retrieve your database connection string and replace the placeholders in `.env`:
   ```bash
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/prescription_ocr?retryWrites=true&w=majority
   ```

## Engineering Highlights

- Clear separation between API transport, image preprocessing, OCR, extraction, validation, and UI concerns.
- Confidence metadata is preserved throughout the pipeline instead of returning a single opaque result.
- The medicine validator avoids repeated network calls with disk-backed OpenFDA caching.
- The API is designed for operational visibility with request IDs and explicit failure responses.
- The React interface supports human-in-the-loop correction, which is essential for safety-sensitive OCR workflows.
- Runtime configuration makes the system tunable without code edits, useful for comparing OCR and preprocessing strategies.

## Limitations and Responsible Use

- Handwritten prescriptions are inherently ambiguous; low-quality scans can still produce incorrect text.
- OpenFDA validation is strongest for drugs represented in FDA datasets and may not cover all regional brands.
- The implemented user authentication system is basic and lacks advanced features such as email verification, password reset, or rate-limiting on login/register endpoints.
- The project does not implement encryption-at-rest, audit trails, PHI redaction, or production observability.
- LLM modes can improve difficult extraction cases but must be treated as assistive, not authoritative.
- Clinical deployment would require domain expert validation, privacy controls, monitoring, and compliance review.

## Roadmap

- Add role-based access control (RBAC) for reviewer workflows.
- Add FHIR-compatible export format.
- Add queue-backed batch processing with durable job state.
- Add evaluation scripts for measuring extraction accuracy on labeled prescription datasets.
- Add Docker/Compose deployment once environment assumptions are finalized.

## License
MIT. Use, modify, and extend with attribution according to the license terms.
