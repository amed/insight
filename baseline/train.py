"""
Baseline classifier (P1)
==========================================

This moudle trains a simple text classification model.

- TF-IDF vectorizer over all provided conversations
- One logistic regression model per schema field
- Serializes the full training bundle into `model.joblib`

As baseline, the following are intentionally ignored:

- Evaluation (no train/test split)
- Uses default scikit-learn hyperparameters
- Reproducibility controls (no random seed)
- Dependency or environment tracking
- Relies on pickle-based serialization (unsafe for untrusted files)

Inputs
------
  fixtures/labels.json
  fixtures/<conversation>.json
  insight-core/schemas/v1.json
  (could be replaced with any other schema - pinned for now)

Each conversation is expected to follow:

  {
    "turns": [
      { "speaker": "customer", "text": "..." }
    ]
  }

Labels map each conversation file to schema-defined fields.


High Level Process
--------------------
1. Load schema
2. Extract allowed label values per field
3. Load labeled conversation dataset
4. Flatten each conversation
5. Validate labels against schema constraints
6. Convert text into TF-IDF feature vectors
7. Train one LogisticRegression model per schema field
8. Serialize all artifacts into `model.joblib`

Output
------
  {
    "models": { "field": LogisticRegression },
    "vectorizer": TfidfVectorizer,
    "schema": "v1",
    "schema_hash": "...",
    "version": "tfidf-logreg|..."
  }

Sources
----------
TF-IDF feature extraction:
  https://scikit-learn.org/stable/modules/feature_extraction.html#text-feature-extraction

Logistic Regression:
  https://scikit-learn.org/stable/modules/linear_model.html#logistic-regression

Joblib serialization (pickle-based, unsafe for untrusted inputs):
  https://joblib.readthedocs.io/en/latest/
"""

import hashlib
import json
import os
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# The schema file is the single source of truth:
# fields and allowed values come from it, artifact carries its id and hash so core
# can refuse predictions against any other schema. (v1 is pinned for now)
SCHEMAS_DIR = Path(os.environ.get("SCHEMAS_DIR", Path(__file__).parent.parent / "insight-core" / "schemas"))
SCHEMA_ID = os.environ.get("BASELINE_SCHEMA", "v1")

FIXTURES = Path(__file__).parent / "fixtures"
ARTIFACT = Path(__file__).parent / "model.joblib"


# a conversation is flattened to one text, the same joining used at inference
def conversation_text(turns):
  return " ".join(f"{turn['speaker']}: {turn['text']}" for turn in turns)


# one shared tf-idf vectorizer is fitted over the fixture conversations
# plus one logistic regression per schema field
# every label must belong to the schema's values, so a p1
# prediction can never fall outside the schema it claims. (The case need manual attention)
def main():
  raw_schema = (SCHEMAS_DIR / f"{SCHEMA_ID}.json").read_bytes()
  schema = json.loads(raw_schema)
  schema_hash = hashlib.sha256(raw_schema).hexdigest()[:14]
  allowed = {field["name"]: set(field["values"]) | {"unknown"} for field in schema["fields"]}

  labels = json.loads((FIXTURES / "labels.json").read_text())
  digest = hashlib.sha256((FIXTURES / "labels.json").read_bytes())

  texts = []
  targets = {name: [] for name in allowed}
  for name in sorted(labels):
    raw = (FIXTURES / f"{name}.json").read_bytes()
    digest.update(raw)
    data = json.loads(raw)
    texts.append(conversation_text(data["turns"]))
    for field, values in allowed.items():
      value = labels[name].get(field)
      if value is None:
        sys.exit(f"{name}: label for {field} is missing, training aborted")
      if value not in values:
        sys.exit(f"{name}: label {field}={value} is not in the schema values, training aborted")
      targets[field].append(value)

  vectorizer = TfidfVectorizer()
  matrix = vectorizer.fit_transform(texts)

  models = {}
  for field in allowed:
    if len(set(targets[field])) < 2:
      sys.exit(f"field {field} has a single class in the fixture labels, training aborted")
    models[field] = LogisticRegression(max_iter=1000).fit(matrix, targets[field])

  version = f"tfidf-logreg|{digest.hexdigest()[:14]}"
  joblib.dump(
    {
      "models": models,
      "version": version,
      "vectorizer": vectorizer,
      "schema": SCHEMA_ID,
      "schema_hash": schema_hash,
    },
    ARTIFACT,
  )
  print(f"trained on {len(texts)} conversations for {SCHEMA_ID} - version {version}")


main()
