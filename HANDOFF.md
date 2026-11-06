# MEDVISION-AI — Developer Handoff Document

## 1. Directory Overview
- `backend/`: Central Express gateway coordinating MongoDB and the three AI microservices.
- `frontend/`: Vanilla HTML/CSS/JS single-origin clinical UI served by Express on port 3000.
- `ai-services/`:
  - `prescription-ai/`: Original prescription project preserving weights and code, wrapped by `adapter/service_adapter.py` on port 8001.
  - `xray-ai/`: Original multi-region radiograph project preserving ResNet and DenseNet checkpoints, wrapped on port 8002.
  - `ct-ai/`: Original CT scan clinical vision project preserving model weights and Gemini prompts, wrapped on port 8003.
- `storage/`: Holds uploaded binaries and generated PDF reports.
- `start-all.bat`: Orchestrates all services and launches the platform.

## 2. Configuration & Secrets
All secrets and environment variables are centrally managed in `.env` in the root of `MEDVISION-AI/`:
- `GEMINI_API_KEY`: API key for Gemini Clinical Vision calls.
- `MONGODB_URI`: Local MongoDB connection string (`mongodb://127.0.0.1:27017/medvision_ai`).
- `PORT`: Gateway listener port (`3000`).

## 3. Operational Tips
- If an AI microservice needs independent debugging or retraining, navigate to its folder in `ai-services/<name>` and run its native CLI or tests without affecting other services.
- All patient diagnostic records are indexed by `patientId` in the `analysisresults` and `prescriptions` collections in MongoDB.

