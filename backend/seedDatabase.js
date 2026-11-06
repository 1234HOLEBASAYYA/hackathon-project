/**
 * MEDVISION-AI Comprehensive Database Seeder
 * Populates MongoDB with complete longitudinal clinical records for:
 * - Patient Profiles (P-1001, P-1002, P-1003)
 * - Doctor Prescriptions (Verified clinical tables, dosages, advice)
 * - Multi-Region X-Ray Diagnostic Studies (ResNet-18 & DenseNet-121)
 * - CT Clinical Vision Evaluations (Physical densities & differential findings)
 */

const mongoose = require('mongoose');
const Patient = require('./models/Patient');
const Prescription = require('./models/Prescription');
const AnalysisResult = require('./models/AnalysisResult');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/medvision_ai';

const PATIENTS = [
  {
    patientId: 'P-1001',
    name: 'Robert Miller',
    age: 58,
    gender: 'Male',
    contact: '+1 (555) 014-3829',
    bloodGroup: 'O+',
    allergies: ['Penicillin'],
    chronicConditions: ['Type 2 Diabetes', 'Essential Hypertension']
  },
  {
    patientId: 'P-1002',
    name: 'Elena Rostova',
    age: 42,
    gender: 'Female',
    contact: '+1 (555) 082-1940',
    bloodGroup: 'A+',
    allergies: ['Sulfa drugs'],
    chronicConditions: ['Mild Bronchial Asthma', 'Allergic Rhinitis']
  },
  {
    patientId: 'P-1003',
    name: 'Marcus Vance',
    age: 31,
    gender: 'Male',
    contact: '+1 (555) 099-2311',
    bloodGroup: 'B+',
    allergies: ['Aspirin'],
    chronicConditions: ['Post-Trauma Right Knee Arthralgia']
  }
];

