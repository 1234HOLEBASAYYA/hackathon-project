const mongoose = require('mongoose');

const AnalysisResultSchema = new mongoose.Schema({
  analysisId: {
    type: String,
    required: true,
    unique: true,
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
  modality: {
    type: String,
    required: true,
    enum: ['prescription', 'prescription_doc', 'xray', 'chest_xray', 'ct_scan'],
    index: true
  },
  reportTitle: {
    type: String,
    default: 'Clinical Imaging Analysis Report'
  },
  status: {
    type: String,
    default: 'completed'
  },
  modelInfo: {
    modelName: { type: String, default: '' },
    version: { type: String, default: '1.0.0' },
    device: { type: String, default: 'cpu' }
  },
  fileMetadata: {
    originalFilename: String,
    storedFilename: String,
    storedPath: String,
    fileSize: Number,
    mimeType: String
  },
  primaryFinding: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  findings: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  report: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  specimenUrl: {
    type: String,
    default: ''
  },
  reportPdfUrl: {
    type: String,
    default: ''
  },
  gradcam: {
    type: mongoose.Schema.Types.Mixed,
    default: {}
  },
  filename: {
    type: String,
    default: ''
  }
}, {
  timestamps: true,
  collection: 'analysisresults'
});

AnalysisResultSchema.pre('save', function(next) {
  if (!this.patient && this.patientId) {
    this.patient = this.patientId;
  }
  next();
});

module.exports = mongoose.model('AnalysisResult', AnalysisResultSchema);

