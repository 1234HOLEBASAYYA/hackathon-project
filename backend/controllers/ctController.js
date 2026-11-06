const path = require('path');
const fs = require('fs');
const AnalysisResult = require('../models/AnalysisResult');
const Patient = require('../models/Patient');
const { analyzeCTScan } = require('../services/ctService');
const { SERVICES } = require('../config/ports');
const { successResponse, errorResponse } = require('../utils/responseFormatter');

async function handleCTAnalysis(req, res, next) {
  try {
    if (!req.file) {
      return errorResponse(res, 'No CT scan file provided. Please upload a PNG, JPG, or JPEG.', 400);
    }

    const patientId = req.body.patientId || req.body.patient_id || 'guest_patient';
    const patientName = req.body.patientName || req.body.patient_name || 'Demo Patient';

    // Auto-upsert patient record
    if (patientId !== 'guest_patient') {
      await Patient.findOneAndUpdate(
        { patientId },
        { $setOnInsert: { patientId, name: patientName } },
        { upsert: true, new: true }
      );
    }

    const filePath = req.file.path;
    const originalFilename = req.file.originalname;

    // Call CT AI Service (:8003)
    const aiResult = await analyzeCTScan(filePath, originalFilename, patientId);

    const reportData = aiResult.data || aiResult;
    const analysisId = reportData.analysis_id || `an_ct_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 6)}`;

    const observations = reportData.visual_observations || [];
    const findings = reportData.potential_findings || [];
    const reportTitle = reportData.report_title || 'AI-Assisted CT Image Analysis Report';

    const recordDoc = {
      analysisId,
      patientId,
      patient: patientId,
      patientName,
      modality: 'ct_scan',
      reportTitle,
      status: 'completed',
      modelInfo: {
        modelName: reportData.model_used || 'Gemini 3.5 Flash Multimodal Vision',
        version: '2.0.0',
        device: 'cloud-vision'
      },
      fileMetadata: {
        originalFilename,
        storedFilename: req.file.filename,
        storedPath: `/storage/ct-scans/${req.file.filename}`,
        fileSize: req.file.size,
        mimeType: req.file.mimetype
      },
      primaryFinding: findings[0] || (observations[0] ? { observation: observations[0].observation_summary } : {}),
      findings: {
        detectedModality: reportData.detected_modality || 'ct_scan',
        isCompatibleCtScan: reportData.is_compatible_ct_scan,
        visualObservations: observations,
        potentialFindings: findings,
        summary: reportData.summary || '',
        recommendations: reportData.recommendations_for_review || [],
        limitations: reportData.limitations || []
      },
      report: reportData,
      specimenUrl: `/storage/ct-scans/${req.file.filename}`,
      filename: originalFilename
    };

    await AnalysisResult.findOneAndUpdate(
      { analysisId },
      { $set: recordDoc },
      { upsert: true, new: true }
    );

    return successResponse(res, {
      analysisId,
      patientId,
      modality: 'ct_scan',
      reportTitle,
      detectedModality: reportData.detected_modality || 'ct_scan',
      visualObservations: observations,
      potentialFindings: findings,
      summary: reportData.summary || '',
      recommendations: reportData.recommendations_for_review || [],
      limitations: reportData.limitations || [],
      medicalDisclaimer: reportData.medical_disclaimer || '',
      specimenUrl: `/storage/ct-scans/${req.file.filename}`,
      savedToDatabase: true
    }, 'CT scan slice successfully analyzed and persisted to MongoDB', 200);

  } catch (error) {
    console.error('[CTController Error]', error.message);
    const detail = error.response && error.response.data ? error.response.data.detail || error.response.data.message : null;
    const errText = (detail || error.message || '').toLowerCase();
    
    // Check if error is due to uploading an incompatible or non-CT image
    if (errText.includes('incompatible') || errText.includes('prescription_doc') || errText.includes('unsupported') || errText.includes('not a proper') || errText.includes('non-radiological')) {
      return errorResponse(res, 'not a proper image to scan', 400, {
        isCompatibleCtScan: false,
        warning: 'The uploaded file is not a valid CT scan image. Please upload an authentic CT axial slice or scout view.',
        detail
      });
    }

    return errorResponse(res, `CT scan analysis failed: ${detail || error.message}`, error.response ? error.response.status : 500, detail);
  }
}

module.exports = {
  handleCTAnalysis
};
