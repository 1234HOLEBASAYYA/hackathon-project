const path = require('path');
const fs = require('fs');

const STORAGE_ROOT = path.resolve(__dirname, '../../storage');

function getRelativeUrl(category, filename) {
  return `/storage/${category}/${encodeURIComponent(filename)}`;
}

function getAbsolutePath(category, filename) {
  return path.join(STORAGE_ROOT, category, filename);
}

module.exports = {
  STORAGE_ROOT,
  getRelativeUrl,
  getAbsolutePath
};

