const path = require('path');
const fs = require('fs');
const AnalysisResult = require('../models/AnalysisResult');
const Prescription = require('../models/Prescription');
const Patient = require('../models/Patient');
const { analyzePrescription } = require('../services/prescriptionService');
const { successResponse, errorResponse } = require('../utils/responseFormatter');

async function handlePrescriptionAnalysis(req, res, next) {
  try {
    if (!req.file) {
      return errorResponse(res, 'No prescription file provided. Please upload an image or PDF.', 400);
    }

    const patientId = req.body.patientId || req.body.patient_id || 'guest_patient';
    const patientName = req.body.patientName || req.body.patient_name || 'Demo Patient';

    // Auto-upsert patient if does not exist
    if (patientId !== 'guest_patient') {
      await Patient.findOneAndUpdate(
        { patientId },
        { $setOnInsert: { patientId, name: patientName } },
        { upsert: true, new: true }
      );
    }

    const filePath = req.file.path;
    const originalFilename = req.file.originalname;

    // Call Prescription AI Service (:8001)
    const aiResult = await analyzePrescription(filePath, originalFilename, patientId);

    const prescriptionId = aiResult.prescription_id || aiResult.id || `rx_${Date.now()}`;
    const analysisId = `an_rx_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 6)}`;

    // Normalize medications list
    const rawMeds = aiResult.medicines || aiResult.medications || [];
    const normalizedMeds = rawMeds.map(m => ({
      medicineName: m.medicine_name || m.name || 'Unknown Medication',
      name: m.medicine_name || m.name || 'Unknown Medication',
      strength: m.strength || 'Not detected',
      dosage: m.dosage || 'Not detected',
      route: m.route || 'Oral',
      frequency: m.frequency || 'Not detected',
      duration: m.duration || 'Not detected',
      foodInstructions: m.food_instructions || m.foodInstructions || 'Not detected',
      specialInstructions: m.special_instructions || m.specialInstructions || 'None',
      confidence: typeof m.confidence === 'number' ? m.confidence : (parseFloat(m.confidence) || 85.0)
    }));

    // Save to Prescription collection
    const prescriptionDoc = new Prescription({
      prescriptionId,
      analysisId,
      patientId,
      patient: patientId,
      patientName: (aiResult.patient && aiResult.patient.name) ? aiResult.patient.name : patientName,
      doctor: aiResult.doctor || {},
      clinicHeader: aiResult.clinic_header || '',
      diagnosis: aiResult.diagnosis || 'Clinical Prescription Review',
      advice: aiResult.advice || '',
      followUp: aiResult.follow_up || '',
      medications: normalizedMeds,
      rawOcrText: aiResult.raw_text || '',
      quality: aiResult.quality || {},
      filename: originalFilename,
      status: 'completed'
    });

    await Prescription.findOneAndUpdate(
      { prescriptionId },
      { $set: prescriptionDoc.toObject() },
      { upsert: true, new: true }
    );

    // Save to unified AnalysisResult collection
    const recordDoc = {
      analysisId,
      patientId,
      patient: patientId,
      patientName: prescriptionDoc.patientName,
      modality: 'prescription',
      reportTitle: 'Clinical Prescription OCR & Medicine Extraction Report',
      status: 'completed',
      modelInfo: {
        modelName: 'EasyOCR (CRAFT + BiLSTM) & NLP Grammar Extractor',
        version: '1.0.0',
        device: aiResult.device || 'gpu'
      },
      fileMetadata: {
        originalFilename,
        storedFilename: req.file.filename,
        storedPath: `/storage/prescriptions/${req.file.filename}`,
        fileSize: req.file.size,
        mimeType: req.file.mimetype
      },
      primaryFinding: {
        totalMedications: normalizedMeds.length,
        primaryMedication: normalizedMeds[0] ? normalizedMeds[0].medicineName : 'None',
        doctor: prescriptionDoc.doctor.name || 'Not detected'
      },
      findings: {
        doctor: prescriptionDoc.doctor,
        patientDetails: aiResult.patient || {},
        clinicHeader: aiResult.clinic_header,
        diagnosis: aiResult.diagnosis,
        advice: aiResult.advice,
        followUp: aiResult.follow_up,
        medications: normalizedMeds,
        boundingBoxes: aiResult.bounding_boxes || []
      },
      report: aiResult,
      specimenUrl: `/storage/prescriptions/${req.file.filename}`,
      filename: originalFilename
    };

    await AnalysisResult.findOneAndUpdate(
      { analysisId },
      { $set: recordDoc },
      { upsert: true, new: true }
    );

    return successResponse(res, {
      analysisId,
      prescriptionId,
      patientId,
      modality: 'prescription',
      doctor: prescriptionDoc.doctor,
      patient: aiResult.patient || {},
      clinicHeader: aiResult.clinic_header,
      diagnosis: aiResult.diagnosis,
      advice: aiResult.advice,
      medications: normalizedMeds,
      quality: aiResult.quality || {},
      rawText: aiResult.raw_text || '',
      specimenUrl: `/storage/prescriptions/${req.file.filename}`,
      savedToDatabase: true
    }, 'Prescription processed, structured and persisted to MongoDB successfully', 200);

  } catch (error) {
    console.error('[PrescriptionController Error]', error.message);
    return errorResponse(res, `Prescription processing failed: ${error.message}`, 500, error.response ? error.response.data : null);
  }
}

