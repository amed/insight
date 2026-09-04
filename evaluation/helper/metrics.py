"""
Scoring metrics
===============

accuracy and macro_f1 work on (gold, predicted) pairs, wer and role_accuracy
on produced text against reference turns. Everything returns None when nothing
was scored, so an empty slice can never masquerade as a perfect one.
"""

import re


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


# One pinned normalization for every wer and role comparison: lowercase, strip
# every character that is not a letter, digit, or whitespace, collapse whitespace
def normalize(text):
  text = text.lower()
  text = re.sub(r"[^a-z0-9\s]", "", text)

  return re.sub(r"\s+", " ", text).strip()


# Word error rate: (substitutions + deletions + insertions) / reference words,
# from the classic levenshtein edit-distance alignment over words.
# None when the reference is empty
def wer(reference, hypothesis):
  ref = normalize(reference).split()
  hyp = normalize(hypothesis).split()

  # dp[i][j] = edit cost for ref[:i] vs hyp[:j]
  rows = len(ref) + 1
  cols = len(hyp) + 1
  dp = [[0] * cols for _ in range(rows)]
  for i in range(1, rows):
    dp[i][0] = i
  for j in range(1, cols):
    dp[0][j] = j

  for i in range(1, rows):
    for j in range(1, cols):
      if ref[i - 1] == hyp[j - 1]:
        dp[i][j] = dp[i - 1][j - 1]
      else:
        dp[i][j] = 1 + min(dp[i - 1][j - 1], dp[i - 1][j], dp[i][j - 1])

  return dp[-1][-1] / len(ref) if ref else None


# Line-level speaker agreement against known roles. Positional comparison is
# wrong when asr segments the audio differently than the reference turns, so
# each produced line is matched to the reference turn with the largest word
# overlap and judged against that turn's speaker. Lines sharing no word with
# any turn are skipped
def role_accuracy(lines, turns):
  turn_words = [set(normalize(turn["text"]).split()) for turn in turns]
  correct = 0
  total = 0
  for line in lines:
    words = set(normalize(line["text"]).split())
    best = None
    best_overlap = 0
    for i, candidate in enumerate(turn_words):
      overlap = len(words & candidate)
      if overlap > best_overlap:
        best = i
        best_overlap = overlap
    if best is None:
      continue
    total += 1
    correct += 1 if line["speaker"] == turns[best]["speaker"] else 0

  return correct / total if total else None
