"""
Scoring metrics
===============

Both metrics work on (gold, predicted) pairs and return None when nothing was
scored, so an empty slice can never masquerade as a perfect one.
"""


# Correct / total over (gold, predicted) pairs
def accuracy(pairs):
  if not pairs:
    return None

  return sum(1 for gold, predicted in pairs if gold == predicted) / len(pairs)


# Per-class f1 averaged over the classes that appear in gold. The averaged set
# depends on gold only, never on a pipeline's own predictions, so the score is
# comparable across pipelines. Abstention (unknown) is never a class
def macro_f1(pairs, classes):
  if not pairs:
    return None

  scores = []
  for cls in classes:
    tp = sum(1 for gold, predicted in pairs if gold == cls and predicted == cls)
    fp = sum(1 for gold, predicted in pairs if gold != cls and predicted == cls)
    fn = sum(1 for gold, predicted in pairs if gold == cls and predicted != cls)
    if tp + fn == 0:
      continue
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    scores.append(f1)

  return sum(scores) / len(scores) if scores else None
