// the first json object embedded in the text is parsed, or null is returned.
// the model sometimes wraps json in prose or code fences.
function extractJson(text) {
  try {
    const match = text.match(/\{[\s\S]*\}/);
    return match ? JSON.parse(match[0]) : null;
  } catch {
    return null;
  }
}

module.exports = extractJson;
