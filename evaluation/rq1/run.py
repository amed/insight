"""
Research question 1: comparative field accuracy
===============================================

Scores the three pipelines against gold, per field, from the predictions the
one cycle stored (evaluation/run.py). This module uploads nothing.

Which batch scores which fields (gold exists nowhere else):
- abcd-text   intent, issue_type, agent_action (variant text)
- maia-text   sentiment, resolution_status (variant text)
- hvb-audio   intent (variant oracle only, the audio variants are rq3)

Only complete predictions are scored: a failed or timed out prediction is not
a wrong answer, it is counted separately as not_complete so an infrastructure
problem never lowers a pipeline's accuracy.

Usage
-----
  python3 evaluation/rq1/run.py

=============================================================================
Output shapes:

out/results.csv columns:
  batch, record, pipeline, status, field, gold, predicted, correct
  (empty gold = the record has no gold for that field, excluded from scores)

out/scores.json:
  batch -> pipeline -> field -> {accuracy, macro_f1, scored, correct, not_complete}
"""

import json
import sys
from pathlib import Path

# The shared helper package lives one directory up
sys.path.append(str(Path(__file__).parent.parent))
from helper import datasets, files, metrics

# The store the one cycle fills, read-only here
PREDICTIONS = Path(__file__).parent.parent.joinpath("out", "predictions", "v1")
OUT = Path(__file__).parent.joinpath("out")

# Which fields have gold in which batch, and which variant is rq1's input
BATCHES = {
  "abcd-text": ("text", ["intent", "issue_type", "agent_action"]),
  "maia-text": ("text", ["sentiment", "resolution_status"]),
  "hvb-audio": ("oracle", ["intent"]),
}

PIPELINES = ("p1", "p2", "p3")


# The file name is <batch>__<record>__<variant>__<pipeline>, record ids never
# contain a double underscore, the other segments never contain any
def parse_name(path):
  batch, rest = path.stem.split("__", 1)
  record_id, variant, pipeline = rest.rsplit("__", 2)

  return batch, record_id, variant, pipeline


# Predictions vs gold. Every prediction becomes one csv row per gold field,
# complete rows are also collected into (gold, predicted) pairs for the scores
def scores(all_gold):
  rows = []
  pairs = {}
  not_complete = {}
  for path in sorted(PREDICTIONS.glob("*.json")):
    batch, record_id, variant, pipeline = parse_name(path)
    if batch not in BATCHES or variant != BATCHES[batch][0]:
      continue
    prediction = json.loads(path.read_text())

    for field in BATCHES[batch][1]:
      gold = all_gold[batch][record_id].get(field)
      predicted = prediction["fields"].get(field, "")
      correct = ""
      if gold is not None and prediction["status"] == "complete":
        correct = 1 if predicted == gold else 0
        pairs.setdefault((batch, pipeline, field), []).append((gold, predicted))
      elif gold is not None:
        not_complete[(batch, pipeline, field)] = not_complete.get((batch, pipeline, field), 0) + 1
      rows.append([batch, record_id, pipeline, prediction["status"], field,
                   gold if gold is not None else "", predicted, correct])

  # The union of both key sets, so a slice whose cells all failed still appears
  values = datasets.schema_values()
  summary = {}
  for key in sorted(set(pairs) | set(not_complete)):
    batch, pipeline, field = key
    scored = pairs.get(key, [])
    summary.setdefault(batch, {}).setdefault(pipeline, {})[field] = {
      "accuracy": metrics.accuracy(scored),
      "macro_f1": metrics.macro_f1(scored, values[field]),
      "scored": len(scored),
      "correct": sum(1 for gold, predicted in scored if gold == predicted),
      "not_complete": not_complete.get(key, 0),
    }

  return rows, summary


def main():
  if not PREDICTIONS.exists():
    sys.exit(f"no predictions under {PREDICTIONS}; run evaluation/run.py first")

  all_gold = {}
  for batch in BATCHES:
    gold_file = datasets.DATASETS.joinpath(batch, "gold.json")
    all_gold[batch] = json.loads(gold_file.read_text())

  rows, summary = scores(all_gold)
  files.write_csv(
    OUT.joinpath("results.csv"),
    ["batch", "record", "pipeline", "status", "field", "gold", "predicted", "correct"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"rq1: {len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"rq1: scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
