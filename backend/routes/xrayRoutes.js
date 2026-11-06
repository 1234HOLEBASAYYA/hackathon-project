const express = require('express');
const router = express.Router();
const { xrayUpload } = require('../middleware/upload');
const xrayController = require('../controllers/xrayController');

router.post('/analyze', xrayUpload.single('file'), xrayController.handleXRayAnalysis);

module.exports = router;

