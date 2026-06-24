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
          // fields + citations arrive when extraction is implemented
          fields: [],
        }
      : null,
  };
}

module.exports = { serializeInteraction };
