const config = require('../config');

// The conversation lines are sent to the tf-idf baseline service.
// All field values and the trained model version are returned in one call.
async function extract(lines) {
  const res = await fetch(`${config.services.baseline}/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      lines: lines.map((l) => ({ speaker: l.speaker, text: l.text })),
    }),
  });

  if (!res.ok) throw new Error(`baseline extract failed: ${res.status}`);

  return res.json();
}

module.exports = { extract };
