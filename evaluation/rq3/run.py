"""
Research question 3: asr error propagation
==========================================

Compares the same 50 hvb calls across the four input variants, from the
predictions the one cycle stored (evaluation/run.py). This module uploads
nothing. oracle is the reference: wer and role accuracy are measured for the
degraded variants, and every intent answer is paired with the same pipeline's
oracle answer to count flips.

Definitions:
- wer            (substitutions + deletions + insertions) / reference words, one pinned normalization, computed for asr, mono, and stereo against the oracle turns
- role accuracy  each produced line matched to the oracle turn with the largest word overlap,
                 its speaker judged against that turn. Computed for mono and stereo only,
                 the text variants carry the corpus roles by construction
- flip           same record, same pipeline: oracle correct but the variant wrong (to_wrong), or the reverse (to_right)

Usage
-----
  python3 evaluation/rq3/run.py

=============================================================================
Output shapes:

out/results.csv columns:
  record, variant, pipeline, status, gold, predicted, correct, wer, role_accuracy (empty gold = the call's task is outside the schema, excluded from accuracy)

out/scores.json:
  variant -> pipeline -> {accuracy, scored, mean_wer, mean_role_accuracy, to_wrong, to_right, paired, not_complete}
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

BATCH = "hvb-audio"
VARIANTS = ("oracle", "asr", "mono", "stereo")
PIPELINES = ("p1", "p2", "p3")


def cell(record_id, variant, pipeline):
  return PREDICTIONS.joinpath(f"{BATCH}__{record_id}__{variant}__{pipeline}.json")


# The oracle turns per record, the reference for wer and role accuracy
def oracle_turns(record_id):
  record = datasets.DATASETS.joinpath(BATCH, "records", f"{record_id}.json")

  return json.loads(record.read_text())["turns"]


# One row per record x variant x pipeline: the intent answer plus, for the
# degraded variants, how far the produced text and speakers drifted from oracle
def collect_rows(gold):
  rows = []
  for record_id in sorted(gold):
    turns = oracle_turns(record_id)
    reference = " ".join(turn["text"] for turn in turns)

    for variant in VARIANTS:
      for pipeline in PIPELINES:
        path = cell(record_id, variant, pipeline)
        if not path.exists():
          continue
        prediction = json.loads(path.read_text())

        gold_intent = gold[record_id]["intent"]
        predicted = prediction["fields"].get("intent", "")
        correct = ""
        if gold_intent is not None and prediction["status"] == "complete":
          correct = 1 if predicted == gold_intent else 0

        wer = ""
        role = ""
        if variant != "oracle" and prediction["status"] == "complete":
          hypothesis = " ".join(line["text"] for line in prediction.get("lines", []))
          value = metrics.wer(reference, hypothesis)
          wer = round(value, 4) if value is not None else ""
        if variant in ("mono", "stereo") and prediction["status"] == "complete":
          value = metrics.role_accuracy(prediction.get("lines", []), turns)
          role = round(value, 4) if value is not None else ""

        rows.append([record_id, variant, pipeline, prediction["status"],
                     gold_intent if gold_intent is not None else "",
                     predicted, correct, wer, role])

  return rows


# Aggregates per variant x pipeline, with the paired flips against oracle
def scores(rows):
  # correct-by-cell index for the flip pairing
  correct_of = {}
  for record_id, variant, pipeline, status, gold, predicted, correct, wer, role in rows:
    if correct != "":
      correct_of[(record_id, variant, pipeline)] = correct

  summary = {}
  for variant in VARIANTS:
    for pipeline in PIPELINES:
      slice_rows = [row for row in rows if row[1] == variant and row[2] == pipeline]
      if not slice_rows:
        continue
      scored = [row for row in slice_rows if row[6] != ""]
      wers = [row[7] for row in slice_rows if row[7] != ""]
      roles = [row[8] for row in slice_rows if row[8] != ""]

      to_wrong = 0
      to_right = 0
      paired = 0
      if variant != "oracle":
        for row in scored:
          oracle_correct = correct_of.get((row[0], "oracle", pipeline))
          if oracle_correct is None:
            continue
          paired += 1
          if oracle_correct == 1 and row[6] == 0:
            to_wrong += 1
          if oracle_correct == 0 and row[6] == 1:
            to_right += 1

      summary.setdefault(variant, {})[pipeline] = {
        "accuracy": sum(row[6] for row in scored) / len(scored) if scored else None,
        "scored": len(scored),
        "mean_wer": sum(wers) / len(wers) if wers else None,
        "mean_role_accuracy": sum(roles) / len(roles) if roles else None,
        "to_wrong": to_wrong,
        "to_right": to_right,
        "paired": paired,
        "not_complete": sum(1 for row in slice_rows if row[3] != "complete"),
      }

  return summary


def main():
  if not PREDICTIONS.exists():
    sys.exit(f"no predictions under {PREDICTIONS}; run evaluation/run.py first")

  gold = json.loads(datasets.DATASETS.joinpath(BATCH, "gold.json").read_text())
  rows = collect_rows(gold)
  summary = scores(rows)

  files.write_csv(
    OUT.joinpath("results.csv"),
    ["record", "variant", "pipeline", "status", "gold", "predicted", "correct",
     "wer", "role_accuracy"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"rq3: {len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"rq3: scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
