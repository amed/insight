const HttpError = require('../utils/httpError');

// Parse and validate uploaded JSON transcript file.
// The expected shape is { "interaction_id": string, "turns": [{ "speaker": string, "text": string }] }.
// A turn may also carry numeric "start" and "end" seconds, which are kept as the line's time.
// TODO: find better strategy for validation
function parseTranscript(file) {
  if (!file) {
    throw new HttpError(400, 'no file uploaded (form field name must be "file")');
  }

  let data;
  try {
    data = JSON.parse(file.buffer.toString('utf-8'));
  } catch {
    throw new HttpError(400, 'uploaded file is not valid JSON');
  }

  if (typeof data.interaction_id !== 'string' || !data.interaction_id.trim()) {
    throw new HttpError(400, 'interaction_id (non-empty string) is required');
  }

  if (!Array.isArray(data.turns) || data.turns.length === 0) {
    throw new HttpError(400, 'turns (non-empty array) is required');
  }

  data.turns.forEach((turn, i) => {
    if (typeof turn.speaker !== 'string' || typeof turn.text !== 'string') {
      throw new HttpError(400, `turn ${i} must have string "speaker" and "text"`);
    }
    for (const key of ['start', 'end']) {
      if (turn[key] !== undefined && !Number.isFinite(turn[key])) {
        throw new HttpError(400, `turn ${i} "${key}" must be a number of seconds`);
      }
    }
  });

  return { interactionId: data.interaction_id.trim(), turns: data.turns };
}

module.exports = { parseTranscript };