const PRESCRIPTIONS = [
  {
    prescriptionId: 'rx_seed_p1001_01',
    analysisId: 'an_rx_seed_p1001_01',
    patientId: 'P-1001',
    patient: 'P-1001',
    patientName: 'Robert Miller',
    doctor: {
      name: 'Dr. Sarah Jenkins, MD',
      qualification: 'MBBS, MD (Cardiology)',
      specialization: 'Cardiometabolic Specialist',
      clinicOrHospital: 'Apollo Memorial Heart & Diabetes Center',
      registrationNumber: 'REG-CARD-883921',
      contactNumber: '+1 (555) 234-9000'
    },
    clinicHeader: 'Apollo Memorial Heart & Diabetes Center - Outpatient Clinic',
    diagnosis: 'Type 2 Diabetes Mellitus & Stage 1 Essential Hypertension',
    advice: 'Follow diabetic renal-sparing diet, 30 minutes daily aerobic exercise, record morning fasting blood sugars.',
    followUp: '4 weeks with HbA1c and serum creatinine panel',
    status: 'verified',
    rawOcrText: 'Apollo Memorial Heart Center\nDr. Sarah Jenkins MD\nPatient: Robert Miller (58M)\nDx: T2DM + HTN\nRx: Atorvastatin 20mg OD, Metformin 500mg BD, Ramipril 5mg OD\nReview in 4 weeks.',
    medications: [
      {
        medicineName: 'Atorvastatin Calcium',
        name: 'Atorvastatin Calcium',
        strength: '20mg',
        dosage: '1 tablet',
        route: 'Oral',
        frequency: 'Once daily (OD) at bedtime',
        duration: '30 days',
        foodInstructions: 'After dinner',
        specialInstructions: 'Lipid-lowering HMG-CoA reductase inhibitor',
        confidence: 98.5
      },
      {
        medicineName: 'Metformin Hydrochloride',
        name: 'Metformin Hydrochloride',
        strength: '500mg',
        dosage: '1 tablet',
        route: 'Oral',
        frequency: 'Twice daily (BD)',
        duration: '30 days',
        foodInstructions: 'With meals',
        specialInstructions: 'Insulin sensitizer; take with breakfast and dinner',
        confidence: 99.2
      },
      {
        medicineName: 'Ramipril',
        name: 'Ramipril',
        strength: '5mg',
        dosage: '1 capsule',
        route: 'Oral',
        frequency: 'Once daily (OD)',
        duration: '30 days',
        foodInstructions: 'Morning',
        specialInstructions: 'ACE inhibitor for cardioprotection and blood pressure control',
        confidence: 96.0
      }
    ],
    createdAt: new Date(Date.now() - 14 * 24 * 3600 * 1000)
  },
  {
    prescriptionId: 'rx_seed_p1002_01',
    analysisId: 'an_rx_seed_p1002_01',
    patientId: 'P-1002',
    patient: 'P-1002',
    patientName: 'Elena Rostova',
    doctor: {
      name: 'Dr. Robert Hayes, MD, FCCP',
      qualification: 'MBBS, MD, FCCP',
      specialization: 'Consultant Pulmonologist',
      clinicOrHospital: 'Metropolitan Pulmonary & Allergy Institute',
      registrationNumber: 'REG-PULM-447812',
      contactNumber: '+1 (555) 782-4110'
    },
    clinicHeader: 'Metropolitan Pulmonary Institute - Suite 402',
    diagnosis: 'Mild Persistent Asthma with Seasonal Allergic Rhinitis exacerbation',
    advice: 'Avoid known aerosol allergen triggers, practice peak expiratory flow monitoring, maintain good hydration.',
    followUp: '6 weeks with spirometry evaluation',
    status: 'verified',
    rawOcrText: 'Metropolitan Pulmonary Institute\nDr. Robert Hayes MD\nPatient: Elena Rostova (42F)\nDx: Asthma Exacerbation\nRx: Montelukast 10mg OD, Fluticasone 125mcg MDI, Levocetirizine 5mg HS.',
    medications: [
      {
        medicineName: 'Montelukast Sodium',
        name: 'Montelukast Sodium',
        strength: '10mg',
        dosage: '1 tablet',
        route: 'Oral',
        frequency: 'Once daily (OD) at bedtime',
        duration: '30 days',
        foodInstructions: 'Evening after food',
        specialInstructions: 'Leukotriene receptor antagonist',
        confidence: 97.4
      },
      {
        medicineName: 'Fluticasone Propionate Inhaler',
        name: 'Fluticasone Propionate',
        strength: '125mcg',
        dosage: '2 puffs',
        route: 'Inhalation',
        frequency: 'Twice daily (BD)',
        duration: '60 days',
        foodInstructions: 'Rinse mouth after inhalation',
        specialInstructions: 'Controller anti-inflammatory corticosteroid inhaler',
        confidence: 98.1
      },
      {
        medicineName: 'Levocetirizine Dihydrochloride',
        name: 'Levocetirizine',
        strength: '5mg',
        dosage: '1 tablet',
        route: 'Oral',
        frequency: 'Once daily (OD) at night',
        duration: '15 days',
        foodInstructions: 'At bedtime',
        specialInstructions: 'Non-sedating second-generation antihistamine',
        confidence: 95.8
      }
    ],
    createdAt: new Date(Date.now() - 10 * 24 * 3600 * 1000)
  },
  {
    prescriptionId: 'rx_seed_p1003_01',
    analysisId: 'an_rx_seed_p1003_01',
    patientId: 'P-1003',
    patient: 'P-1003',
    patientName: 'Marcus Vance',
    doctor: {
      name: 'Dr. Kenneth Vance, MD',
      qualification: 'MBBS, MS (Ortho), Fellowship Sports Med',
      specialization: 'Orthopedic Sports Medicine Consultant',
      clinicOrHospital: 'City Orthopedic & Joint Reconstruction Pavilion',
      registrationNumber: 'REG-ORTH-331098',
      contactNumber: '+1 (555) 890-4422'
    },
    clinicHeader: 'City Orthopedic Pavilion - Sports Medicine Clinic',
    diagnosis: 'Acute Right Knee Strain / Medial Collateral Ligament (MCL) Grade 1 Sprain',
    advice: 'R.I.C.E. protocol (Rest, Ice 15 mins TID, Compression sleeve, Elevation), avoid high-impact running.',
    followUp: '2 weeks with clinical ligament laxity assessment',
    status: 'verified',
    rawOcrText: 'City Orthopedic Pavilion\nDr. Kenneth Vance MS Ortho\nPatient: Marcus Vance (31M)\nDx: Right Knee Sprain\nRx: Celecoxib 200mg OD, Paracetamol 650mg SOS, Thiocolchicoside 4mg BD.',
    medications: [
      {
        medicineName: 'Celecoxib',
        name: 'Celecoxib',
        strength: '200mg',
        dosage: '1 capsule',
        route: 'Oral',
        frequency: 'Once daily (OD)',
        duration: '7 days',
        foodInstructions: 'After breakfast',
        specialInstructions: 'COX-2 selective nonsteroidal anti-inflammatory',
        confidence: 98.9
      },
      {
        medicineName: 'Paracetamol',
        name: 'Paracetamol',
        strength: '650mg',
        dosage: '1 tablet',
        route: 'Oral',
        frequency: 'As needed (SOS, max TID)',
        duration: '5 days',
        foodInstructions: 'Post-prandial',
        specialInstructions: 'Analgesic for breakthrough joint pain',
        confidence: 99.4
      },
      {
        medicineName: 'Thiocolchicoside',
        name: 'Thiocolchicoside',
        strength: '4mg',
        dosage: '1 capsule',
        route: 'Oral',
        frequency: 'Twice daily (BD)',
        duration: '5 days',
        foodInstructions: 'After food',
        specialInstructions: 'Centrally-acting muscle relaxant',
        confidence: 96.2
      }
    ],
    createdAt: new Date(Date.now() - 5 * 24 * 3600 * 1000)
  }
];

