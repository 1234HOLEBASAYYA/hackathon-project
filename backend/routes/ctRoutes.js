const express = require('express');
const router = express.Router();
const { ctUpload } = require('../middleware/upload');
const ctController = require('../controllers/ctController');

router.post('/analyze', ctUpload.single('file'), ctController.handleCTAnalysis);

module.exports = router;

