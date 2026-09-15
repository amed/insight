// Pure functions that map whisper segments onto diarization turns and then onto agent/customer roles.
// No i/o, so they are easy to reason about and to test.

// The overlap in seconds between two [start, end] intervals.
function overlap(aStart, aEnd, bStart, bEnd) {
  return Math.max(0, Math.min(aEnd, bEnd) - Math.max(aStart, bStart));
}

// Each segment is assigned the diarization turn it overlaps most,
// with a confidence (overlap / segment duration).
// Segments are mutated in place and returned.
function assignClusters(segments, turns) {
  for (const segment of segments) {
    let best = null;
    let bestOverlap = 0;

    for (const turn of turns) {
      const value = overlap(segment.start, segment.end, turn.start, turn.end);
      if (value > bestOverlap) {
        bestOverlap = value;
        best = turn;
      }
    }

    // When no turn intersects (timebase or vad mismatch), the nearest turn by start is used.
    if (!best && turns.length) {
      best = turns.reduce((closest, turn) =>
        Math.abs(turn.start - segment.start) < Math.abs(closest.start - segment.start) ? turn : closest
      );
    }

    const duration = Math.max(segment.end - segment.start, 1e-6);
    segment.cluster = best ? best.speaker : null;
    segment.confidence = bestOverlap / duration;
  }

  return segments;
}

// The two clusters with the most speaking time are kept as the parties.
// The one that speaks first is the agent (support calls open with the agent greeting), configurable.
// A map of cluster label -> 'agent' | 'customer' is returned.
function clustersToRoles(segments, agentSpeaksFirst = true) {
  const totals = new Map();
  const earliest = new Map();

  for (const segment of segments) {
    if (!segment.cluster) continue;
    const duration = Math.max(segment.end - segment.start, 0);
    totals.set(segment.cluster, (totals.get(segment.cluster) || 0) + duration);
    const start = earliest.has(segment.cluster)
      ? Math.min(earliest.get(segment.cluster), segment.start)
      : segment.start;
    earliest.set(segment.cluster, start);
  }

  const ranked = [...totals.keys()].sort((a, b) => totals.get(b) - totals.get(a));
  const roles = new Map();
  if (ranked.length === 0) return roles;
  if (ranked.length === 1) {
    roles.set(ranked[0], 'agent');
    return roles;
  }

  const [first, second] = ranked;
  const earlier = earliest.get(first) <= earliest.get(second) ? first : second;
  const later = earlier === first ? second : first;

  const agent = agentSpeaksFirst ? earlier : later;
  const customer = agent === earlier ? later : earlier;
  roles.set(agent, 'agent');
  roles.set(customer, 'customer');

  // Any minor third or later cluster is collapsed to customer.
  for (const cluster of ranked.slice(2)) {
    roles.set(cluster, 'customer');
  }

  return roles;
}

module.exports = { overlap, assignClusters, clustersToRoles };
