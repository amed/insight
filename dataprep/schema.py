"""
The pinned reference schema: v1
===============================

Everything this module builds is bound to schema v1.
Mappings must be stamped for it,
every training label and gold value is checked against its value sets before a file is written,
and every output manifest carries its name and content hash.
The hash is computed exactly as core's registry computes it so the chain
mapping -> prepared data -> trained artifact -> stored record is one identity.
"""

import hashlib
import json
import sys
from pathlib import Path

NAME = "v1"
FILE = Path(__file__).parent.parent.joinpath("insight-core", "schemas", f"{NAME}.json")


# returns (hash, {field: set of allowed values})
def load():
  if not FILE.exists():
    sys.exit(f"{FILE} not found; dataprep is bound to schema {NAME}")

  raw = FILE.read_bytes()
  schema = json.loads(raw)

  if schema.get("name") != NAME:
    sys.exit(f"{FILE} declares name {schema.get('name')!r}, expected {NAME!r}")
  values = {field["name"]: set(field["values"]) for field in schema["fields"]}

  return hashlib.sha256(raw).hexdigest()[:14], values
