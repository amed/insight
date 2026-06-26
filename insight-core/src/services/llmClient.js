const config = require('../config');

// Calls the OpenAI-compatible chat endpoint (ollama by default).
// Returns the assistant message content as a string.
async function complete(messages, { json = false } = {}) {
  const body = { model: config.llmModel, messages, temperature: 0 };
  if (json) {
    body.response_format = { type: 'json_object' };
  }

  const res = await fetch(`${config.services.llmBaseUrl}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(`llm completion failed: ${res.status}`);
  }
  const data = await res.json();
  return data.choices[0].message.content;
}

module.exports = { complete };
