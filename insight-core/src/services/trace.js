const { Step } = require('../models');

// A processing step and its output are recorded for debugging.
// Failures here are swallowed so tracing never breaks the pipeline.
async function record(interactionId, name, status, detail) {
  try {
    await Step.create({ interactionId, name, status, detail: detail || null });
  } catch (err) {
    console.error(`failed to record step "${name}" for interaction ${interactionId}`, err);
  }
}

module.exports = { record };
