# ⚡ AI PRESCRIPTION READER - QUICK START GUIDE

Fast, standalone AI-powered medical prescription OCR and clinical information extraction engine running on local GPU/CPU.

---

## 🚀 Live Application URLs

Both services are currently active:

- **Web Application UI**: [http://127.0.0.1:5173/](http://127.0.0.1:5173/) *(Vite Dev Server)*
- **Production Single-Port Mode**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) *(FastAPI serving API + built React frontend)*
- **Backend Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) *(Swagger UI)*

---

## 💻 How to Run the Code

### 1. Launch the Web Application & Server
```powershell
python main.py
```
*Starts the FastAPI backend on port 8000 and serves the built web interface.*

To start the Vite frontend development server separately:
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

### 2. Analyze a Prescription Directly from the CLI
You can pass any prescription image or PDF directly to `main.py`:

```powershell
python main.py tests/fixtures/actual_handwritten_prescription.png
```
Or with custom files:
```powershell
python main.py path/to/prescription.jpg
python main.py path/to/scanned_prescription.pdf
```

---

### 3. Run the Automated Test Suite
To verify OCR accuracy across printed, handwritten, PDF, blurry, and edge-case fixtures:

```powershell
python main.py --test
# or
python -m pytest tests/test_prescription_reader.py -v
```

---

## 📋 Extracted Clinical Fields

The system extracts full-page prescription information:
1. **Clinic / Hospital Institution Header**
2. **Doctor Information**: Name, Qualification, Specialization, Medical Reg / License #, Clinic, Contact Number
3. **Patient Details**: Name, Age, Gender, Address, Prescription Date, Patient ID / UHID
4. **Clinical Findings**: Diagnosis, Medical Advice, Follow-up instructions
5. **Prescribed Medications (10 attributes per entry)**:
   - Medicine Name
   - Strength (e.g. `650 mg`, `500 mg`)
   - Dosage (e.g. `10 ml`, `1 tablet`)
   - Frequency (e.g. `Twice daily (1-0-1)`, `Once daily (Night)`)
   - Duration (e.g. `5 days`, `3 days`)
   - Route (e.g. `Oral (Tablet)`, `Oral (Syrup)`)
   - Food Instructions (e.g. `Before food`, `After food`)
   - Special Instructions (e.g. `Take at bedtime`)
   - OCR Confidence %
   - Verification Status
