const schemas = require('./schemas');

describe('get', () => {
  test('returns a generated schema by ID', () => {
    const schema = schemas.get('v1');

    expect(schema.id).toBe('v1');
    expect(schema.name).toBe('v1');
  });

  test('returns null when the schema does not exist', () => {
    expect(schemas.get('does-not-exist')).toBeNull();
  });
});

describe('list', () => {
  test('returns every generated schema', () => {
    const availableSchemas = schemas.list();

    expect(availableSchemas.length).toBeGreaterThan(0);
    expect(availableSchemas).toContain(schemas.get(schemas.DEFAULT_ID));
  });

  test('returns schemas with unique IDs', () => {
    const ids = schemas.list().map((schema) => schema.id);

    expect(new Set(ids).size).toBe(ids.length);
  });
});
