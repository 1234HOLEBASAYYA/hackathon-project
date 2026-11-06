const mongoose = require('mongoose');

const PatientSchema = new mongoose.Schema({
  patientId: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    index: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  age: {
    type: Number,
    required: false
  },
  gender: {
    type: String,
    enum: ['Male', 'Female', 'Other', 'Not specified'],
    default: 'Not specified'
  },
  contact: {
    type: String,
    default: ''
  },
  bloodGroup: {
    type: String,
    default: ''
  },
  allergies: {
    type: [String],
    default: []
  },
  chronicConditions: {
    type: [String],
    default: []
  }
}, {
  timestamps: true,
  collection: 'patients'
});

module.exports = mongoose.model('Patient', PatientSchema);

