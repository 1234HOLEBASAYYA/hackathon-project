const AnalysisResult = require('../models/AnalysisResult');
const Prescription = require('../models/Prescription');
const Patient = require('../models/Patient');
const { successResponse, errorResponse } = require('../utils/responseFormatter');

async function getDashboardStats(req, res, next) {
  try {
    const [
      totalPatients,
      totalAnalyses,
      totalPrescriptions,
      totalXrays,
      totalCTs,
      recentRecords
    ] = await Promise.all([
      Patient.countDocuments(),
      AnalysisResult.countDocuments(),
      AnalysisResult.countDocuments({ modality: 'prescription' }),
      AnalysisResult.countDocuments({ modality: 'xray' }),
      AnalysisResult.countDocuments({ modality: 'ct_scan' }),
      AnalysisResult.find().sort({ createdAt: -1 }).limit(6)
    ]);

    return successResponse(res, {
      totalPatients,
      totalAnalyses,
      totalPrescriptions,
      totalXrays,
      totalCTs,
      recentRecords
    }, 'Dashboard statistics retrieved');
  } catch (error) {
    next(error);
  }
}

async function getReportById(req, res, next) {
  try {
    const { analysisId } = req.params;

    const [analysis, prescription] = await Promise.all([
      AnalysisResult.findOne({ analysisId }),
      Prescription.findOne({ $or: [{ analysisId }, { prescriptionId: analysisId }] })
    ]);

    if (!analysis && !prescription) {
      return errorResponse(res, `No clinical record found for ID: ${analysisId}`, 404);
    }

    return successResponse(res, {
      analysis,
      prescription
    }, 'Clinical record retrieved successfully');
  } catch (error) {
    next(error);
  }
}

async function getRecentReports(req, res, next) {
  try {
    const limit = parseInt(req.query.limit, 10) || 25;
    const reports = await AnalysisResult.find().sort({ createdAt: -1 }).limit(limit);
    return successResponse(res, reports, 'Recent reports retrieved successfully');
  } catch (error) {
    next(error);
  }
}

module.exports = {
  getDashboardStats,
  getReportById,
  getRecentReports
};

