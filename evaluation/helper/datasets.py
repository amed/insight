"""
Batches and the pinned schema
=============================

load_batch returns the records and gold of one dataprep batch, and refuses a
batch that is missing, not stamped for v1, or built against an older revision
of v1.json. schema_values returns the allowed values per field.

=============================================================================
Data shapes:

record (dataprep test record, the api upload shape):
  interaction_id: str
  turns: [{speaker, text}]

gold (dataprep gold.json):
  record id -> {field: value | null, ...}
"""

import hashlib
import json
import sys
from pathlib import Path

SCHEMA_FILE = Path(__file__).parent.parent.parent.joinpath("insight-core", "schemas", "v1.json")
DATASETS = Path(__file__).parent.parent.parent.joinpath("dataprep", "out", "testing")


# Field -> list of allowed values, from the pinned v1 schema
def schema_values():
  schema = json.loads(SCHEMA_FILE.read_text())

  return {field["name"]: field["values"] for field in schema["fields"]}


# Records and gold of one dataprep batch. A batch that is missing, not stamped
# for v1, or built against an older revision of v1.json is refused
def load_batch(name):
  batch = DATASETS.joinpath(name)
  if not batch.joinpath("manifest.json").exists():
    sys.exit(f"batch {name} is not built under {DATASETS}; run dataprep/prepare.py first")
  manifest = json.loads(batch.joinpath("manifest.json").read_text())
  if manifest.get("schema") != "v1":
    sys.exit(f"batch {name} is stamped for schema {manifest.get('schema')!r}, expected v1")
  current_hash = hashlib.sha256(SCHEMA_FILE.read_bytes()).hexdigest()[:14]
  if manifest.get("schema_hash") != current_hash:
    sys.exit(f"batch {name} was built for v1 hash {manifest.get('schema_hash')}, the current "
             f"v1.json is {current_hash}; re-run dataprep/prepare.py")

  records = [json.loads(path.read_text())
             for path in sorted(batch.joinpath("records").glob("*.json"))]
  gold = json.loads(batch.joinpath("gold.json").read_text())

  return records, gold
