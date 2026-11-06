const path = require('path');
const fs = require('fs');
const multer = require('multer');

const ROOT_STORAGE = path.resolve(__dirname, '../../storage');

const storageDirs = {
  prescription: path.join(ROOT_STORAGE, 'prescriptions'),
  xray: path.join(ROOT_STORAGE, 'xrays'),
  ct: path.join(ROOT_STORAGE, 'ct-scans'),
  report: path.join(ROOT_STORAGE, 'reports')
};

// Ensure all storage directories exist
Object.values(storageDirs).forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

function createUploader(category) {
  const targetDir = storageDirs[category] || storageDirs.prescription;

  const storage = multer.diskStorage({
    destination: (req, file, cb) => {
      cb(null, targetDir);
    },
    filename: (req, file, cb) => {
      const ext = path.extname(file.originalname).toLowerCase();
      const cleanStem = path.basename(file.originalname, ext).replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30);
      const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
      cb(null, `${cleanStem}_${uniqueSuffix}${ext}`);
    }
  });

  const fileFilter = (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.pdf', '.dcm', '.dicom', '.webp'];
    const ext = path.extname(file.originalname).toLowerCase();
    if (allowed.includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error(`Invalid file type: ${ext}. Supported: ${allowed.join(', ')}`), false);
    }
  };

  return multer({
    storage,
    limits: {
      fileSize: 30 * 1024 * 1024 // 30 MB max
    },
    fileFilter
  });
}

module.exports = {
  prescriptionUpload: createUploader('prescription'),
  xrayUpload: createUploader('xray'),
  ctUpload: createUploader('ct'),
  storageDirs
};

