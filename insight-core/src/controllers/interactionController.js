const interactionService = require('../services/interactionService');
const processingService = require('../services/processingService');
const intake = require('../services/intake');
const {
  serializeInteraction,
  serializeInteractionSummary,
  serializeStep,
} = require('../serializers/interaction');
const HttpError = require('../utils/httpError');

function parseId(value) {
  const id = Number.parseInt(value, 10);
  if (Number.isNaN(id)) {
    throw new HttpError(400, 'id must be a number');
  }
  return id;
}

// the interactions are listed
async function list(_req, res) {
  const interactions = await interactionService.listInteractions();
  res.json(interactions.map(serializeInteractionSummary));
}

// an uploaded transcript or audio file is accepted. the file is only classified here, then
// a pending interaction is created and the id returned at once. transcription, diarization,
// and field extraction all run on the background path so the upload never blocks on a model.
async function create(req, res) {
  // audio options: per-channel split (separate speakers) and which channel is the agent
  const splitChannels = req.body.split_channels === 'true' || req.body.split_channels === '1';
  const agentChannel = Number.parseInt(req.body.agent_channel, 10);

  const prepared = intake.prepare(req.file);
  const id = await interactionService.createPending({
    interactionId: prepared.interactionId,
    sourceFilename: req.file.originalname,
  });

  processingService.run(id, prepared, req.file, {
    splitChannels,
    agentChannel: Number.isNaN(agentChannel) ? 0 : agentChannel,
  });

  res.status(202).json({ id, status: 'pending' });
}

// the stored interaction is returned with its lines and record
async function getOne(req, res) {
  const interaction = await interactionService.getInteraction(parseId(req.params.id));
  if (!interaction) {
    throw new HttpError(404, 'interaction not found');
  }
  res.json(serializeInteraction(interaction));
}

// the recorded steps for one interaction are returned, oldest first
async function listSteps(req, res) {
  const steps = await interactionService.getSteps(parseId(req.params.id));
  res.json(steps.map(serializeStep));
}

module.exports = { list, create, getOne, listSteps };
