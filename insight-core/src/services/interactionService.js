const { sequelize, Interaction, Line, InsightRecord } = require('../models');
const { buildLines } = require('./lineBuilder');
const processingService = require('./processingService');

// Stores a transcript as an interaction + its lines, then runs processing.
// Everything happens in one transaction so a failure leaves nothing behind.
// TODO: test
async function createInteraction({ interactionId, turns, sourceFilename }) {
  return sequelize.transaction(async (transaction) => {
    const interaction = await Interaction.create(
      { interactionId, sourceFilename },
      { transaction }
    );

    const lines = buildLines(turns).map((line) => ({
      ...line,
      interactionId: interaction.id,
    }));
    await Line.bulkCreate(lines, { transaction });

    await processingService.process(interaction, { transaction });

    return interaction.id;
  });
}

// Loads an interaction with its lines (ordered) and its insight record.
async function getInteraction(id) {
  return Interaction.findByPk(id, {
    include: [
      { model: Line, as: 'lines' },
      { model: InsightRecord, as: 'record' },
    ],
    order: [[{ model: Line, as: 'lines' }, 'ordinal', 'ASC']],
  });
}

module.exports = { createInteraction, getInteraction };
