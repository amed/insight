const schemas = require('../services/schemas');
const summaryService = require('../services/summaryService');
const HttpError = require('../utils/httpError');

// Loaded schemas are listed so the upload ui can offer the choice.
function list(_req, res) {
  res.json(
    schemas.list().map(({ id, name, version, hash, fields }) => ({
      id,
      name,
      version,
      hash,
      default: id === schemas.DEFAULT_ID,
      fields,
    }))
  );
}

// Value counts for one schema, optionally filtered to one pipeline.
// Only records under the schema's current name, version, and content hash are counted.
async function summary(req, res) {
  const schema = schemas.get(req.params.name);
  if (!schema) throw new HttpError(404, 'schema not found');

  const pipeline = req.query.pipeline;
  if (pipeline && !['p1', 'p2', 'p3'].includes(pipeline)) { // TODO: validate and make dynamic
    throw new HttpError(400, 'pipeline must be p1, p2, or p3');
  }

  res.json(await summaryService.summarize(schema, pipeline || null));
}

module.exports = { list, summary };
