"""
Research question 1: comparative field accuracy
===============================================

Runs every record of the three test batches through the three pipelines and
stores everything needed to answer rq1 in two files, no presentation layer:
- out/results.csv  one row per record x pipeline x field, the full picture
- out/scores.json  accuracy and macro-f1 per batch x pipeline x field

Which batch scores which fields (gold exists nowhere else):
- abcd-text   intent, issue_type, agent_action
- maia-text   sentiment, resolution_status
- hvb-audio   intent (oracle transcript records only, audio variants are rq3)

Stages (the README's report stage is the presentation layer, not built yet):
1. prepare  load the batches and pair records with gold
2. runner   every record through p1, p2, p3 via the core api, one prediction
            file per record x pipeline, existing files are skipped so an
            interrupted run continues where it stopped
3. scores   predictions vs gold, written as results.csv + scores.json

Usage
-----
  python3 evaluation/rq1/run.py                  # full run, needs the stack up
  python3 evaluation/rq1/run.py --limit 5        # pilot, first 5 records per batch

=============================================================================
Output shapes:

out/predictions/<batch>__<record>__<pipeline>.json:
  status:         complete | failed | timeout
  fields:         {field: predicted value}
  config_version: str (what configuration produced the record)

out/results.csv columns:
  batch, record, pipeline, status, field, gold, predicted, correct
  (empty gold = the record has no gold for that field, excluded from scores)

out/scores.json:
  batch -> pipeline -> field -> {accuracy, macro_f1, scored, correct}
"""

import argparse
import json
import sys
from pathlib import Path

# The shared helper package lives one directory up, one module per concern
sys.path.append(str(Path(__file__).parent.parent))
from helper import api, datasets, files, metrics, services

# Which fields have gold in which batch
BATCHES = {
  "abcd-text": ["intent", "issue_type", "agent_action"],
  "maia-text": ["sentiment", "resolution_status"],
  "hvb-audio": ["intent"],
}

PIPELINES = ("p1", "p2", "p3")

OUT = Path(__file__).parent.joinpath("out")
PREDICTIONS = Path(__file__).parent.joinpath("out", "predictions")


# Stage 1: records paired with gold. Only records with a gold entry are kept,
# this drops the hvb asr variant records (they belong to rq3)
def prepare(name):
  records, gold = datasets.load_batch(name)
  records = [record for record in records if record["interaction_id"] in gold]

  return records, gold


# Stage 2: one prediction file per record x pipeline, skipped when it exists
def runner(core, name, records, timeout):
  for record in records:
    for pipeline in PIPELINES:
      target = PREDICTIONS.joinpath(f"{name}__{record['interaction_id']}__{pipeline}.json")
      if target.exists():
        continue
      print(f"{name} {record['interaction_id']} {pipeline} ...", flush=True)
      prediction = api.predict(core, record, pipeline, timeout)
      files.write_json(target, prediction)


# Stage 3: predictions vs gold. Every stored prediction becomes one csv row per
# gold field. Only complete predictions are scored:
# a failed or timed out prediction is not a wrong answer,
# it is counted separately as not_complete so an infrastructure problem never lowers a pipeline's accuracy
def scores(all_gold):
  rows = []
  pairs = {}
  not_complete = {}
  for path in sorted(PREDICTIONS.glob("*.json")):
    # The file name is <batch>__<record>__<pipeline>, record ids never contain
    # a double underscore, batch and pipeline names never contain any
    name, rest = path.stem.split("__", 1)
    record_id, pipeline = rest.rsplit("__", 1)
    prediction = json.loads(path.read_text())

    for field in BATCHES[name]:
      gold = all_gold[name][record_id].get(field)
      predicted = prediction["fields"].get(field, "")
      correct = ""
      if gold is not None and prediction["status"] == "complete":
        correct = 1 if predicted == gold else 0
        pairs.setdefault((name, pipeline, field), []).append((gold, predicted))
      elif gold is not None:
        not_complete[(name, pipeline, field)] = not_complete.get((name, pipeline, field), 0) + 1
      rows.append([name, record_id, pipeline, prediction["status"], field,
                   gold if gold is not None else "", predicted, correct])

  # The union of both key sets, so a slice whose cells all failed still appears
  values = datasets.schema_values()
  summary = {}
  for key in sorted(set(pairs) | set(not_complete)):
    name, pipeline, field = key
    scored = pairs.get(key, [])
    summary.setdefault(name, {}).setdefault(pipeline, {})[field] = {
      "accuracy": metrics.accuracy(scored),
      "macro_f1": metrics.macro_f1(scored, values[field]),
      "scored": len(scored),
      "correct": sum(1 for gold, predicted in scored if gold == predicted),
      "not_complete": not_complete.get(key, 0),
    }

  return rows, summary


def main():
  parser = argparse.ArgumentParser(description="run rq1, store results.csv and scores.json")
  parser.add_argument("--core", default=services.ENDPOINTS["core"])
  parser.add_argument("--timeout", type=int, default=900, help="seconds per record")
  parser.add_argument("--limit", type=int, help="only the first n records per batch (pilot)")
  args = parser.parse_args()

  # Text uploads through the three pipelines need these services up
  # whisper and diarization are audio-path only and not required for rq1
  services.check_services(["core", "baseline", "embeddings", "ollama"])

  all_gold = {}
  for name in BATCHES:
    records, gold = prepare(name)
    all_gold[name] = gold
    runner(args.core, name, records[: args.limit], args.timeout)

  rows, summary = scores(all_gold)
  files.write_csv(
    OUT.joinpath("results.csv"),
    ["batch", "record", "pipeline", "status", "field", "gold", "predicted", "correct"],
    rows
  )

  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"{len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
