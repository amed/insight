const interactionService = require('../services/interactionService');
const processingService = require('../services/processingService');
const intake = require('../services/intake');
const schemas = require('../services/schemas');
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

// The interactions are listed.
async function list(_req, res) {
  const interactions = await interactionService.listInteractions();
  res.json(interactions.map(serializeInteractionSummary));
}

// An uploaded transcript or audio file is accepted.
// The file is only classified here, then a pending interaction is created and the id returned at once.
// Transcription, diarization, and field extraction all run on the background path so the upload never blocks on a model.
async function create(req, res) {
  // The per-channel split (separate speakers) and the agent channel are read (audio options).
  const splitChannels = req.body.split_channels === 'true' || req.body.split_channels === '1';
  const agentChannel = Number.parseInt(req.body.agent_channel, 10);

  // The pipeline is p1 tf-idf baseline, p2 retrieval-grounded llm, or p3 direct llm (extraction pipeline).
  const pipeline = req.body.pipeline || 'p2';
  if (!['p1', 'p2', 'p3'].includes(pipeline)) {
    throw new HttpError(400, 'pipeline must be p1, p2, or p3');
  }

  // The schema the batch was selected under. The base schema when none is named.
  // p1 needs no guard here,
  // because the baseline artifact claims the schema it was trained for and processing fails the record on a mismatch.
  const schema = schemas.get(req.body.schema || schemas.DEFAULT_ID);
  if (!schema) {
    throw new HttpError(400, `unknown schema (see GET /schemas)`);
  }

  const prepared = intake.prepare(req.file); // Classify + validate
  const id = await interactionService.createPending({ // Pending row
    interactionId: prepared.interactionId,
    sourceFilename: req.file.originalname,
    pipeline,
    schema,
  });

  processingService.run(id, prepared, req.file, { // Background, not awaited
    splitChannels,
    agentChannel: Number.isNaN(agentChannel) ? 0 : agentChannel,
  });

  res.status(202).json({ id, status: 'pending' }); // Returns immediately - promise ignored
}

// The stored interaction is returned with its lines and record.
async function getOne(req, res) {
  const interaction = await interactionService.getInteraction(parseId(req.params.id));
  if (!interaction) {
    throw new HttpError(404, 'interaction not found');
  }
  res.json(serializeInteraction(interaction));
}

// The recorded steps for one interaction are returned, oldest first.
async function listSteps(req, res) {
  const steps = await interactionService.getSteps(parseId(req.params.id));
  res.json(steps.map(serializeStep));
}

module.exports = { list, create, getOne, listSteps };
