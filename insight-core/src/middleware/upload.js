const multer = require('multer');

// Keeps the uploaded file in memory.
// Transcripts and audio files up to 25 MB are accepted.
module.exports = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }, // 25 MB
});
