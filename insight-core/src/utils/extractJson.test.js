const extractJson = require('./extractJson');

describe('extractJson', () => {
  test('parses a json object wrapped in prose or code fences', () => {
    const text = 'Sure, here it is.\n```json\n{"value": "positive", "citations": ["L0001"]}\n```';
    expect(extractJson(text)).toEqual({ value: 'positive', citations: ['L0001'] });
  });

  test('returns null when there is no parsable object', () => {
    expect(extractJson('no answer')).toBeNull();
    expect(extractJson('{"value": ')).toBeNull();
  });
});
