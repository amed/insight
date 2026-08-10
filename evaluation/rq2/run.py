"""
Research question 2: grounding vs direct extraction
===================================================

Compares p2 (retrieval-grounded) with p3 (direct) on the unsupported-claim
rate, using the predictions rq1 already stored. Nothing is uploaded twice:
rq1 runs both pipelines on every record and its prediction files carry the
citations and trace flags core kept per field. p1 is out of scope, it can not cite evidence.
Gold is not needed, every schema field of every record counts, not only the fields a batch has gold for.

Definitions:
- claim-bearing  a value that asserts something: not unknown, not none
- supported      claim-bearing with at least one surviving citation
- uncited        claim-bearing, the model cited nothing at all
- invalid-cited  claim-bearing, every cited line was dropped by the grounding filter (the model cited lines it was never shown)
- ucr            (uncited + invalid-cited) / claim-bearing
- validity       share of extracted fields whose first answer was schema-valid

Stages, matching the README:
1. prepare   collect rq1's stored p2 and p3 predictions
2. backfill  older prediction files that predate the evidence fields are upgraded in place from core's stored interactions
3. evidence  per record x field: claim-bearing, supported, uncited, invalid-cited, coerced
4. scores    results.csv + scores.json with the pre-committed criteria

Usage
-----
  python3 evaluation/rq2/run.py    # scoring only; core is contacted only when
                                   # old prediction files need the backfill

=============================================================================
Output shapes:

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
from pathlib import Path

# Shared helper one directory up
sys.path.append(str(Path(__file__).parent.parent))
from helper import api, files, services

# rq2 reuses rq1's stored predictions, nothing is uploaded twice
RQ1_PREDICTIONS = Path(__file__).parent.parent.joinpath("rq1", "out", "predictions")
OUT = Path(__file__).parent.joinpath("out")

PIPELINES = ("p2", "p3")

# Values that assert nothing; a field carrying one makes no claim to support
NO_CLAIM = ("unknown", "none", "")


# The file name is <batch>__<record>__<pipeline>, record ids never contain a
# double underscore, batch and pipeline names never contain any
def parse_name(path):
  batch, rest = path.stem.split("__", 1)
  record_id, pipeline = rest.rsplit("__", 1)

  return batch, record_id, pipeline


# Stage 1: rq1's p2 and p3 prediction files
def prepare():
  paths = [path for path in sorted(RQ1_PREDICTIONS.glob("*.json"))
           if parse_name(path)[2] in PIPELINES]
  if not paths:
    sys.exit(f"no p2/p3 predictions under {RQ1_PREDICTIONS}; run evaluation/rq1/run.py first")

  return paths


# Stage 2: prediction files written before the evidence fields existed are
# upgraded in place. The interactions still exist in core, found by their
# interaction id prefix; the newest complete one wins (earlier tries may have
# failed or timed out)
def backfill(core, paths):
  old = [path for path in paths if "citations" not in json.loads(path.read_text())]
  if not old:
    return

  print(f"{len(old)} prediction files predate the evidence fields, upgrading from core ...")
  services.check_services(["core"])
  listing = api.request("GET", f"{core}/interactions")

  unrecovered = []
  for path in old:
    batch, record_id, pipeline = parse_name(path)
    prefix = f"{record_id}--{pipeline}--"
    candidates = [entry for entry in listing
                  if entry["interaction_id"].startswith(prefix) and entry["status"] == "complete"]
    if not candidates:
      unrecovered.append(path.name)
      continue
    best = max(candidates, key=lambda entry: entry["id"])
    data = api.request("GET", f"{core}/interactions/{best['id']}")
    extra = api.evidence(core, best["id"], data["record"])
    prediction = {
      "status": data["record"]["status"],
      "api_id": best["id"],
      "fields": {f["name"]: f["value"] for f in data["record"].get("fields", [])},
      "citations": extra["citations"],
      "dropped_citations": extra["dropped_citations"],
      "coerced": extra["coerced"],
      "config_version": data["record"].get("config_version"),
    }
    files.write_json(path, prediction)

  print(f"upgraded {len(old) - len(unrecovered)} files")
  if unrecovered:
    sys.exit(f"{len(unrecovered)} predictions have no complete interaction in core and no "
             f"evidence data: {unrecovered[:5]}{' ...' if len(unrecovered) > 5 else ''}\n"
             f"delete those files and re-run evaluation/rq1/run.py, then run rq2 again")


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
  return {"fields": 0, "claim_bearing": 0, "supported": 0, "uncited": 0,
          "invalid_cited": 0, "coerced": 0, "not_complete": 0}


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
  parser = argparse.ArgumentParser(description="score rq2 from rq1's stored predictions")
  parser.add_argument("--core", default=services.ENDPOINTS["core"],
                      help="only contacted when old prediction files need the backfill")
  args = parser.parse_args()

  paths = prepare()
  backfill(args.core, paths)
  rows, tallies = evidence(paths)
  summary = scores(tallies)

  files.write_csv(
    OUT.joinpath("results.csv"),
    ["batch", "record", "pipeline", "field", "value", "claim_bearing",
     "citations", "dropped", "coerced", "supported"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"{len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
