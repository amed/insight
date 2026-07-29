from pathlib import Path

import joblib
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# the artifact is produced by train.py at container start and loaded once
bundle = joblib.load(Path(__file__).parent / "model.joblib")


class Line(BaseModel):
  speaker: str
  text: str


class Request(BaseModel):
  lines: list[Line]


# all field values are predicted from the flattened conversation in one call. the schema
# claim (id and hash the artifact was trained for) rides along so core can refuse a mismatch.
@app.post("/extract")
def extract(req: Request):
  text = " ".join(f"{line.speaker}: {line.text}" for line in req.lines)
  matrix = bundle["vectorizer"].transform([text])
  fields = [
    {"name": name, "value": str(model.predict(matrix)[0])}
    for name, model in bundle["models"].items()
  ]
  return {
    "fields": fields,
    "model_version": bundle["version"],
    "schema": bundle["schema"],
    "schema_hash": bundle["schema_hash"],
  }
