"""
Research question 4: field extension by configuration
=====================================================

Scores the schema v2 cells (the hvb oracle records with the banking_task field
added by configuration alone), from the predictions the one cycle stored
(evaluation/run.py). This module uploads nothing.

Gold needs no annotation: every call's task label is stored as intent_source
in the batch gold, snake_cased it is the banking_task value. p1's record fails
on its schema claim by design, the refusal count is part of the answer: the
supervised pipeline structurally can not follow a configuration-only change.

Criteria (pre-committed):
- first-attempt validity at least 95 percent for p2 and p3
- banking_task accuracy within 10 points of intent accuracy on the same calls

Usage
-----
  python3 evaluation/rq4/run.py

=============================================================================
Output shapes:

out/results.csv columns:
  record, pipeline, status, field, gold, predicted, correct, citations, coerced

out/scores.json:
  p2 / p3 -> {banking_task_accuracy, intent_accuracy, banking_scored, intent_scored, supported_banking_claims, validity, fields, coerced, not_complete}
  p1 -> {cells, failed (the designed refusal)}
  criteria:
    validity_ge_95 per pipeline banking_within_10_of_intent per pipeline
"""

import json
import sys
from pathlib import Path

# The shared helper package lives one directory up
sys.path.append(str(Path(__file__).parent.parent))
from helper import datasets, files

# The store the one cycle fills, read-only here
PREDICTIONS = Path(__file__).parent.parent.joinpath("out", "predictions", "v2")
OUT = Path(__file__).parent.joinpath("out")

BATCH = "hvb-audio"
PIPELINES = ("p2", "p3")

# Values that assert nothing; an unknown with citations is still no claim
NO_CLAIM = ("unknown", "none", "")


# The banking_task gold is the call's task label in snake case, matching the
# values declared in insight-core/schemas/v2.json
def banking_gold(gold_entry):
  return gold_entry["intent_source"].replace(" ", "_")


# One row per record x pipeline x scored field, plus the p1 refusal rows.
# Validity is tallied over every v2 field of each complete prediction, not
# only the two scored ones, a coercion on any field is a validity failure
def collect_rows(gold):
  rows = []
  validity = {}
  for path in sorted(PREDICTIONS.glob("*.json")):
    batch, rest = path.stem.split("__", 1)
    record_id, variant, pipeline = rest.rsplit("__", 2)
    prediction = json.loads(path.read_text())

    if pipeline == "p1":
      # The designed refusal: the artifact claims v1, core fails the v2 record
      rows.append([record_id, "p1", prediction["status"], "", "", "", "", "", ""])
      continue

    if prediction["status"] == "complete":
      tally = validity.setdefault(pipeline, {"fields": 0, "coerced": 0})
      tally["fields"] += len(prediction["fields"])
      tally["coerced"] += sum(1 for flag in prediction.get("coerced", {}).values() if flag)

    for field, gold_value in (("banking_task", banking_gold(gold[record_id])),
                              ("intent", gold[record_id]["intent"])):
      predicted = prediction["fields"].get(field, "")
      correct = ""
      if gold_value is not None and prediction["status"] == "complete":
        correct = 1 if predicted == gold_value else 0
      rows.append([record_id, pipeline, prediction["status"], field,
                   gold_value if gold_value is not None else "", predicted, correct,
                   len(prediction.get("citations", {}).get(field, [])),
                   1 if prediction.get("coerced", {}).get(field, False) else 0])

  return rows, validity


# Aggregates per pipeline plus the pre-committed criteria
def scores(rows, validity):
  summary = {}

  p1_rows = [row for row in rows if row[1] == "p1"]
  summary["p1"] = {
    "cells": len(p1_rows),
    "failed": sum(1 for row in p1_rows if row[2] == "failed"),
  }

  for pipeline in PIPELINES:
    slice_rows = [row for row in rows if row[1] == pipeline]
    banking = [row for row in slice_rows if row[3] == "banking_task" and row[6] != ""]
    intent = [row for row in slice_rows if row[3] == "intent" and row[6] != ""]
    tally = validity.get(pipeline, {"fields": 0, "coerced": 0})

    summary[pipeline] = {
      "banking_task_accuracy": sum(row[6] for row in banking) / len(banking) if banking else None,
      "intent_accuracy": sum(row[6] for row in intent) / len(intent) if intent else None,
      "banking_scored": len(banking),
      "intent_scored": len(intent),
      "supported_banking_claims": sum(1 for row in banking
                                      if row[7] > 0 and row[5] not in NO_CLAIM),
      "fields": tally["fields"],
      "coerced": tally["coerced"],
      "validity": ((tally["fields"] - tally["coerced"]) / tally["fields"]
                   if tally["fields"] else None),
      "not_complete": len({row[0] for row in slice_rows if row[2] != "complete"}),
    }

  summary["criteria"] = {"validity_ge_95": {}, "banking_within_10_of_intent": {}}
  for pipeline in PIPELINES:
    validity = summary[pipeline]["validity"]
    banking = summary[pipeline]["banking_task_accuracy"]
    intent = summary[pipeline]["intent_accuracy"]
    summary["criteria"]["validity_ge_95"][pipeline] = {
      "validity": validity,
      "met": validity is not None and validity >= 0.95,
    }
    summary["criteria"]["banking_within_10_of_intent"][pipeline] = {
      "banking_task": banking,
      "intent": intent,
      "met": banking is not None and intent is not None and banking >= intent - 0.10,
    }

  return summary


def main():
  if not PREDICTIONS.exists():
    sys.exit(f"no v2 predictions under {PREDICTIONS}; run evaluation/run.py first")

  gold = json.loads(datasets.DATASETS.joinpath(BATCH, "gold.json").read_text())
  rows, validity = collect_rows(gold)
  summary = scores(rows, validity)

  files.write_csv(
    OUT.joinpath("results.csv"),
    ["record", "pipeline", "status", "field", "gold", "predicted", "correct",
     "citations", "coerced"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"rq4: {len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"rq4: scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
