const { buildLines } = require('./lineBuilder');

describe('buildLines', () => {
  test('numbers the turns with stable padded ids in order', () => {
    const lines = buildLines([
      { speaker: 'agent', text: 'hi' },
      { speaker: 'customer', text: 'hello' },
    ]);
    expect(lines.map((line) => line.lineId)).toEqual(['L0001', 'L0002']);
    expect(lines[1]).toMatchObject({ ordinal: 2, speaker: 'customer', text: 'hello' });
  });

  test('keeps segment times as whole milliseconds and leaves them null otherwise', () => {
    const [timed, untimed] = buildLines([
      { speaker: 'agent', text: 'a', start: 0.5, end: 2.2504 },
      { speaker: 'customer', text: 'b' },
    ]);
    expect(timed).toMatchObject({ startMs: 500, endMs: 2250 });
    expect(untimed).toMatchObject({ startMs: null, endMs: null });
  });
});
