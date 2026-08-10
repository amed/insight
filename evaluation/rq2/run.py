"""
Research question 2: grounding vs direct extraction
===================================================

Compares p2 (retrieval-grounded) with p3 (direct) on the unsupported-claim rate.
Self-contained: rq2 stores its own evidence predictions under out/predictions and never modifies rq1's files.
A cell is copied from rq1's stored prediction when that file already carries the evidence keys,
otherwise rq2 runs the cell itself via the core api. p1 is out of scope, it can not cite evidence.
Gold is not needed, every schema field of every record counts.

Definitions:
- claim-bearing  a value that asserts something: not unknown, not none
- supported      claim-bearing with at least one surviving citation
- uncited        claim-bearing, the model cited nothing at all
- invalid-cited  claim-bearing, every cited line was dropped by the grounding filter (the model cited lines it was never shown)
- ucr            (uncited + invalid-cited) / claim-bearing
- validity       share of extracted fields whose first answer was schema-valid

Stages, matching the README:
1. prepare   the same records rq1 evaluates, from the dataprep batches
2. collect   one evidence prediction per record x p2/p3: copied from rq1 when possible, run fresh otherwise, skipped when it already exists
3. evidence  per record x field: claim-bearing, supported, uncited, invalid-cited, coerced
4. scores    results.csv + scores.json with the pre-committed criteria

Usage
-----
  python3 evaluation/rq2/run.py                # core is only needed when cells must run fresh
  python3 evaluation/rq2/run.py --limit 5      # pilot, first 5 records per batch

=============================================================================
Output shapes:

out/predictions/<batch>__<record>__<pipeline>.json:
  status:            complete | failed | timeout
  api_id:            int (the interaction id in core)
  fields:            {field: predicted value}
  citations:         {field: [line ids that survived the grounding filter]}
  dropped_citations: {field: [cited line ids the filter rejected]}
  coerced:           {field: bool (the first answer was off-schema)}
  config_version:    str

out/results.csv columns:
  batch, record, pipeline, field, value, claim_bearing, citations, dropped, coerced, supported

out/scores.json:
  p2 / p3 -> overall and per batch -> fields, claim_bearing, supported, uncited, invalid_cited, ucr, coerced, validity, not_complete
  criteria:
    ucr_p2_lt_p3 (the pre-committed grounding criterion)
    validity_ge_95 per pipeline
"""

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

# The shared helper package lives one directory up
sys.path.append(str(Path(__file__).parent.parent))
from helper import api, datasets, files, services

# rq1's predictions are read-only input, reused when they carry evidence
RQ1_PREDICTIONS = Path(__file__).parent.parent.joinpath("rq1", "out", "predictions")
OUT = Path(__file__).parent.joinpath("out")
PREDICTIONS = Path(__file__).parent.joinpath("out", "predictions")

BATCHES = ("abcd-text", "maia-text", "hvb-audio")
PIPELINES = ("p2", "p3")

# Values that assert nothing; a field carrying one makes no claim to support
NO_CLAIM = ("unknown", "none", "")


# The file name is <batch>__<record>__<pipeline>, record ids never contain a
# double underscore, batch and pipeline names never contain any
def parse_name(path):
  batch, rest = path.stem.split("__", 1)
  record_id, pipeline = rest.rsplit("__", 1)

  return batch, record_id, pipeline


# Stage 1: the same records rq1 evaluates. Only records with a gold entry are kept,
# this drops the hvb asr variant records (they belong to rq3)
def prepare(name):
  records, gold = datasets.load_batch(name)

  return [record for record in records if record["interaction_id"] in gold]


# The evidence core kept per field: the surviving citations from the record,
# the coercion flag and the dropped citations from the extract:<field> steps
def evidence_of(core, api_id, record_data):
  steps = api.request("GET", f"{core}/interactions/{api_id}/steps")
  coerced = {}
  dropped = {}
  for step in steps:
    if step["name"].startswith("extract:") and step["status"] == "ok":
      field = step["name"].split(":", 1)[1]
      coerced[field] = bool(step["detail"].get("coerced", False))
      dropped[field] = step["detail"].get("dropped_citations", [])

  return {
    "citations": {f["name"]: f.get("citations", []) for f in record_data.get("fields", [])},
    "dropped_citations": dropped,
    "coerced": coerced,
  }


# Local upload that also stores the evidence. The shared api.predict stays
# untouched and rq1's files are never modified
def predict_with_evidence(core, record, pipeline, timeout):
  payload = dict(record)
  payload["interaction_id"] = f"{record['interaction_id']}--{pipeline}--{uuid.uuid4().hex[:8]}"
  body, headers = api.multipart({"pipeline": pipeline, "schema": "v1"},
                                f"{record['interaction_id']}.json",
                                json.dumps(payload).encode())
  created = api.request("POST", f"{core}/interactions", body, headers)

  deadline = time.time() + timeout
  while time.time() < deadline:
    data = api.request("GET", f"{core}/interactions/{created['id']}")
    status = (data.get("record") or {}).get("status")
    if status in ("complete", "failed"):
      extra = evidence_of(core, created["id"], data["record"])
      return {
        "status": status,
        "api_id": created["id"],
        "fields": {f["name"]: f["value"] for f in data["record"].get("fields", [])},
        "citations": extra["citations"],
        "dropped_citations": extra["dropped_citations"],
        "coerced": extra["coerced"],
        "config_version": data["record"].get("config_version"),
      }
    time.sleep(2)

  return {"status": "timeout", "api_id": created["id"], "fields": {}, "citations": {},
          "dropped_citations": {}, "coerced": {}, "config_version": None}


