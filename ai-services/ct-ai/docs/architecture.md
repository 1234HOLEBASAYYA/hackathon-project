# Medical Image-Based Abnormality Detection and Visualization System
## System Architecture & Technical Specifications

### 1. Executive Summary
The **PneumoScan AI** system is a clinical decision support prototype developed to detect, visualize, and quantify pulmonary abnormalities (specifically Community-Acquired and Hospital-Acquired Pneumonia) from frontal chest radiographs (PA/AP views). 

The system leverages:
1. **Deep Transfer Learning with ResNet-18** fine-tuned on 5,856 pediatric chest X-ray images.
2. **Gradient-weighted Class Activation Mapping (Grad-CAM)** at the final residual block (`layer4[-1]`) providing explainable visual localization.
3. **Region of Interest (ROI) Extraction** computing pixel coordinates and relative spatial dimensions of lung opacifications.
4. **FastAPI Asynchronous Backend** offering sub-100ms inference with warm-loaded PyTorch state caching.
5. **Interactive Dual-Perspective Frontend (React + Vite)** presenting high-density clinical metrics for doctors alongside clear, compassionate guidance for patients.

---

### 2. End-to-End Workflow Diagram

```
[ Chest Radiograph (PNG/JPEG) ]
              │
              ▼
   [ Preprocessing & Normalization ]
   • Grayscale -> 3-Channel RGB
   • Resize to 224 x 224
   • Tensor conversion & ImageNet Mean/Std Normalization
              │
              ▼
    [ Pretrained ResNet-18 ]
    ├── Conv Layers (1 to 3) [Low-Level Radiographic Features]
    ├── Conv Layer 4         [Pathological Texture / Infiltrate Patterns]
    └── Custom Head: Dropout(0.3) -> Linear(512 -> 2)
              │
      ┌───────┴────────────────────────┐
      ▼                                ▼
[ Softmax Classifier ]         [ Grad-CAM Service ]
• P(NORMAL)                    • Hook into layer4 activations
• P(PNEUMONIA)                 • Backprop class gradient score
• Confidence Score             • Global Average Pooling of weights
• Severity Assessment          • ReLU & Bilinear Interpolation
      │                        • OpenCV JET Colormap Blending
      │                        • Spatial ROI Bounding Box Detection
      └───────┬────────────────────────┘
              ▼
    [ Fast API REST Server ]
    ├── POST /api/images/analyze
    ├── GET  /api/images/sample
    ├── GET  /api/images/metrics
    └── POST /api/prescriptions/analyze
              │
              ▼
    [ React Clinical Portal ]
    ├── Radiologist View: CAM Overlay, Sliders, Opacity Score, Metrics
    ├── Patient View: Simplified Findings, Home Care Checklist
    └── Prescription Rx Analyzer: Antimicrobial Entity Extraction
```

---

### 3. Model Engineering Details

| Property | Value |
| :--- | :--- |
| **Base Architecture** | Deep Residual Network (ResNet-18) |
| **Pretrained Weights** | PyTorch ImageNet Default (`ResNet18_Weights.DEFAULT`) |
| **Total Parameters** | 11,177,538 |
| **Trainable Parameters** | 10,494,466 (Layers 3, 4, and Classifier Head) |
| **Frozen Parameters** | 683,072 (Conv1, BN1, Layers 1-2) |
| **Loss Function** | Weighted Cross-Entropy Loss (`weight=[1.9448, 0.6730]`) |
| **Optimizer** | AdamW (`lr=1e-4`, `weight_decay=1e-4`) |
| **Input Shape** | `(Batch_Size, 3, 224, 224)` |
| **Output Classes** | `0: NORMAL`, `1: PNEUMONIA` |
| **Grad-CAM Target** | `model.layer4[-1]` (Conv2d 512 channels) |

---

### 4. API Endpoints Reference

#### `POST /api/images/analyze`
- **Payload**: `file` (multipart/form-data), `generate_gradcam` (bool), `alpha` (float 0.0 - 1.0)
- **Response**:
  - `prediction`: `"NORMAL"` or `"PNEUMONIA"`
  - `confidence`: Diagnostic certainty float (0.0 - 1.0)
  - `probabilities`: Normalized class distribution
  - `is_abnormal`: Boolean flag
  - `severity`: `"None"`, `"Mild"`, `"Moderate"`, or `"Severe"`
  - `clinical_finding`: Detailed radiologist assessment
  - `doctor_recommendation`: Suggested clinical next steps
  - `patient_explanation`: Patient-accessible summary
  - `gradcam`:
    - `overlay_b64`: Base64 PNG of blended image + heatmap
    - `heatmap_b64`: Base64 PNG of isolated activation map
    - `rois`: Array of detected bounding boxes `[x, y, width, height]`
    - `opacity_score`: Mean intensity index of active consolidation zones

#### `GET /api/images/sample?category=PNEUMONIA`
- Instant demonstration endpoint reading real held-out test scans.

#### `GET /api/images/metrics`
- Returns evaluated accuracy, precision, recall, F1, and confusion matrix.

#### `POST /api/prescriptions/analyze`
- Parses clinical notes, extracts drugs, posology, contraindications, and warnings.
