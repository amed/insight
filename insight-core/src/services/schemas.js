const { load, DEFAULT_ID } = require('./schemaHelper');

// Schema Registry
// Every json file in insight-core/schemas/ is loaded once at startup, validated, and hashed.
// A broken schema stops the process, it is never served half-right.
// Schema is identified by its name.
const registry = load();

function get(id) {
  return registry.get(id) || null;
}

function list() {
  return [...registry.values()];
}

module.exports = { get, list, DEFAULT_ID };
