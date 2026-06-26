const multer = require('multer');

// Keeps the uploaded file in memory; Parse a small JSON transcript fow now
module.exports = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }, // 25 MB
});
