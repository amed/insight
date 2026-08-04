const {
  fail,
  validate,
  load,
  DEFAULT_ID,
} = require('./schemaHelper');

const validSchema = {
  name: 'test',
  version: 1,
  fields: [
    {
      name: 'status',
      question: 'what is the status?',
      values: ['open', 'closed'],
    },
  ],
};

describe('fail', () => {
  test('throws a schema error with the file and reason', () => {
    expect(() => fail('test.json', 'invalid schema')).toThrow(
      'schema test.json: invalid schema',
    );
  });
});

describe('validate', () => {
  test('accepts a valid schema', () => {
    expect(() => validate(validSchema, 'test.json')).not.toThrow();
  });

  test('rejects an invalid schema', () => {
    expect(() => validate({ ...validSchema, name: 'Invalid Name' }, 'test.json')).toThrow(
      'schema test.json: name must be a lowercase identifier',
    );
  });
});

describe('load', () => {
  test('loads the schema registry with generated state', () => {
    const registry = load();
    const defaultSchema = registry.get(DEFAULT_ID);

    expect(registry).toBeInstanceOf(Map);
    expect(defaultSchema).toEqual(
      expect.objectContaining({
        id: DEFAULT_ID,
        name: DEFAULT_ID,
        version: expect.any(Number),
        hash: expect.stringMatching(/^[a-f0-9]{14}$/),
        fields: expect.any(Array),
      }),
    );
    expect(defaultSchema.fields.length).toBeGreaterThan(0);
  });
});
