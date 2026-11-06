const path = require('path');
const express = require('express');
const cors = require('cors');
const morgan = require('morgan');

const patientRoutes = require('./routes/patientRoutes');
const prescriptionRoutes = require('./routes/prescriptionRoutes');
const xrayRoutes = require('./routes/xrayRoutes');
const ctRoutes = require('./routes/ctRoutes');
const reportRoutes = require('./routes/reportRoutes');
const healthRoutes = require('./routes/healthRoutes');
const errorHandler = require('./middleware/errorHandler');

const app = express();

// Basic Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));
app.use(morgan('dev'));

// Static File Mounts
const STORAGE_DIR = path.resolve(__dirname, '../storage');
const FRONTEND_DIR = path.resolve(__dirname, '../frontend');
const PAGES_DIR = path.join(FRONTEND_DIR, 'pages');

app.use('/storage', express.static(STORAGE_DIR));
app.use('/css', express.static(path.join(FRONTEND_DIR, 'css')));
app.use('/js', express.static(path.join(FRONTEND_DIR, 'js')));
app.use('/assets', express.static(path.join(FRONTEND_DIR, 'assets')));
app.use(express.static(PAGES_DIR));

// API Routes
app.use('/api/patients', patientRoutes);
app.use('/api/analysis/prescription', prescriptionRoutes);
app.use('/api/analysis/xray', xrayRoutes);
app.use('/api/analysis/ct', ctRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/health', healthRoutes);

// Fallback to index.html for SPA-style page routing
app.get('/', (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'index.html'));
});

// Alias for timeline
app.get(['/timeline', '/timeline.html'], (req, res) => {
  res.sendFile(path.join(PAGES_DIR, 'dashboard.html'));
});

// Central Error Handler
app.use(errorHandler);

module.exports = app;

