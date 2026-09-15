"""
Baseline classifier (P1): train from the prepared data
======================================================

Fits one classifier per v1 schema field from the files dataprep produced:
- one shared tf-idf vectorizer over every training text
- one logistic regression per field, balanced class weights
  (macro-f1 is the evaluation metric and the sentiment labels skew positive)

Run dataprep/prepare.py first, how each label is derived is documented there.
The prepared data carries the schema it was built for and the artifact carries
the v1 schema claim (name + content hash). A schema change is refused until the
data is rebuilt, an existing artifact retrains automatically when its claim no
longer matches the current schema, and core fails any p1 record whose claim
does not match the record's schema stamp.

Usage
-----
  python3 train.py

Sources
-------
TF-IDF and logistic regression: https://scikit-learn.org/stable/modules/feature_extraction.html
Joblib serialization (pickle-based, unsafe for untrusted files): https://joblib.readthedocs.io

=============================================================================
Data in/out:

In (dataprep/out/training/, mounted as /app/data in docker):
  <field>.json:  [{text, label}] per schema field
  manifest.json: schema, schema_hash, example counts

Out (model.joblib):
  models:      {field: LogisticRegression}
  vectorizer:  the shared tf-idf vectorizer
  version:     "tfidf-logreg|<sha256[:14] of the training files>"
  schema:      "v1"
  schema_hash: sha256[:14] of v1.json, the claim core checks per record
"""

import hashlib
import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

ARTIFACT = Path(__file__).parent.joinpath("model.joblib")

# Prepared training data and the pinned v1 schema are read from the repo locally,
# and from the read-only mounts in docker.
DATA = Path(__file__).parent.parent.joinpath("dataprep", "out", "training")
if not DATA.exists():
  DATA = Path("/app/data")
SCHEMA_FILE = Path(__file__).parent.parent.joinpath("insight-core", "schemas", "v1.json")
if not SCHEMA_FILE.exists():
  SCHEMA_FILE = Path("/schemas/v1.json")

TRAINED_FIELDS = ("intent", "issue_type", "sentiment", "resolution_status", "agent_action")


def train(raw_schema, schema):
  allowed = {field["name"]: set(field["values"]) for field in schema["fields"]}
  if set(allowed) != set(TRAINED_FIELDS):
    sys.exit(f"schema fields {sorted(allowed)} do not match trained fields {sorted(TRAINED_FIELDS)}")

  # The prepared data carries the schema it was built for.
  # A mismatch means the schema changed after preparation and the data must be rebuilt first.
  schema_hash = hashlib.sha256(raw_schema).hexdigest()[:14]
  manifest_file = DATA.joinpath("manifest.json")
  if not manifest_file.exists():
    sys.exit(f"{manifest_file} not found; run dataprep/prepare.py first")
  manifest = json.loads(manifest_file.read_text())
  if manifest.get("schema") != schema["name"] or manifest.get("schema_hash") != schema_hash:
    sys.exit(f"training data was prepared for schema "
             f"{manifest.get('schema')}|{manifest.get('schema_hash')}, the current schema is "
             f"{schema['name']}|{schema_hash}; re-run dataprep/prepare.py")

  digest = hashlib.sha256()
  fields = {}
  for field in TRAINED_FIELDS:
    path = DATA.joinpath(f"{field}.json")
    if not path.exists():
      sys.exit(f"{path} not found; run dataprep/prepare.py first")
    raw = path.read_bytes()
    digest.update(raw)
    fields[field] = json.loads(raw)

  # One shared vectorizer over every training text, then one classifier per field.
  # Balanced class weights because macro-f1 is the evaluation metric,
  # and the emowoz sentiment labels are heavily skewed toward positive.
  texts = sorted({example["text"] for examples in fields.values() for example in examples})
  row_of = {text: i for i, text in enumerate(texts)}
  vectorizer = TfidfVectorizer()
  matrix = vectorizer.fit_transform(texts)

  models = {}
  for field, examples in fields.items():
    for example in examples:
      if example["label"] not in allowed[field]:
        sys.exit(f"label {field}={example['label']} is not in the schema values, training aborted")
    if len({example["label"] for example in examples}) < 2:
      sys.exit(f"field {field} has a single class, training aborted")
    rows = [row_of[example["text"]] for example in examples]
    models[field] = LogisticRegression(max_iter=1000, class_weight="balanced").fit(
      matrix[rows], [example["label"] for example in examples])
    print(f"trained {field} ({len(examples)} examples)")

  version = f"tfidf-logreg|{digest.hexdigest()[:14]}"
  joblib.dump({
    "models": models,
    "vectorizer": vectorizer,
    "version": version,
    "schema": schema["name"],
    "schema_hash": schema_hash,
  }, ARTIFACT)
  print(f"saved model.joblib, version {version}")


def main():
  if not SCHEMA_FILE.exists():
    sys.exit("schema v1.json not found (looked in insight-core/schemas and /schemas)")
  raw_schema = SCHEMA_FILE.read_bytes()
  schema_hash = hashlib.sha256(raw_schema).hexdigest()[:14]

  # An existing artifact is reused only while its claim matches the current schema.
  if ARTIFACT.exists():
    if joblib.load(ARTIFACT).get("schema_hash") == schema_hash:
      print(f"model exists at {ARTIFACT} and matches the schema, training skipped")
      return
    print("schema changed since the model was trained, retraining ...")

  train(raw_schema, json.loads(raw_schema))


main()
