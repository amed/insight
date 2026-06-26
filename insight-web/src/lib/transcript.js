// pasted text is turned into a transcript file the backend accepts.
// lines shaped "speaker: text" are split into turns; other lines default to the customer.
export function buildTranscriptFile(text) {
  const turns = text
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^(\w+)\s*:\s*(.+)$/);
      if (match) {
        return { speaker: match[1].toLowerCase(), text: match[2] };
      }
      return { speaker: 'customer', text: line };
    });

  const payload = { interaction_id: `web-${Date.now()}`, turns };
  return new File([JSON.stringify(payload)], 'transcript.json', {
    type: 'application/json',
  });
}
