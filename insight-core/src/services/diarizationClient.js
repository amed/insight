const config = require('../config');

// the audio file is sent to the diarization service; anonymous speaker turns are returned
async function diarize(file) {
  const form = new FormData();
  form.append('file', new Blob([file.buffer]), file.originalname || 'audio');

  const res = await fetch(`${config.services.diarization}/diarize`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    throw new Error(`diarization /diarize failed: ${res.status}`);
  }
  return res.json();
}

module.exports = { diarize };
