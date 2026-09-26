const { parseTranscript } = require('./transcriptParser');

// An upload as multer hands it over, a buffer holding the file.
function file(data) {
  return { buffer: Buffer.from(typeof data === 'string' ? data : JSON.stringify(data)) };
}

// The thrown error, or null when nothing was thrown.
function thrown(fn) {
  try {
    fn();
  } catch (err) {
    return err;
  }
  return null;
}

describe('parseTranscript', () => {
  test('returns the trimmed id and the turns of a valid transcript', () => {
    const parsed = parseTranscript(
      file({ interaction_id: ' demo ', turns: [{ speaker: 'agent', text: 'hi', start: 0.5 }] })
    );
    expect(parsed.interactionId).toBe('demo');
    expect(parsed.turns).toHaveLength(1);
  });

  test.each([
    ['no file', undefined, 'no file uploaded'],
    ['broken json', file('{'), 'not valid JSON'],
    ['a missing id', file({ turns: [{ speaker: 'a', text: 'b' }] }), 'interaction_id'],
    ['empty turns', file({ interaction_id: 'x', turns: [] }), 'turns'],
    ['a turn without text', file({ interaction_id: 'x', turns: [{ speaker: 'a' }] }), 'turn 0'],
    ['a non-numeric time', file({ interaction_id: 'x', turns: [{ speaker: 'a', text: 'b', start: 'soon' }] }), '"start"'],
  ])('rejects %s with a 400', (_name, input, message) => {
    const err = thrown(() => parseTranscript(input));
    expect(err.status).toBe(400);
    expect(err.message).toContain(message);
  });
});
