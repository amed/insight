// Shapes an Interaction model (with its lines and record) into the API response.
function serializeInteraction(interaction) {
  return {
    id: interaction.id,
    interaction_id: interaction.interactionId,
    source_filename: interaction.sourceFilename,
    created_at: interaction.createdAt,
    lines: (interaction.lines || []).map((line) => ({
      line_id: line.lineId,
      speaker: line.speaker,
      text: line.text,
    })),
    record: interaction.record
      ? {
          status: interaction.record.status,
          pipeline: interaction.record.pipeline,
          config_version: interaction.record.configVersion,
          fields: (interaction.record.fields || []).map((field) => ({
            name: field.name,
            value: field.value,
            citations: (field.citations || []).map((c) => c.line && c.line.lineId),
          })),
        }
      : null,
  };
}

// a lightweight summary is shaped for the list view
function serializeInteractionSummary(interaction) {
  return {
    id: interaction.id,
    interaction_id: interaction.interactionId,
    source_filename: interaction.sourceFilename,
    created_at: interaction.createdAt,
    status: interaction.record ? interaction.record.status : null,
    pipeline: interaction.record ? interaction.record.pipeline : null,
  };
}

// a recorded step is shaped for the api
function serializeStep(step) {
  return {
    id: step.id,
    name: step.name,
    status: step.status,
    detail: step.detail,
    created_at: step.createdAt,
  };
}

module.exports = { serializeInteraction, serializeInteractionSummary, serializeStep };
