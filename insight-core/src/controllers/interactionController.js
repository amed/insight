const interactionService = require('../services/interactionService');
const { parseTranscript } = require('../services/transcriptParser');
const { serializeInteraction } = require('../serializers/interaction');
const HttpError = require('../utils/httpError');

// Upload a JSON transcript, store it, return its id.
async function create(req, res) {
  const { interactionId, turns } = parseTranscript(req.file);

  const id = await interactionService.createInteraction({
    interactionId,
    turns,
    sourceFilename: req.file.originalname,
  });

  res.status(201).json({ id, status: 'pending' });
}

// Return the stored interaction with its lines and record.
async function getOne(req, res) {
  const id = Number.parseInt(req.params.id, 10);
  if (Number.isNaN(id)) {
    throw new HttpError(400, 'id must be a number');
  }

  const interaction = await interactionService.getInteraction(id);
  if (!interaction) {
    throw new HttpError(404, 'interaction not found');
  }

  res.json(serializeInteraction(interaction));
}

module.exports = { create, getOne };
