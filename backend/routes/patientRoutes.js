const express = require('express');
const router = express.Router();
const patientController = require('../controllers/patientController');

router.post('/', patientController.createPatient);
router.get('/', patientController.getAllPatients);
router.get('/:patientId', patientController.getPatientById);
router.get('/:patientId/timeline', patientController.getPatientTimeline);

module.exports = router;

