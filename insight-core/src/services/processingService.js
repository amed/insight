const { sequelize, InsightRecord, Line, RecordField, FieldCitation } = require('../models');
const interactionService = require('./interactionService');
const intake = require('./intake');
const retrievalClient = require('./retrievalClient');
const baselineClient = require('./baselineClient');
const llmClient = require('./llmClient');
const trace = require('./trace');
const extractJson = require('../utils/extractJson');
const config = require('../config');
const FIELDS = require('./fields');

// bumped when the extraction prompt text changes, part of the stored config version
const PROMPT_VERSION = 'prompt1';

// a short error message is taken from an error or value
function message(err) {
  return String(err && err.message ? err.message : err);
}

// the effective llm configuration for a record, stored so results stay comparable:
// p2 sees the retrieved top-k lines, p3 sees the full conversation
function llmConfigVersion(pipeline) {
  const scope = pipeline === 'p3' ? 'full' : `top${config.topK}`;
  return `${config.llmModel}|${scope}|${PROMPT_VERSION}`;
}

// the whole pipeline for one interaction runs here, off the request path, so the upload
// responds at once. turns are obtained (transcribed and diarized for audio), stored as
// lines, then the record's pipeline extracts the fields. every stage is traced.
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
      pipeline: record.pipeline,
      lines: lines.length,
      fields: FIELDS.map((field) => field.name),
    });

    if (record.pipeline === 'p1') {
      await extractBaseline(interactionId, record, lines);
    } else {
      await record.update({ configVersion: llmConfigVersion(record.pipeline) });
      for (const field of FIELDS) {
        await extractField(interactionId, record, field, lines, record.pipeline);
      }
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

// p1: all six fields come from one call to the tf-idf baseline service. a failure marks
// the record failed, there is nothing partial to salvage from a single call.
async function extractBaseline(interactionId, record, lines) {
  let data;
  try {
    data = await baselineClient.extract(lines);
  } catch (err) {
    await trace.record(interactionId, 'extract:baseline', 'error', { message: message(err) });
    throw err;
  }

  // the trained model version (a hash of the training data) is the p1 config version
  await record.update({ configVersion: data.model_version });
  await RecordField.bulkCreate(
    data.fields.map((f) => ({ recordId: record.id, name: f.name, value: f.value }))
  );

  await trace.record(interactionId, 'extract:baseline', 'ok', {
    values: Object.fromEntries(data.fields.map((f) => [f.name, f.value])),
    model_version: data.model_version,
  });
}

// p2 and p3: one field is selected, extracted, grounded, and stored. p2 retrieves the
// top-k lines first; p3 passes the full conversation, so retrieval is the only variable
// that differs between the two. a stage failure is traced without stopping other fields.
async function extractField(interactionId, record, field, lines, pipeline) {
  let topLines;
  if (pipeline === 'p3') {
    topLines = lines;
  } else {
    let matches;
    try {
      matches = await retrievalClient.search(field.query, lines.map((l) => l.text), config.topK);
    } catch (err) {
      await trace.record(interactionId, `retrieve:${field.name}`, 'error', { message: message(err) });
      return;
    }

    const ranked = matches.map((m) => lines[m.index]);
    await trace.record(interactionId, `retrieve:${field.name}`, 'ok', {
      query: field.query,
      matched: ranked.map((l) => l.lineId),
      scores: matches.map((m) => Number(m.score.toFixed(3))),
    });

    // the prompt shows the retrieved lines in conversation order, not score order,
    // so p2 and p3 prompts differ only in which lines are included
    topLines = [...ranked].sort((a, b) => a.ordinal - b.ordinal);
  }

  let extracted;
  let promptChars;
  try {
    ({ extracted, promptChars } = await askLlm(field, topLines));
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

  // grounding check: keep only citations that were in the lines given to the model.
  // the model may ignore the schema and return a non-array, treated as no citations.
  const cited = Array.isArray(extracted.citations) ? extracted.citations : [];
  const allowed = new Map(topLines.map((l) => [l.lineId, l]));
  const citedLines = cited.map((id) => allowed.get(id)).filter(Boolean);
  const dropped = cited.filter((id) => !allowed.has(id));

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

  // lines_given and prompt_chars make silent context truncation visible for p3
  await trace.record(interactionId, `extract:${field.name}`, 'ok', {
    value: extracted.value,
    citations: citedLines.map((l) => l.lineId),
    dropped_citations: dropped,
    lines_given: topLines.length,
    prompt_chars: promptChars,
  });
}

async function askLlm(field, lines) {
  const numbered = lines
    .map((l) => `${l.lineId} (${l.speaker}): ${l.text}`)
    .join('\n');

  const messages = [
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
  ];
  const promptChars = messages[0].content.length + messages[1].content.length;

  const content = await llmClient.complete(messages, { json: true });
  return { extracted: extractJson(content), promptChars };
}

module.exports = { run };
