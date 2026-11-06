const express = require('express');
const router = express.Router();
const reportController = require('../controllers/reportController');

router.get('/stats', reportController.getDashboardStats);
router.get('/', reportController.getRecentReports);
router.get('/:analysisId', reportController.getReportById);

module.exports = router;

