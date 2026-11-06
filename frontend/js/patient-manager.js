/**
 * MEDVISION-AI Patient Manager
 * Handles active patient identity across all diagnostic modalities
 */

const PatientManager = {
  ACTIVE_PATIENT_KEY: 'medvision_active_patient',

  DEFAULT_PATIENTS: [
    {
      patientId: 'P-1001',
      name: 'Robert Miller',
      age: 58,
      gender: 'Male',
      contact: '+1 555-0143',
      allergies: ['Penicillin'],
      chronicConditions: ['Type 2 Diabetes', 'Hypertension']
    },
    {
      patientId: 'P-1002',
      name: 'Elena Rostova',
      age: 42,
      gender: 'Female',
      contact: '+1 555-0821',
      allergies: ['Sulfa drugs'],
      chronicConditions: ['Mild Asthma']
    },
    {
      patientId: 'P-1003',
      name: 'Marcus Vance',
      age: 31,
      gender: 'Male',
      contact: '+1 555-0992',
      allergies: [],
      chronicConditions: ['Sports trauma history']
    }
  ],

  getActivePatient() {
    const raw = localStorage.getItem(this.ACTIVE_PATIENT_KEY);
    if (raw) {
      try { return JSON.parse(raw); } catch (e) { /* fallback */ }
    }
    const defaultPatient = this.DEFAULT_PATIENTS[0];
    this.setActivePatient(defaultPatient);
    return defaultPatient;
  },

  setActivePatient(patient) {
    localStorage.setItem(this.ACTIVE_PATIENT_KEY, JSON.stringify(patient));
    this.updateUI();
    window.dispatchEvent(new CustomEvent('patientChanged', { detail: patient }));
  },

  updateUI() {
    const patient = this.getActivePatient();
    document.querySelectorAll('.active-patient-name').forEach(el => el.textContent = patient.name);
    document.querySelectorAll('.active-patient-id').forEach(el => el.textContent = patient.patientId);
  },

  async init() {
    // Attempt to register default patients if not in database
    try {
      const active = this.getActivePatient();
      await window.API.createPatient(active);
    } catch (e) {
      console.warn('[PatientManager] Could not sync patient with DB on boot:', e);
    }
    this.updateUI();
  }
};

window.PatientManager = PatientManager;
document.addEventListener('DOMContentLoaded', () => PatientManager.init());

