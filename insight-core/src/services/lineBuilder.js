// Turns a list of {speaker, text} turns into line-addressable units with
// stable ids ("L0001", "L0002", ...). Mirrors the original from_turns logic.
function buildLines(turns) {
  return turns.map((turn, i) => ({
    lineId: `L${String(i + 1).padStart(4, '0')}`,
    ordinal: i + 1,
    speaker: turn.speaker,
    text: turn.text,
  }));
}

module.exports = { buildLines };
