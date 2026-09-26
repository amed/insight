const { overlap, assignClusters, clustersToRoles } = require('./diarize');

describe('overlap', () => {
  test('returns the shared seconds of two intervals', () => {
    expect(overlap(0, 2, 1, 3)).toBe(1);
  });

  test('returns zero when the intervals do not touch', () => {
    expect(overlap(0, 1, 2, 3)).toBe(0);
  });
});

describe('assignClusters', () => {
  const turns = [
    { start: 0, end: 2, speaker: 'A' },
    { start: 2, end: 4, speaker: 'B' },
  ];

  test('gives a segment the turn it overlaps most, with the overlap share as confidence', () => {
    const [segment] = assignClusters([{ start: 1.5, end: 3.5 }], turns);
    expect(segment.cluster).toBe('B');
    expect(segment.confidence).toBeCloseTo(0.75);
  });

  test('falls back to the nearest turn by start when nothing overlaps', () => {
    const [segment] = assignClusters([{ start: 10, end: 11 }], turns);
    expect(segment.cluster).toBe('B');
    expect(segment.confidence).toBe(0);
  });
});

describe('clustersToRoles', () => {
  // A speaks most and first, B second, C is a sliver.
  const segments = [
    { start: 0, end: 3, cluster: 'A' },
    { start: 3, end: 5, cluster: 'B' },
    { start: 5, end: 5.2, cluster: 'C' },
  ];

  test('the earlier of the two largest clusters is the agent by default', () => {
    const roles = clustersToRoles(segments);
    expect(roles.get('A')).toBe('agent');
    expect(roles.get('B')).toBe('customer');
  });

  test('the flag inverts the assignment', () => {
    const roles = clustersToRoles(segments, false);
    expect(roles.get('A')).toBe('customer');
    expect(roles.get('B')).toBe('agent');
  });

  test('a minor third cluster is collapsed to customer', () => {
    expect(clustersToRoles(segments).get('C')).toBe('customer');
  });
});
