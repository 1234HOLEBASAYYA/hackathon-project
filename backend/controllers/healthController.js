const mongoose = require('mongoose');
const { SERVICES, PORT } = require('../config/ports');
const prescriptionService = require('../services/prescriptionService');
const xrayService = require('../services/xrayService');
const ctService = require('../services/ctService');

async function getSystemHealth(req, res) {
  const mongoStatus = mongoose.connection.readyState === 1 ? 'connected' : 'disconnected';

  const [rxHealth, xrayHealth, ctHealth] = await Promise.all([
    prescriptionService.checkHealth(),
    xrayService.checkHealth(),
    ctService.checkHealth()
  ]);

  const allHealthy = (mongoStatus === 'connected') &&
                     (rxHealth.status === 'healthy') &&
                     (xrayHealth.status === 'healthy') &&
                     (ctHealth.status === 'healthy');

  res.status(200).json({
    status: allHealthy ? 'healthy' : 'degraded',
    platform: 'MEDVISION-AI Unified Diagnostic Platform',
    version: '1.0.0',
    gateway: {
      port: PORT,
      status: 'active'
    },
    database: {
      type: 'MongoDB',
      host: '127.0.0.1:27017',
      name: 'medvision_ai',
      status: mongoStatus
    },
    services: {
      prescriptionAi: {
        name: SERVICES.PRESCRIPTION.NAME,
        url: SERVICES.PRESCRIPTION.URL,
        ...rxHealth
      },
      xrayAi: {
        name: SERVICES.XRAY.NAME,
        url: SERVICES.XRAY.URL,
        ...xrayHealth
      },
      ctAi: {
        name: SERVICES.CT.NAME,
        url: SERVICES.CT.URL,
        ...ctHealth
      }
    },
    timestamp: new Date().toISOString()
  });
}

module.exports = {
  getSystemHealth
};

