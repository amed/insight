const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// the schema registry. every json file in insight-core/schemas/ is loaded once at startup,
// validated, and hashed. a broken schema stops the process, it is never served half-right.
// schemas are identified as <name>-v<version>, matching their file name.

const DIR = path.join(__dirname, '../../schemas');

// the base schema: the upload default and the fixed reference for evaluation
const DEFAULT_ID = 'support-v1';

// 'unknown' is reserved as the implicit abstention value on every field
const RESERVED = 'unknown';

function fail(file, reason) {
  throw new Error(`schema ${file}: ${reason}`);
}

function validate(schema, file) {
  if (typeof schema.name !== 'string' || !/^[a-z][a-z0-9_-]*$/.test(schema.name)) {
    fail(file, 'name must be a lowercase identifier');
  }
  if (!Number.isInteger(schema.version) || schema.version < 1) {
    fail(file, 'version must be a positive integer');
  }
  if (!Array.isArray(schema.fields) || schema.fields.length === 0) {
    fail(file, 'fields must be a non-empty array');
  }

  const names = new Set();
  for (const field of schema.fields) {
    if (typeof field.name !== 'string' || !field.name.trim()) {
      fail(file, 'every field needs a name');
    }
    if (names.has(field.name)) {
      fail(file, `duplicate field name "${field.name}"`);
    }
    names.add(field.name);

    if (typeof field.question !== 'string' || !field.question.trim()) {
      fail(file, `field "${field.name}" needs a question`);
    }
    if (!Array.isArray(field.values) || field.values.length === 0) {
      fail(file, `field "${field.name}" needs a non-empty values list`);
    }

    const seen = new Set();
    for (const value of field.values) {
      if (typeof value !== 'string' || !value.trim() || value !== value.trim().toLowerCase()) {
        fail(file, `field "${field.name}" values must be non-empty lowercase strings`);
      }
      if (value === RESERVED) {
        fail(file, `field "${field.name}" lists "${RESERVED}", which is reserved`);
      }
      if (seen.has(value)) {
        fail(file, `field "${field.name}" has duplicate value "${value}"`);
      }
      seen.add(value);
    }
  }
}

function load() {
  const byId = new Map();
  for (const file of fs.readdirSync(DIR).filter((f) => f.endsWith('.json')).sort()) {
    const raw = fs.readFileSync(path.join(DIR, file));
    let schema;
    try {
      schema = JSON.parse(raw);
    } catch {
      fail(file, 'not valid json');
    }
    validate(schema, file);

    const id = `${schema.name}-v${schema.version}`;
    if (file !== `${id}.json`) {
      fail(file, `file name must match its content (expected ${id}.json)`);
    }
    const hash = crypto.createHash('sha256').update(raw).digest('hex').slice(0, 12);
    byId.set(id, { ...schema, id, hash });
  }

  if (!byId.has(DEFAULT_ID)) {
    throw new Error(`default schema ${DEFAULT_ID} is missing from ${DIR}`);
  }
  return byId;
}

const registry = load();

function get(id) {
  return registry.get(id) || null;
}

function list() {
  return [...registry.values()];
}

module.exports = { get, list, DEFAULT_ID };
