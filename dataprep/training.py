"""
Writes the baseline training files into out/training/
=====================================================

Training sources per field:
- intent, issue_type, agent_action   abcd train split
- sentiment                          emowoz plus the maia train part
- resolution_status                  maia train part

Every label is checked against the pinned v1 schema before anything is written,
a label outside the schema aborts the build. Skipped when all outputs exist,
delete out/training to rebuild.

=============================================================================
What it produces:

out/training/<field>.json:
  - text:  str (customer: ... agent: ...)
    label: str (a v1 schema value)

out/training/maia_holdout.json:
  [dialogue ids reserved for testing, never trained]

out/training/manifest.json:
  schema, schema_hash, examples per field, maia_holdout count, created_utc
"""

import json
import sys
import time

import schema
from corpora import abcd, emowoz, maia

FIELDS = ("intent", "issue_type", "agent_action", "sentiment", "resolution_status")


def write_all(data, out):
  outputs = [out.joinpath(f"{field}.json") for field in FIELDS] + [
    out.joinpath("maia_holdout.json"), out.joinpath("manifest.json")]
  if all(path.exists() for path in outputs):
    print("training files exist, skipped (delete out/training to rebuild)")
    return
  out.mkdir(parents=True, exist_ok=True)

  schema_hash, allowed = schema.load()
  examples = abcd.training_examples(data)
  maia_examples, holdout = maia.training_examples(data)
  examples["sentiment"] = emowoz.training_examples(data) + maia_examples["sentiment"]
  examples["resolution_status"] = maia_examples["resolution_status"]

  # Every label must sit inside the pinned schema before anything is written
  for field in FIELDS:
    for example in examples[field]:
      if example["label"] not in allowed[field]:
        sys.exit(f"training label {field}={example['label']!r} is not a {schema.NAME} "
                 f"schema value, nothing written")

  for field in FIELDS:
    (out.joinpath(f"{field}.json")).write_text(json.dumps(examples[field], indent=1) + "\n")
    print(f"training/{field}.json ({len(examples[field])} examples)")
  (out.joinpath("maia_holdout.json")).write_text(json.dumps(holdout, indent=1) + "\n")
  print(f"training/maia_holdout.json ({len(holdout)} dialogues reserved for testing)")

  (out.joinpath("manifest.json")).write_text(json.dumps({
    "schema": schema.NAME,
    "schema_hash": schema_hash,
    "examples": {field: len(examples[field]) for field in FIELDS},
    "maia_holdout": len(holdout),
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  }, indent=2) + "\n")
  print(f"training/manifest.json (schema {schema.NAME}, hash {schema_hash})")
