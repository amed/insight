const { sequelize, Interaction, Line, InsightRecord, RecordField, FieldCitation, Step } = require('../models');
const { buildLines } = require('./lineBuilder');

// an empty interaction and its pending record are created in one transaction and the id is
// returned, so the upload can respond immediately. the lines and fields are filled in later
// on the background path (see processingService), once transcription and extraction finish.
async function createPending({ interactionId, sourceFilename, pipeline = 'p2', schema }) {
  return sequelize.transaction(async (transaction) => {
    const interaction = await Interaction.create(
      { interactionId, sourceFilename },
      { transaction }
    );
    await InsightRecord.create(
      {
        interactionId: interaction.id,
        status: 'pending',
        pipeline,
        // the schema stamp makes the record self-describing and partitionable
        schemaName: schema.name,
        schemaVersion: schema.version,
        schemaHash: schema.hash,
      },
      { transaction }
    );
    return interaction.id;
  });
}

// the turns are stored as the interaction's lines, with stable ids and order
async function saveLines(interactionId, turns) {
  const lines = buildLines(turns).map((line) => ({ ...line, interactionId }));
  await Line.bulkCreate(lines);
}

// the interactions are listed newest first, each with its record status
async function listInteractions() {
  return Interaction.findAll({
    include: [
      {
        model: InsightRecord,
        as: 'record',
        attributes: ['status', 'pipeline', 'schemaName', 'schemaVersion'],
      },
    ],
    order: [['createdAt', 'DESC']],
  });
}

// the interaction is loaded with its ordered lines and its record (fields + citations)
async function getInteraction(id) {
  return Interaction.findByPk(id, {
    include: [
      { model: Line, as: 'lines' },
      {
        model: InsightRecord,
        as: 'record',
        include: [
          {
            model: RecordField,
            as: 'fields',
            include: [
              {
                model: FieldCitation,
                as: 'citations',
                include: [{ model: Line, as: 'line' }],
              },
            ],
          },
        ],
      },
    ],
    order: [[{ model: Line, as: 'lines' }, 'ordinal', 'ASC']],
  });
}

// the recorded steps for an interaction are loaded oldest first
async function getSteps(interactionId) {
  return Step.findAll({ where: { interactionId }, order: [['id', 'ASC']] });
}

module.exports = { createPending, saveLines, listInteractions, getInteraction, getSteps };
