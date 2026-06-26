const HttpError = require('../utils/httpError');
const whisperClient = require('./whisperClient');
const diarizationClient = require('./diarizationClient');
const { assignClusters, clustersToRoles } = require('./diarize');
const { parseTranscript } = require('./transcriptParser');
const config = require('../config');

const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm'];

// whether the uploaded file is audio, decided by mimetype or extension
function isAudio(file) {
  if (file.mimetype && file.mimetype.startsWith('audio/')) {
    return true;
  }
  const name = (file.originalname || '').toLowerCase();
  return AUDIO_EXTENSIONS.some((ext) => name.endsWith(ext));
}

// the upload is validated and classified without any heavy work, so the request can return
// at once. a transcript is parsed here, it is cheap and gives early validation errors. audio
// carries no turns yet; they are produced later by ingestAudio on the background path.
function prepare(file) {
  if (!file) {
    throw new HttpError(400, 'no file uploaded (form field name must be "file")');
  }
  if (isAudio(file)) {
    return { kind: 'audio', interactionId: `audio-${Date.now()}`, turns: null };
  }
  const parsed = parseTranscript(file);
  return { kind: 'transcript', interactionId: parsed.interactionId, turns: parsed.turns };
}

// audio is turned into { speaker, text } turns. transcription runs first, then for combined
// audio diarization decides who spoke when and the clusters are mapped to roles. the two
// models run in sequence on purpose: each saturates the cpu, so overlapping them is slower.
async function ingestAudio(file, { splitChannels = false, agentChannel = 0 } = {}) {
  const { channels, split, segments, text } = await whisperClient.transcribe(file, { split: splitChannels });
  const usable = (segments || []).filter((segment) => segment.text);

  // separated channels: the speaker is the channel, no diarization needed
  if (split && channels >= 2) {
    const turns = usable.map((segment) => ({
      speaker: segment.channel === agentChannel ? 'agent' : 'customer',
      text: segment.text,
    }));
    return { turns, ingest: { kind: 'audio', channels, split, segments: usable.length, diarization: 'skipped' } };
  }

  // combined audio: diarization assigns clusters, clusters map to roles
  const diar = usable.length ? await diarizationClient.diarize(file).catch(() => null) : null;
  if (usable.length && diar && diar.turns && diar.turns.length) {
    assignClusters(usable, diar.turns);
    const roles = clustersToRoles(usable, config.agentSpeaksFirst);
    const turns = usable.map((segment) => ({
      speaker: roles.get(segment.cluster) || 'unknown',
      text: segment.text,
    }));
    return {
      turns,
      ingest: { kind: 'audio', channels, split, segments: usable.length, diarization: 'ok', speakers: diar.speakers },
    };
  }

  // fallback: diarization unavailable or empty, speakers stay unknown so processing still runs
  const turns = usable.length
    ? usable.map((segment) => ({ speaker: 'unknown', text: segment.text }))
    : text
      ? [{ speaker: 'unknown', text }]
      : [];
  const status = !usable.length ? 'empty' : diar ? 'empty' : 'error';
  return { turns, ingest: { kind: 'audio', channels, split, segments: usable.length, diarization: status } };
}

module.exports = { prepare, ingestAudio };
