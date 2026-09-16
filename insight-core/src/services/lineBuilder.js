// Seconds become whole milliseconds, anything that is not a finite number becomes null.
function toMs(seconds) {
  return Number.isFinite(seconds) ? Math.round(seconds * 1000) : null;
}

// Turns a list of {speaker, text} turns into line-addressable units with stable ids ("L0001", "L0002", ...).
// Segment times are kept when the turn carries them, audio turns do and transcript turns usually do not.
function buildLines(turns) {
  return turns.map((turn, i) => ({
    lineId: `L${String(i + 1).padStart(4, '0')}`,
    ordinal: i + 1,
    speaker: turn.speaker,
    text: turn.text,
    startMs: toMs(turn.start),
    endMs: toMs(turn.end),
  }));
}

module.exports = { buildLines };
