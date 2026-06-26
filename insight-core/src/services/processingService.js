const { sequelize, InsightRecord, Line, RecordField, FieldCitation } = require('../models');
const interactionService = require('./interactionService');
const intake = require('./intake');
const retrievalClient = require('./retrievalClient');
const llmClient = require('./llmClient');
const trace = require('./trace');
const extractJson = require('../utils/extractJson');
const config = require('../config');
const FIELDS = require('./fields');

// a short error message is taken from an error or value
function message(err) {
  return String(err && err.message ? err.message : err);
}

// the whole pipeline for one interaction runs here, off the request path, so the upload
// responds at once. turns are obtained (transcribed and diarized for audio), stored as
// lines, then each field is extracted and grounded. every stage is traced for debugging.
async function run(interactionId, prepared, file, options) {
  try {
    const turns = await obtainTurns(interactionId, prepared, file, options);
    if (turns.length === 0) {
      await trace.record(interactionId, 'processing:empty', 'error', { reason: 'no usable lines' });
      await markFailed(interactionId);
      return;
    }

    await interactionService.saveLines(interactionId, turns);
    const lines = await Line.findAll({
      where: { interactionId },
      order: [['ordinal', 'ASC']],
    });

    const record = await InsightRecord.findOne({ where: { interactionId } });
    await trace.record(interactionId, 'processing:start', 'ok', {
      lines: lines.length,
      fields: FIELDS.map((field) => field.name),
    });

    for (const field of FIELDS) {
      await extractField(interactionId, record, field, lines);
    }

    await record.update({ status: 'complete' });
    await trace.record(interactionId, 'processing:complete', 'ok', null);
  } catch (err) {
    console.error(`processing failed for interaction ${interactionId}`, err);
    await markFailed(interactionId);
    await trace.record(interactionId, 'processing:failed', 'error', { message: message(err) });
  }
}

async function markFailed(interactionId) {
  await InsightRecord.update({ status: 'failed' }, { where: { interactionId } }).catch(() => {});
}

// turns are parsed already for a transcript; for audio they are transcribed and diarized now
async function obtainTurns(interactionId, prepared, file, options) {
  if (prepared.kind === 'transcript') {
    await trace.record(interactionId, 'ingest', 'ok', { kind: 'transcript', turns: prepared.turns.length });
    return prepared.turns;
  }
  const { turns, ingest } = await intake.ingestAudio(file, options);
  await trace.record(interactionId, 'ingest', 'ok', ingest);
  return turns;
}

// one field is retrieved, extracted, validated, and stored. each stage is traced,
// and a stage failure is recorded without stopping the other fields.
async function extractField(interactionId, record, field, lines) {
  let matches;
  try {
    matches = await retrievalClient.search(field.query, lines.map((l) => l.text), config.topK);
  } catch (err) {
    await trace.record(interactionId, `retrieve:${field.name}`, 'error', { message: message(err) });
    return;
  }

  const topLines = matches.map((m) => lines[m.index]);
  await trace.record(interactionId, `retrieve:${field.name}`, 'ok', {
    query: field.query,
    matched: topLines.map((l) => l.lineId),
    scores: matches.map((m) => Number(m.score.toFixed(3))),
  });

  let extracted;
  try {
    extracted = await askLlm(field, topLines);
  } catch (err) {
    await trace.record(interactionId, `extract:${field.name}`, 'error', { message: message(err) });
    return;
  }

  if (!extracted || !extracted.value) {
    await trace.record(interactionId, `extract:${field.name}`, 'skipped', {
      reason: 'no value returned',
    });
    return;
  }

  // grounding check: keep only citations that were in the retrieved set
  const allowed = new Map(topLines.map((l) => [l.lineId, l]));
  const citedLines = (extracted.citations || []).map((id) => allowed.get(id)).filter(Boolean);
  const dropped = (extracted.citations || []).filter((id) => !allowed.has(id));

  await sequelize.transaction(async (transaction) => {
    const saved = await RecordField.create(
      { recordId: record.id, name: field.name, value: extracted.value },
      { transaction }
    );
    await FieldCitation.bulkCreate(
      citedLines.map((l) => ({ fieldId: saved.id, lineId: l.id })),
      { transaction }
    );
  });

  await trace.record(interactionId, `extract:${field.name}`, 'ok', {
    value: extracted.value,
    citations: citedLines.map((l) => l.lineId),
    dropped_citations: dropped,
  });
}

async function askLlm(field, lines) {
  const numbered = lines
    .map((l) => `${l.lineId} (${l.speaker}): ${l.text}`)
    .join('\n');

  const content = await llmClient.complete(
    [
      {
        role: 'system',
        content:
          'You extract one field from a customer support conversation. ' +
          'Use only the provided lines. Reply with JSON: ' +
          '{"value": "<short answer>", "citations": ["<line id>", ...]}. ' +
          'citations are the line ids that support the value.',
      },
      {
        role: 'user',
        content: `Field: ${field.name}\nQuestion: ${field.query}\n\nLines:\n${numbered}`,
      },
    ],
    { json: true }
  );

  return extractJson(content);
}

module.exports = { run };
