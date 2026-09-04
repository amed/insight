"""
Research question 2: grounding vs direct extraction
===================================================

Compares p2 (retrieval-grounded) with p3 (direct) on the unsupported-claim
rate, from the predictions the one cycle stored (evaluation/run.py). This
module uploads nothing. p1 is out of scope, it can not cite evidence. Gold is
not needed, every schema field of every record counts. Only the text and
oracle variants are read, the audio variants belong to rq3.

Definitions:
- claim-bearing  a value that asserts something: not unknown, not none
- supported      claim-bearing with at least one surviving citation
- uncited        claim-bearing, the model cited nothing at all
- invalid-cited  claim-bearing, every cited line was dropped by the grounding
                 filter (the model cited lines it was never shown)
- ucr            (uncited + invalid-cited) / claim-bearing
- validity       share of extracted fields whose first answer was schema-valid

Usage
-----
  python3 evaluation/rq2/run.py

=============================================================================
Output shapes:

out/results.csv columns:
  batch, record, pipeline, field, value, claim_bearing, citations, dropped,
  coerced, supported

out/scores.json:
  p2 / p3 -> overall and per batch ->
    fields, claim_bearing, supported, uncited, invalid_cited, ucr,
    coerced, validity, not_complete
  criteria:
    ucr_p2_lt_p3 (the pre-committed grounding criterion)
    validity_ge_95 per pipeline
"""

import json
import sys
from pathlib import Path

# The shared helper package lives one directory up
sys.path.append(str(Path(__file__).parent.parent))
from helper import files

# The store the one cycle fills, read-only here
PREDICTIONS = Path(__file__).parent.parent.joinpath("out", "predictions", "v1")
OUT = Path(__file__).parent.joinpath("out")

PIPELINES = ("p2", "p3")
VARIANTS = ("text", "oracle")

# Values that assert nothing; a field carrying one makes no claim to support
NO_CLAIM = ("unknown", "none", "")


# The file name is <batch>__<record>__<variant>__<pipeline>, record ids never
# contain a double underscore, the other segments never contain any
def parse_name(path):
  batch, rest = path.stem.split("__", 1)
  record_id, variant, pipeline = rest.rsplit("__", 2)

  return batch, record_id, variant, pipeline


# Per record x field evidence. Only complete predictions count, the rest are
# tallied as not_complete. A p2/p3 file without the evidence keys is a broken
# store and stops the run
def evidence(paths):
  rows = []
  tallies = {}
  for path in paths:
    batch, record_id, variant, pipeline = parse_name(path)
    if pipeline not in PIPELINES or variant not in VARIANTS:
      continue
    prediction = json.loads(path.read_text())

    if prediction["status"] != "complete":
      for scope in ((pipeline, "overall"), (pipeline, batch)):
        tally = tallies.setdefault(scope, blank_tally())
        tally["not_complete"] += 1
      continue

    if "citations" not in prediction:
      sys.exit(f"{path.name} was stored without evidence; delete it and re-run evaluation/run.py")

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


# Rates per tally plus the pre-committed criteria
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
  if not PREDICTIONS.exists():
    sys.exit(f"no predictions under {PREDICTIONS}; run evaluation/run.py first")

  rows, tallies = evidence(sorted(PREDICTIONS.glob("*.json")))
  summary = scores(tallies)

  files.write_csv(
    OUT.joinpath("results.csv"),
    ["batch", "record", "pipeline", "field", "value", "claim_bearing",
     "citations", "dropped", "coerced", "supported"],
    rows
  )
  files.write_json(OUT.joinpath("scores.json"), summary)
  print(f"rq2: {len(rows)} rows in {OUT.joinpath('results.csv')}")
  print(f"rq2: scores in {OUT.joinpath('scores.json')}")


if __name__ == "__main__":
  main()
