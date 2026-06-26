const config = require('../config');

// Ranks lines against a query using the embeddings service.
// Returns [{ index, score }], best first.
async function search(query, lines, topK = config.topK) {
  const res = await fetch(`${config.services.embeddings}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, lines, top_k: topK }),
  });
  if (!res.ok) {
    throw new Error(`embeddings /search failed: ${res.status}`);
  }
  const data = await res.json();
  return data.matches;
}

module.exports = { search };
