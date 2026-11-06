require('dotenv').config({ path: require('path').resolve(__dirname, '../.env') });
require('dotenv').config(); // Fallback to local .env

const app = require('./app');
const { connectDatabase } = require('./config/database');
const { PORT, HOST } = require('./config/ports');

async function startServer() {
  console.log('----------------------------------------------------');
  console.log('   MEDVISION-AI: Central Node.js & Express Gateway   ');
  console.log('----------------------------------------------------');

  await connectDatabase();

  app.listen(PORT, HOST, () => {
    console.log(`[Express Gateway] Server actively listening at http://${HOST}:${PORT}`);
    console.log(`[Express Gateway] Unified Medical Web UI at http://localhost:${PORT}`);
  });
}

startServer();

