const config = require('../config');

// The audio file is sent to whisper. Per-channel split is requested only when asked.
async function transcribe(file, { split = false } = {}) {
  const form = new FormData();
  form.append('file', new Blob([file.buffer]), file.originalname || 'audio');
  if (split) {
    form.append('split', 'true');
  }

  const res = await fetch(`${config.services.whisper}/transcribe`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    throw new Error(`whisper /transcribe failed: ${res.status}`);
  }
  return res.json();
}

module.exports = { transcribe };