# A cell that neither exists in out/predictions nor can be copied from an rq1
# prediction carrying evidence must be run fresh
def missing_cells(all_records):
  missing = []
  for name, records in all_records.items():
    for record in records:
      for pipeline in PIPELINES:
        target = PREDICTIONS.joinpath(f"{name}__{record['interaction_id']}__{pipeline}.json")
        if target.exists():
          continue
        reusable = RQ1_PREDICTIONS.joinpath(target.name)
        if reusable.exists() and "citations" in json.loads(reusable.read_text()):
          continue
        missing.append(target.name)

  return missing


# Stage 2: one evidence prediction per record x pipeline, skipped when it
# exists, copied from rq1 when its file carries the evidence keys
def collect(core, name, records, timeout):
  for record in records:
    for pipeline in PIPELINES:
      target = PREDICTIONS.joinpath(f"{name}__{record['interaction_id']}__{pipeline}.json")
      if target.exists():
        continue

      reusable = RQ1_PREDICTIONS.joinpath(target.name)
      if reusable.exists():
        prediction = json.loads(reusable.read_text())
        if "citations" in prediction:
          files.write_json(target, prediction)
          continue

      print(f"{name} {record['interaction_id']} {pipeline} ...", flush=True)
      files.write_json(target, predict_with_evidence(core, record, pipeline, timeout))


# Stage 3: per record x field evidence. Only complete predictions count,
# the rest are tallied as not_complete
def evidence(paths):
  rows = []
  tallies = {}
  for path in paths:
    batch, record_id, pipeline = parse_name(path)
    prediction = json.loads(path.read_text())

    if prediction["status"] != "complete":
      for scope in ((pipeline, "overall"), (pipeline, batch)):
        tally = tallies.setdefault(scope, blank_tally())
        tally["not_complete"] += 1
      continue

    for field, value in prediction["fields"].items():
      claim_bearing = value not in NO_CLAIM
      citations = prediction["citations"].get(field, [])
      dropped = prediction["dropped_citations"].get(field, [])
      coerced = prediction["coerced"].get(field, False)
      supported = claim_bearing and len(citations) > 0

      for scope in ((pipeline, "overall"), (pipeline, batch)):
        tally = tallies.setdefault(scope, blank_tally())
        tally["fields"] += 1
        tally["coerced"] += 1 if coerced else 0
        if claim_bearing:
          tally["claim_bearing"] += 1
          if supported:
            tally["supported"] += 1
          elif len(dropped) > 0:
            tally["invalid_cited"] += 1
          else:
            tally["uncited"] += 1

      rows.append([batch, record_id, pipeline, field, value,
                   1 if claim_bearing else 0, len(citations), len(dropped),
                   1 if coerced else 0, 1 if supported else 0])

  return rows, tallies


def blank_tally():
  return {"fields": 0, "claim_bearing": 0, "supported": 0, "uncited": 0, "invalid_cited": 0, "coerced": 0, "not_complete": 0}


# Stage 4: rates per tally plus the pre-committed criteria
def scores(tallies):
  summary = {}
  for (pipeline, scope), tally in sorted(tallies.items()):
    unsupported = tally["uncited"] + tally["invalid_cited"]
    tally["ucr"] = unsupported / tally["claim_bearing"] if tally["claim_bearing"] else None
    tally["validity"] = (tally["fields"] - tally["coerced"]) / tally["fields"] if tally["fields"] else None
    summary.setdefault(pipeline, {})[scope] = tally

  p2 = summary.get("p2", {}).get("overall", blank_tally())
  p3 = summary.get("p3", {}).get("overall", blank_tally())

  summary["criteria"] = {
    "ucr_p2_lt_p3": {
      "p2": p2.get("ucr"),
      "p3": p3.get("ucr"),
      "met": p2.get("ucr") is not None and p3.get("ucr") is not None and p2["ucr"] < p3["ucr"],
    },
    "validity_ge_95": {
      "p2": {"validity": p2.get("validity"),
             "met": p2.get("validity") is not None and p2["validity"] >= 0.95},
      "p3": {"validity": p3.get("validity"),
             "met": p3.get("validity") is not None and p3["validity"] >= 0.95},
    },
  }

  return summary


def main():
  parser = argparse.ArgumentParser(description="run rq2, store results.csv and scores.json")
  parser.add_argument("--core", default=services.ENDPOINTS["core"])
  parser.add_argument("--timeout", type=int, default=900, help="seconds per record")
  parser.add_argument("--limit", type=int, help="only the first n records per batch (pilot)")
  args = parser.parse_args()

  all_records = {name: prepare(name)[: args.limit] for name in BATCHES}

  # The stack is only needed when cells must run fresh; p2 and p3 need
  # retrieval and the llm, the baseline is not involved
  if missing_cells(all_records):
    services.check_services(["core", "embeddings", "ollama"])

  for name, records in all_records.items():
    collect(args.core, name, records, args.timeout)

  rows, tallies = evidence(sorted(PREDICTIONS.glob("*.json")))
  summary = scores(tallies)

  files.write_csv(
    OUT.joinpath("results.csv"),
    ["batch", "record", "pipeline", "field", "value", "claim_bearing", "citations", "dropped", "coerced", "supported"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)

  print(f"{len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
