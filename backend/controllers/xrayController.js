const path = require('path');
const fs = require('fs');
const AnalysisResult = require('../models/AnalysisResult');
const Patient = require('../models/Patient');
const { analyzeXRay } = require('../services/xrayService');
const { SERVICES } = require('../config/ports');
const { successResponse, errorResponse } = require('../utils/responseFormatter');

async function handleXRayAnalysis(req, res, next) {
  try {
    if (!req.file) {
      return errorResponse(res, 'No X-Ray radiograph file provided. Please upload a PNG, JPG, or DICOM.', 400);
    }

    const patientId = req.body.patientId || req.body.patient_id || 'guest_patient';
    const patientName = req.body.patientName || req.body.patient_name || 'Demo Patient';

    // Auto-upsert patient record if needed
    if (patientId !== 'guest_patient') {
      await Patient.findOneAndUpdate(
        { patientId },
        { $setOnInsert: { patientId, name: patientName } },
        { upsert: true, new: true }
      );
    }

    const filePath = req.file.path;
    const originalFilename = req.file.originalname;

    // Call X-Ray AI Service (:8002)
    const aiResult = await analyzeXRay(filePath, originalFilename, patientId);

    // Reject non-X-Ray images (prescriptions, clinical documents, photographs, selfies, etc.)
    const regLower = (aiResult.anatomical_region || '').toLowerCase();
    if (aiResult.is_radiograph === false || aiResult.status === 'not_an_xray' || regLower === 'not a medical x-ray' || regLower.includes('not a medical')) {
      const rejectReason = aiResult.warning || aiResult.clinical_summary?.summary || 'The uploaded file is not a medical X-ray radiograph.';
      return errorResponse(res, 'not a proper image to scan', 400, {
        isRadiograph: false,
        detectedImageType: aiResult.detected_image_type || 'Non-radiological image',
        warning: rejectReason,
        patientGuidance: aiResult.clinical_summary?.patient_guidance || 'Please upload an authentic medical X-ray radiograph in PNG, JPG, or DICOM format.'
      });
    }

    const analysisId = aiResult.analysis_id || `an_xray_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 6)}`;

    // Resolve specimen and PDF URLs
    let specimenUrl = `/storage/xrays/${req.file.filename}`;
    if (aiResult.specimen_url) {
      specimenUrl = `${SERVICES.XRAY.URL}${aiResult.specimen_url}`;
    }

    let reportPdfUrl = '';
    if (aiResult.report_pdf_url) {
      reportPdfUrl = `${SERVICES.XRAY.URL}${aiResult.report_pdf_url}`;
    }

    const region = aiResult.anatomical_region || 'Unknown Region';
    const isAbnormal = Boolean(aiResult.is_abnormal);
    const affectedBone = aiResult.affected_bone || 'Unspecified';
    const boundingBox = aiResult.bounding_box_pixels || [];

    const summaryText = isAbnormal
      ? `Abnormality/Defect detected in ${region} (${affectedBone}) with ${(aiResult.confidence * 100 || 0).toFixed(1)}% confidence.`
      : `No significant abnormality detected in ${region}. Normal radiographic appearance.`;

    // Save to AnalysisResult collection
    const recordDoc = {
      analysisId,
      patientId,
      patient: patientId,
      patientName,
      modality: 'xray',
      reportTitle: `Multi-Region Radiograph Analysis (${region.toUpperCase()})`,
      status: 'completed',
      modelInfo: {
        modelName: 'Multi-Task ResNet-18 MSK Detector & TorchXRayVision DenseNet-121',
        version: '2.0.0',
        device: aiResult.device || 'cpu'
      },
      fileMetadata: {
        originalFilename,
        storedFilename: req.file.filename,
        storedPath: `/storage/xrays/${req.file.filename}`,
        fileSize: req.file.size,
        mimeType: req.file.mimetype
      },
      primaryFinding: {
        region,
        isAbnormal,
        affectedBone,
        confidence: aiResult.confidence,
        regionConfidence: aiResult.region_confidence,
        summary: summaryText
      },
      findings: {
        anatomicalRegion: region,
        regionConfidence: aiResult.region_confidence,
        isAbnormal,
        confidence: aiResult.confidence,
        affectedBone,
        boundingBoxPixels: boundingBox,
        findingsList: aiResult.findings || [],
        clinicalImpression: aiResult.clinical_impression || summaryText,
        observations: aiResult.observations || []
      },
      report: aiResult,
      specimenUrl,
      reportPdfUrl,
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
      modality: 'xray',
      anatomicalRegion: region,
      regionConfidence: aiResult.region_confidence,
      isAbnormal,
      confidence: aiResult.confidence,
      affectedBone,
      boundingBoxPixels: boundingBox,
      findings: aiResult.findings || [],
      clinicalImpression: aiResult.clinical_impression || summaryText,
      specimenUrl,
      reportPdfUrl,
      savedToDatabase: true
    }, 'X-Ray radiograph successfully analyzed and persisted to MongoDB', 200);

  } catch (error) {
    console.error('[XRayController Error]', error.message);
    return errorResponse(res, `X-Ray analysis failed: ${error.message}`, 500, error.response ? error.response.data : null);
  }
}

module.exports = {
  handleXRayAnalysis
};
