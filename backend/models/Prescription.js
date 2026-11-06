const mongoose = require('mongoose');

const MedicationSchema = new mongoose.Schema({
  medicineName: { type: String, default: '' },
  name: { type: String, default: '' },
  strength: { type: String, default: '' },
  dosage: { type: String, default: '' },
  route: { type: String, default: 'Oral' },
  frequency: { type: String, default: '' },
  duration: { type: String, default: '' },
  foodInstructions: { type: String, default: '' },
  specialInstructions: { type: String, default: '' },
  confidence: { type: Number, default: 0 }
}, { _id: false });

const PrescriptionSchema = new mongoose.Schema({
  prescriptionId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  analysisId: {
    type: String,
    required: true,
    index: true
  },
  patientId: {
    type: String,
    required: true,
    index: true
  },
  patient: {
    type: String,
    index: true
  },
  patientName: {
    type: String,
    default: 'Patient'
  },
  doctor: {
    name: { type: String, default: '' },
    qualification: { type: String, default: '' },
    specialization: { type: String, default: '' },
    clinicOrHospital: { type: String, default: '' },
    registrationNumber: { type: String, default: '' },
    contactNumber: { type: String, default: '' }
  },
  clinicHeader: {
    type: String,
    default: ''
  },
  diagnosis: {
    type: String,
    default: ''
  },
  advice: {
    type: String,
    default: ''
  },
  followUp: {
    type: String,
    default: ''
  },
  medications: [MedicationSchema],
  extractedItems: [mongoose.Schema.Types.Mixed],
  rawOcrText: {
    type: String,
    default: ''
  },
  clinicalWarnings: [String],
  doctorGuidance: [String],
  quality: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  filename: {
    type: String,
    default: ''
  },
  status: {
    type: String,
    default: 'completed'
  }
}, {
  timestamps: true,
  collection: 'prescriptions'
});

PrescriptionSchema.pre('save', function(next) {
  if (!this.patient && this.patientId) {
    this.patient = this.patientId;
  }
  next();
});

module.exports = mongoose.model('Prescription', PrescriptionSchema);

