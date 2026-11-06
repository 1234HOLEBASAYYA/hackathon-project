const express = require('express');
const router = express.Router();
const { prescriptionUpload } = require('../middleware/upload');
const prescriptionController = require('../controllers/prescriptionController');

router.post('/analyze', prescriptionUpload.single('file'), prescriptionController.handlePrescriptionAnalysis);
router.put('/:prescriptionId', prescriptionController.updatePrescription);
router.get('/history/:patientId', prescriptionController.getPrescriptionHistory);

module.exports = router;

