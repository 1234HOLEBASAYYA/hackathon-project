const Patient = require('../models/Patient');
const AnalysisResult = require('../models/AnalysisResult');
const Prescription = require('../models/Prescription');
const { successResponse, errorResponse } = require('../utils/responseFormatter');

async function createPatient(req, res, next) {
  try {
    const { patientId, name, age, gender, contact, allergies, chronicConditions, bloodGroup } = req.body;

    if (!patientId || !name) {
      return errorResponse(res, 'patientId and name are required', 400);
    }

    const existing = await Patient.findOne({ patientId });
    if (existing) {
      existing.name = name || existing.name;
      existing.age = age !== undefined ? age : existing.age;
      existing.gender = gender || existing.gender;
      existing.contact = contact || existing.contact;
      existing.bloodGroup = bloodGroup || existing.bloodGroup;
      if (allergies) existing.allergies = Array.isArray(allergies) ? allergies : [allergies];
      if (chronicConditions) existing.chronicConditions = Array.isArray(chronicConditions) ? chronicConditions : [chronicConditions];
      await existing.save();
      return successResponse(res, existing, 'Patient profile updated successfully', 200);
    }

    const patient = new Patient({
      patientId,
      name,
      age: age ? Number(age) : undefined,
      gender: gender || 'Not specified',
      contact: contact || '',
      bloodGroup: bloodGroup || '',
      allergies: Array.isArray(allergies) ? allergies : (allergies ? [allergies] : []),
      chronicConditions: Array.isArray(chronicConditions) ? chronicConditions : (chronicConditions ? [chronicConditions] : [])
    });

    await patient.save();
    return successResponse(res, patient, 'Patient registered successfully', 201);
  } catch (error) {
    next(error);
  }
}

async function getAllPatients(req, res, next) {
  try {
    const { search } = req.query;
    let filter = {};
    if (search && search.trim()) {
      const regex = new RegExp(search.trim(), 'i');
      filter = {
        $or: [
          { patientId: regex },
          { name: regex },
          { contact: regex }
        ]
      };
    }
    const patients = await Patient.find(filter).sort({ updatedAt: -1 }).limit(100);
    return successResponse(res, patients, 'Patients retrieved successfully');
  } catch (error) {
    next(error);
  }
}

async function getPatientById(req, res, next) {
  try {
    const { patientId } = req.params;
    const patient = await Patient.findOne({ patientId });
    if (!patient) {
      return errorResponse(res, `Patient with ID ${patientId} not found`, 404);
    }
    return successResponse(res, patient, 'Patient found');
  } catch (error) {
    next(error);
  }
}

async function getPatientTimeline(req, res, next) {
  try {
    const { patientId } = req.params;

    // Search patient demographics and historical records across all modalities
    const [patient, analyses, prescriptions] = await Promise.all([
      Patient.findOne({ patientId }),
      AnalysisResult.find({
        $or: [{ patientId }, { patient: patientId }]
      }).sort({ createdAt: -1 }),
      Prescription.find({
        $or: [{ patientId }, { patient: patientId }]
      }).sort({ createdAt: -1 })
    ]);

    return successResponse(res, {
      patientId,
      patient: patient || { patientId, name: 'Patient ' + patientId },
      totalAnalyses: analyses.length,
      totalPrescriptions: prescriptions.length,
      analyses,
      prescriptions
    }, 'Patient complete medical history retrieved');
  } catch (error) {
    next(error);
  }
}

module.exports = {
  createPatient,
  getAllPatients,
  getPatientById,
  getPatientTimeline
};