async function updatePrescription(req, res, next) {
  try {
    const { prescriptionId } = req.params;
    const { medications, doctor, diagnosis, advice, followUp, patientName, patientAge } = req.body;

    const prescription = await Prescription.findOne({ prescriptionId });
    if (!prescription) {
      return errorResponse(res, `Prescription with ID ${prescriptionId} not found`, 404);
    }

    if (medications) prescription.medications = medications;
    if (doctor) prescription.doctor = { ...prescription.doctor, ...doctor };
    if (diagnosis !== undefined) prescription.diagnosis = diagnosis;
    if (advice !== undefined) prescription.advice = advice;
    if (followUp !== undefined) prescription.followUp = followUp;
    if (patientName) prescription.patientName = patientName;
    if (patientAge !== undefined) prescription.patientAge = patientAge;
    prescription.status = 'verified';

    await prescription.save();

    // Also update associated AnalysisResult if present
    if (prescription.analysisId) {
      const updateData = {
        'findings.medications': prescription.medications,
        'findings.doctor': prescription.doctor,
        'findings.diagnosis': prescription.diagnosis,
        'findings.advice': prescription.advice,
        'findings.followUp': prescription.followUp,
        'primaryFinding.totalMedications': prescription.medications.length,
        'primaryFinding.primaryMedication': prescription.medications[0]?.medicineName || 'None',
        patientName: prescription.patientName
      };
      await AnalysisResult.findOneAndUpdate(
        { analysisId: prescription.analysisId },
        { $set: updateData }
      );
    }

    return successResponse(res, prescription, 'Prescription verified and updated successfully', 200);
  } catch (error) {
    console.error('[PrescriptionController Update Error]', error.message);
    return errorResponse(res, `Failed to update prescription: ${error.message}`, 500);
  }
}

async function getPrescriptionHistory(req, res, next) {
  try {
    const { patientId } = req.params;
    const history = await Prescription.find({
      $or: [{ patientId }, { patient: patientId }]
    }).sort({ createdAt: -1 });

    return successResponse(res, history, 'Prescription history retrieved successfully', 200);
  } catch (error) {
    console.error('[PrescriptionController History Error]', error.message);
    return errorResponse(res, `Failed to retrieve prescription history: ${error.message}`, 500);
  }
}

module.exports = {
  handlePrescriptionAnalysis,
  updatePrescription,
  getPrescriptionHistory
};
