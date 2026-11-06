module.exports = {
  PORT: parseInt(process.env.PORT, 10) || 3000,
  HOST: process.env.HOST || '127.0.0.1',
  SERVICES: {
    PRESCRIPTION: {
      NAME: 'Prescription AI',
      URL: process.env.PRESCRIPTION_SERVICE_URL || 'http://127.0.0.1:8001',
      PORT: 8001
    },
    XRAY: {
      NAME: 'Multi-Region X-Ray AI',
      URL: process.env.XRAY_SERVICE_URL || 'http://127.0.0.1:8002',
      PORT: 8002
    },
    CT: {
      NAME: 'CT-Scan Clinical AI',
      URL: process.env.CT_SERVICE_URL || 'http://127.0.0.1:8003',
      PORT: 8003
    }
  }
};

