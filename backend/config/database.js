const mongoose = require('mongoose');

const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/medvision_ai';

async function connectDatabase() {
  try {
    await mongoose.connect(MONGODB_URI, {
      serverSelectionTimeoutMS: 5000,
      autoIndex: true
    });
    console.log(`[Database] Connected to MongoDB successfully at ${MONGODB_URI}`);
  } catch (error) {
    console.error(`[Database] MongoDB connection error: ${error.message}`);
  }
}

module.exports = {
  connectDatabase,
  mongoose
};

