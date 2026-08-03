const schemas = require('../services/schemas');
const summaryService = require('../services/summaryService');
const HttpError = require('../utils/httpError');

// the loaded schemas are listed so the upload ui can offer the choice
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

// value counts for one schema version, optionally filtered to one pipeline.
// version is required: versions are separate partitions and are never merged.
async function summary(req, res) {
  const version = Number.parseInt(req.query.version, 10);
  if (Number.isNaN(version)) {
    throw new HttpError(400, 'version query parameter is required');
  }

  const schema = schemas.get(`${req.params.name}-v${version}`);
  if (!schema) {
    throw new HttpError(404, 'schema not found');
  }

  const pipeline = req.query.pipeline;
  if (pipeline && !['p1', 'p2', 'p3'].includes(pipeline)) {
    throw new HttpError(400, 'pipeline must be p1, p2, or p3');
  }

  res.json(await summaryService.summarize(schema, pipeline || null));
}

module.exports = { list, summary };
