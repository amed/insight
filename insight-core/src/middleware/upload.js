const multer = require('multer');

// Keeps the uploaded file in memory; Parse a small JSON transcript fow now
module.exports = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 5 * 1024 * 1024 }, // 5 MB
});