const ANALYSIS_RESULTS = [
  // P-1001 Prescriptions & Radiographs
  {
    analysisId: 'an_rx_seed_p1001_01',
    patientId: 'P-1001',
    patient: 'P-1001',
    patientName: 'Robert Miller',
    modality: 'prescription',
    reportTitle: 'Clinical Prescription OCR & Medicine Extraction Report',
    status: 'completed',
    modelInfo: {
      modelName: 'EasyOCR CRAFT + BiLSTM + Clinical Grammar Parser',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      medicineName: 'Atorvastatin Calcium',
      strength: '20mg',
      frequency: 'Once daily (OD)'
    },
    findings: {
      summary: 'Verified prescription with 3 extracted medications for cardiometabolic management.',
      clinicalImpression: 'Prescription orders for Atorvastatin 20mg, Metformin 500mg, and Ramipril 5mg verified against pharmacy grammar rules.',
      doctorName: 'Dr. Sarah Jenkins, MD',
      diagnosis: 'Type 2 Diabetes Mellitus & Stage 1 Essential Hypertension',
      medicationsCount: 3
    },
    specimenUrl: '/assets/images/sample_prescription.png',
    createdAt: new Date(Date.now() - 14 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_xray_seed_p1001_01',
    patientId: 'P-1001',
    patient: 'P-1001',
    patientName: 'Robert Miller',
    modality: 'xray',
    reportTitle: 'Multi-Region Radiograph Analysis (CHEST)',
    status: 'completed',
    modelInfo: {
      modelName: 'TorchXRayVision DenseNet-121 & Gemini 3.5 Multimodal Vision',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      region: 'Chest',
      isAbnormal: false,
      affectedBone: 'Intact Thoracic & Cardiopulmonary Anatomy',
      confidence: 0.96,
      regionConfidence: 0.98,
      summary: 'Normal radiographic study of the chest with clear bilateral lung fields and physiological cardiothoracic ratio.'
    },
    findings: {
      anatomicalRegion: 'Chest',
      regionConfidence: 0.98,
      isAbnormal: false,
      confidence: 0.96,
      affectedBone: 'Intact Thoracic Architecture',
      boundingBoxPixels: [],
      clinicalImpression: 'No acute pulmonary infiltrate, consolidation, or pleural effusion visualized. Normal cardiac silhouette.',
      observations: [
        'Bilateral costophrenic angles are sharp and clear.',
        'Mediastinal contours and hila are within physiological limits.',
        'Skeletal structures of the thoracic cage demonstrate no focal lytic or sclerotic lesions.'
      ]
    },
    specimenUrl: '/assets/images/sample_wrist.png',
    createdAt: new Date(Date.now() - 11 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_ct_seed_p1001_01',
    patientId: 'P-1001',
    patient: 'P-1001',
    patientName: 'Robert Miller',
    modality: 'ct_scan',
    reportTitle: 'AI-Assisted CT Thorax Cross-Sectional Evaluation',
    status: 'completed',
    modelInfo: {
      modelName: 'Gemini 3.5 Multimodal Clinical Vision',
      version: '2.0.0',
      device: 'cloud-vision'
    },
    primaryFinding: {
      finding: 'Clear parenchymal attenuation across bilateral lung windows',
      certainty: 'observed'
    },
    findings: {
      detectedModality: 'ct_scan',
      isCompatibleCtScan: true,
      summary: 'High-resolution axial CT evaluation demonstrating preserved parenchymal architecture and absence of bronchiectasis or focal masses.',
      visualObservations: [
        {
          observation: 'Uniform lung parenchymal attenuation',
          location: 'Bilateral lung fields',
          description: 'Normal pulmonary attenuation without mosaic perfusion or ground-glass opacification.',
          certainty: 'observed'
        },
        {
          observation: 'Tracheobronchial arborization',
          location: 'Central mediastinum',
          description: 'Trachea and major bronchi patent with intact cartilaginous margins.',
          certainty: 'observed'
        }
      ],
      potentialFindings: [
        {
          finding: 'Normal physiological thoracic CT scan',
          certainty: 'uncertain',
          description: 'No evidence of acute thromboembolism, architectural distortion, or pleural thickening.',
          supporting_visual_observation: 'Clear vascular branching patterns throughout periphery'
        }
      ],
      recommendations: [
        'Maintain routine annual clinical surveillance for cardiovascular risk management.',
        'Correlate with periodic spirometry if dyspnea arises.'
      ],
      limitations: [
        'Single slice axial perspective. Complete volumetric reconstruction recommended for full lesion screening.'
      ]
    },
    specimenUrl: '/assets/images/sample_ct.jpg',
    createdAt: new Date(Date.now() - 7 * 24 * 3600 * 1000)
  },

  // P-1002 Prescriptions & Radiographs
  {
    analysisId: 'an_rx_seed_p1002_01',
    patientId: 'P-1002',
    patient: 'P-1002',
    patientName: 'Elena Rostova',
    modality: 'prescription',
    reportTitle: 'Clinical Prescription OCR & Medicine Extraction Report',
    status: 'completed',
    modelInfo: {
      modelName: 'EasyOCR CRAFT + BiLSTM + Clinical Grammar Parser',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      medicineName: 'Fluticasone Propionate Inhaler',
      strength: '125mcg',
      frequency: 'Twice daily (BD)'
    },
    findings: {
      summary: 'Verified prescription with 3 extracted medications for pulmonary asthma maintenance.',
      clinicalImpression: 'Prescription orders for Montelukast 10mg, Fluticasone 125mcg MDI, and Levocetirizine 5mg verified against pharmacy grammar rules.',
      doctorName: 'Dr. Robert Hayes, MD, FCCP',
      diagnosis: 'Mild Persistent Asthma with Seasonal Allergic Rhinitis exacerbation',
      medicationsCount: 3
    },
    specimenUrl: '/assets/images/sample_prescription.png',
    createdAt: new Date(Date.now() - 10 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_xray_seed_p1002_01',
    patientId: 'P-1002',
    patient: 'P-1002',
    patientName: 'Elena Rostova',
    modality: 'xray',
    reportTitle: 'Multi-Region Radiograph Analysis (CHEST)',
    status: 'completed',
    modelInfo: {
      modelName: 'TorchXRayVision DenseNet-121 & Gemini 3.5 Multimodal Vision',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      region: 'Chest',
      isAbnormal: false,
      affectedBone: 'Intact Bronchovascular Markings',
      confidence: 0.94,
      regionConfidence: 0.97,
      summary: 'Normal radiographic study of the thorax. Minimal peribronchial thickening consistent with history of asthma.'
    },
    findings: {
      anatomicalRegion: 'Chest',
      regionConfidence: 0.97,
      isAbnormal: false,
      confidence: 0.94,
      affectedBone: 'Intact Bronchovascular Markings',
      boundingBoxPixels: [],
      clinicalImpression: 'No pneumothorax, focal lobar consolidation, or pleural effusion identified. Thoracic volume preserved.',
      observations: [
        'Normal pulmonary inflation without hyperlucency.',
        'Costophrenic angles preserved bilaterally.',
        'Cardiac contour normal in size and position.'
      ]
    },
    specimenUrl: '/assets/images/sample_wrist.png',
    createdAt: new Date(Date.now() - 8 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_ct_seed_p1002_01',
    patientId: 'P-1002',
    patient: 'P-1002',
    patientName: 'Elena Rostova',
    modality: 'ct_scan',
    reportTitle: 'AI-Assisted Cranial CT Slice Evaluation',
    status: 'completed',
    modelInfo: {
      modelName: 'Gemini 3.5 Multimodal Clinical Vision',
      version: '2.0.0',
      device: 'cloud-vision'
    },
    primaryFinding: {
      finding: 'Symmetrical cerebral parenchymal attenuation',
      certainty: 'observed'
    },
    findings: {
      detectedModality: 'ct_scan',
      isCompatibleCtScan: true,
      summary: 'Axial cranial CT demonstrating preserved gray-white differentiation, normal ventricular caliber, and absence of mass effect.',
      visualObservations: [
        {
          observation: 'Calvarial integrity',
          location: 'Cranial vault',
          description: 'Intact diploic space without depressed fracture or osteolytic focus.',
          certainty: 'observed'
        },
        {
          observation: 'Ventricular symmetry',
          location: 'Lateral ventricles',
          description: 'Frontal and occipital horns symmetric with no midline shift.',
          certainty: 'observed'
        }
      ],
      potentialFindings: [
        {
          finding: 'Normal intracranial CT scan appearance',
          certainty: 'uncertain',
          description: 'No acute intra- or extra-axial hemorrhage, hydrocephalus, or midline shift.',
          supporting_visual_observation: 'Preserved sulcal-gyral pattern'
        }
      ],
      recommendations: [
        'Clinical correlation with headache symptom diary if episodic cephalea occurs.',
        'Formal evaluation by board-certified radiologist.'
      ],
      limitations: [
        'Single 2D slice; volumetric helical review indicated for complete posterior fossa inspection.'
      ]
    },
    specimenUrl: '/assets/images/sample_ct.jpg',
    createdAt: new Date(Date.now() - 4 * 24 * 3600 * 1000)
  },

  // P-1003 Prescriptions & Radiographs
  {
    analysisId: 'an_rx_seed_p1003_01',
    patientId: 'P-1003',
    patient: 'P-1003',
    patientName: 'Marcus Vance',
    modality: 'prescription',
    reportTitle: 'Clinical Prescription OCR & Medicine Extraction Report',
    status: 'completed',
    modelInfo: {
      modelName: 'EasyOCR CRAFT + BiLSTM + Clinical Grammar Parser',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      medicineName: 'Celecoxib',
      strength: '200mg',
      frequency: 'Once daily (OD)'
    },
    findings: {
      summary: 'Verified prescription with 3 extracted medications for orthopedic sports injury management.',
      clinicalImpression: 'Prescription orders for Celecoxib 200mg, Paracetamol 650mg, and Thiocolchicoside 4mg verified against pharmacy grammar rules.',
      doctorName: 'Dr. Kenneth Vance, MD',
      diagnosis: 'Acute Right Knee Strain / Medial Collateral Ligament (MCL) Grade 1 Sprain',
      medicationsCount: 3
    },
    specimenUrl: '/assets/images/sample_prescription.png',
    createdAt: new Date(Date.now() - 5 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_xray_seed_p1003_01',
    patientId: 'P-1003',
    patient: 'P-1003',
    patientName: 'Marcus Vance',
    modality: 'xray',
    reportTitle: 'Multi-Region Radiograph Analysis (WRIST)',
    status: 'completed',
    modelInfo: {
      modelName: 'Multi-Task ResNet-18 MSK Detector & TorchXRayVision DenseNet-121',
      version: '2.0.0',
      device: 'cpu'
    },
    primaryFinding: {
      region: 'Wrist',
      isAbnormal: false,
      affectedBone: 'Distal Radius and Ulna Intact',
      confidence: 0.95,
      regionConfidence: 0.97,
      summary: 'Normal radiographic study of the wrist joint. Well-preserved carpal alignment without acute fracture or dislocation.'
    },
    findings: {
      anatomicalRegion: 'Wrist',
      regionConfidence: 0.97,
      isAbnormal: false,
      confidence: 0.95,
      affectedBone: 'Distal Radius & Ulna Architecture',
      boundingBoxPixels: [],
      clinicalImpression: 'No radiocarpal or intercarpal subluxation. Cortical surfaces smooth and intact.',
      observations: [
        'Scaphoid, lunate, and triquetrum appear intact.',
        'Distal radioulnar joint space is anatomic.',
        'No soft tissue swelling over the dorsal wrist compartment.'
      ]
    },
    specimenUrl: '/assets/images/sample_wrist.png',
    createdAt: new Date(Date.now() - 3 * 24 * 3600 * 1000)
  },
  {
    analysisId: 'an_ct_seed_p1003_01',
    patientId: 'P-1003',
    patient: 'P-1003',
    patientName: 'Marcus Vance',
    modality: 'ct_scan',
    reportTitle: 'AI-Assisted Musculoskeletal CT Evaluation',
    status: 'completed',
    modelInfo: {
      modelName: 'Gemini 3.5 Multimodal Clinical Vision',
      version: '2.0.0',
      device: 'cloud-vision'
    },
    primaryFinding: {
      finding: 'Cortical bone perimeter integrity preserved',
      certainty: 'observed'
    },
    findings: {
      detectedModality: 'ct_scan',
      isCompatibleCtScan: true,
      summary: 'Cross-sectional bone window CT confirming intact osseous margins and absence of intra-articular loose bodies.',
      visualObservations: [
        {
          observation: 'Cortical margins',
          location: 'Articular surfaces',
          description: 'Uniform cortical density with preserved subchondral bone plate.',
          certainty: 'observed'
        },
        {
          observation: 'Trabecular bone architecture',
          location: 'Metaphyseal zone',
          description: 'Normal cancellous bone attenuation without osteolytic geographic lesion.',
          certainty: 'observed'
        }
      ],
      potentialFindings: [
        {
          finding: 'Normal osseous anatomy with no macroscopic fracture',
          certainty: 'uncertain',
          description: 'Bone window reveals intact structural contours; soft-tissue ligamentous evaluation requires clinical MRI correlation.',
          supporting_visual_observation: 'Continuous cortical margins across articular facets'
        }
      ],
      recommendations: [
        'Recommend MRI knee evaluation if ligamentous/meniscal symptoms persist beyond 2 weeks.',
        'Formal radiological review by MSK imaging consultant.'
      ],
      limitations: [
        'CT scan emphasizes osseous anatomy; cruciate and collateral ligaments require MRI for definitive staging.'
      ]
    },
    specimenUrl: '/assets/images/sample_ct.jpg',
    createdAt: new Date(Date.now() - 1 * 24 * 3600 * 1000)
  }
];

async function seedDatabase() {
  console.log('Connecting to MongoDB at:', MONGODB_URI);
  await mongoose.connect(MONGODB_URI);
  console.log('Connected successfully.\n');

  // 1. Seed Patients
  console.log('[1/3] Upserting Patient Profiles...');
  for (const pat of PATIENTS) {
    await Patient.findOneAndUpdate(
      { patientId: pat.patientId },
      { $set: pat },
      { upsert: true, new: true }
    );
    console.log(`  * Patient ${pat.patientId} (${pat.name}) synced.`);
  }

  // 2. Seed Prescriptions
  console.log('\n[2/3] Upserting Verified Prescriptions...');
  for (const rx of PRESCRIPTIONS) {
    await Prescription.findOneAndUpdate(
      { prescriptionId: rx.prescriptionId },
      { $set: rx },
      { upsert: true, new: true }
    );
    console.log(`  * Prescription ${rx.prescriptionId} for ${rx.patientName} (${rx.patientId}) synced.`);
  }

  // 3. Seed Analysis Results (All Modalities)
  console.log('\n[3/3] Upserting Diagnostic Analysis Results (Prescription, X-Ray, CT Scan)...');
  for (const ar of ANALYSIS_RESULTS) {
    await AnalysisResult.findOneAndUpdate(
      { analysisId: ar.analysisId },
      { $set: ar },
      { upsert: true, new: true }
    );
    console.log(`  * Analysis ${ar.analysisId} [${ar.modality.toUpperCase()}] for ${ar.patientName} (${ar.patientId}) synced.`);
  }

  const patientCount = await Patient.countDocuments();
  const rxCount = await Prescription.countDocuments();
  const analysisCount = await AnalysisResult.countDocuments();

  console.log('\n==========================================================');
  console.log(' DATABASE SEEDING COMPLETED SUCCESSFULLY!');
  console.log(` - Total Registered Patients: ${patientCount}`);
  console.log(` - Total Prescriptions:       ${rxCount}`);
  console.log(` - Total Diagnostic Analyses: ${analysisCount}`);
  console.log('==========================================================\n');

  await mongoose.disconnect();
  process.exit(0);
}

seedDatabase().catch(err => {
  console.error('Seeding failed:', err);
  process.exit(1);
});

