const { InsightRecord } = require('../models');

// Processing seam.
//
// This is where pipeline plugs for each BI field
// SBERT (embeddings service) retrieves the supporting lines, the LLM
// extracts the field value grounded in those lines, and the cited line
// ids are persisted as record_fields + field_citations.
//
// For now extraction is stubbed: create the record in a "pending" TODO: find better naming
// state so the result entity exists and the API contract is stable.
async function process(interaction, { transaction } = {}) {
  return InsightRecord.create(
    { interactionId: interaction.id, status: 'pending' },
    { transaction }
  );
}

module.exports = { process };
