const { sequelize, InsightRecord, RecordField } = require('../models');

// Value counts for completed records under exactly one schema name, version, and content hash.
// Schemas are never aggregated across any of the three.
// unknown and missing are separate buckets.
// unknown is a grounded abstention,
// missing means the field produced nothing (a stage failure), which is a different fact.
async function summarize(schema, pipeline) {
  const where = {
    status: 'complete',
    schemaName: schema.name,
    schemaVersion: schema.version,
    schemaHash: schema.hash,
    ...(pipeline ? { pipeline } : {}),
  };

  const total = await InsightRecord.count({ where });

  const rows = await RecordField.findAll({
    attributes: ['name', 'value', [sequelize.fn('COUNT', sequelize.col('RecordField.id')), 'count']],
    include: [{ model: InsightRecord, attributes: [], where }],
    group: ['RecordField.name', 'RecordField.value'],
    raw: true,
  });

  const counts = new Map(rows.map((row) => [`${row.name}\u0000${row.value}`, Number(row.count)]));

  // Every schema-defined value is emitted zero-filled and in schema order,
  // so chart categories are stable regardless of what the data happens to contain.
  const fields = schema.fields.map((field) => {
    const values = field.values.map((value) => ({
      value,
      count: counts.get(`${field.name}\u0000${value}`) || 0,
    }));
    const unknown = counts.get(`${field.name}\u0000unknown`) || 0;
    const counted = values.reduce((sum, v) => sum + v.count, 0) + unknown;
    return { name: field.name, values, unknown, missing: total - counted };
  });

  return { schema: schema.id, hash: schema.hash, pipeline: pipeline || null, total, fields };
}

module.exports = { summarize };
