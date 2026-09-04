"""
The one evaluation cycle: every cell once, four research questions scored
=========================================================================

Runs every record x variant x pipeline x schema combination exactly once
against the live system and stores one self-contained prediction file per
cell. The four rq scorers only read this store, so nothing is ever uploaded
twice across research questions. Assumes dataprep has been run.

The plan (1,611 cells):
- abcd-text   186 records x text x p1, p2, p3 (v1)
- maia-text   101 records x text x p1, p2, p3 (v1)
- hvb-audio   50 calls x oracle,asr,mono,stereo x p1, p2, p3(v1)
- hvb-audio   50 calls x oracle x p1, p2, p3
              (v2, the rq4 banking_task field; p1 fails on its schema claim by design and that refusal is the result)

Stages:
1. seed     existing predictions are copied into the store when they are sufficient:
            p1 files from the old rq1 run (no evidence needed), p2/p3 files only when they already carry the evidence keys
2. gate     the services the missing cells need must answer, and core must serve every schema the missing cells use
3. collect  every missing cell runs once, one file per cell, skip-if-exists, interrupt safe
4. score    the four rq scorers run over the store, each writes its own out/results.csv and out/scores.json

Usage
-----
  python3 evaluation/run.py                 # the full cycle
  python3 evaluation/run.py --limit 5       # pilot, first 5 records per batch
  python3 evaluation/run.py --skip-scoring  # collect only

=============================================================================
The store, one file per cell:

out/predictions/<schema>/<batch>__<record>__<variant>__<pipeline>.json:
  status:            complete | failed | timeout | upload_failed
  api_id:            int (the interaction id in core)
  fields:            {field: predicted value}
  lines:             [{line_id, speaker, text}] core produced (rq3 reads these)
  citations:         {field: [line ids that survived the grounding filter]}
  dropped_citations: {field: [cited line ids the filter rejected]}
  coerced:           {field: bool (the first answer was off-schema)}
  config_version:    str
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import uuid
from pathlib import Path

# The shared helper package lives in this directory
sys.path.append(str(Path(__file__).parent))
from helper import api, datasets, files, services


# Reads are retried with backoff, one transient network error must not abort an hours-long run.
# Uploads are never retried this way, a lost POST response could create a duplicate interaction
def request_retry(method, url):
  for attempt in range(1, 6):
    try:
      return api.request(method, url)
    except (urllib.error.URLError, OSError, TimeoutError):
      if attempt == 5:
        raise
      time.sleep(5 * attempt)

OUT = Path(__file__).parent.joinpath("out", "predictions")
RQ_SCORERS = ("rq1", "rq2", "rq3", "rq4")

# Old prediction stores, read-only seed sources
RQ1_OLD = Path(__file__).parent.joinpath("rq1", "out", "predictions")
RQ2_OLD = Path(__file__).parent.joinpath("rq2", "out", "predictions")

# The whole matrix, every cell runs exactly once
PLAN = (
  ("abcd-text", ("text",), ("p1", "p2", "p3"), "v1"),
  ("maia-text", ("text",), ("p1", "p2", "p3"), "v1"),
  ("hvb-audio", ("oracle", "asr", "mono", "stereo"), ("p1", "p2", "p3"), "v1"),
  ("hvb-audio", ("oracle",), ("p1", "p2", "p3"), "v2"),
)

# What a fresh cell needs up, by variant
TEXT_SERVICES = ("core", "baseline", "embeddings", "ollama")
AUDIO_SERVICES = ("core", "baseline", "embeddings", "ollama", "whisper", "diarization")


def cell_path(schema, batch, record_id, variant, pipeline):
  return OUT.joinpath(schema, f"{batch}__{record_id}__{variant}__{pipeline}.json")


# Records with a gold entry, per batch. This drops the hvb asr variant record
# files, the asr variant is loaded separately when its cell runs
def prepare():
  all_records = {}
  for batch in {row[0] for row in PLAN}:
    records, gold = datasets.load_batch(batch)
    all_records[batch] = [record for record in records if record["interaction_id"] in gold]

  return all_records


# Stage 1: copy old predictions into the store where they are sufficient.
# Only complete files count, a seeded timeout would freeze that cell forever.
# p1 never cites; p2/p3 files count only when they already carry the evidence
# keys, a fields-only file would cripple rq2
def seed(all_records):
  seeded = 0
  for batch, variants, pipelines, schema in PLAN:
    if schema != "v1":
      continue
    for record in all_records[batch]:
      for variant in variants:
        if variant not in ("text", "oracle"):
          continue
        for pipeline in pipelines:
          target = cell_path(schema, batch, record["interaction_id"], variant, pipeline)
          if target.exists():
            continue
          old_name = f"{batch}__{record['interaction_id']}__{pipeline}.json"
          for source_dir in (RQ2_OLD, RQ1_OLD):
            source = source_dir.joinpath(old_name)
            if not source.exists():
              continue
            prediction = json.loads(source.read_text())
            if prediction.get("status") != "complete":
              continue
            if pipeline == "p1" or "citations" in prediction:
              files.write_json(target, prediction)
              seeded += 1
              break
  if seeded:
    print(f"seeded {seeded} cells from the old rq1/rq2 predictions")


# Every cell of the plan that is not in the store yet
def missing_cells(all_records, limit):
  missing = []
  for batch, variants, pipelines, schema in PLAN:
    for record in all_records[batch][:limit]:
      for variant in variants:
        for pipeline in pipelines:
          if not cell_path(schema, batch, record["interaction_id"], variant, pipeline).exists():
            missing.append((batch, record, variant, pipeline, schema))

  return missing


# Stage 2: the services the missing cells need must answer,
# and core must serve every schema the missing cells use
def gate(core, missing):
  needs_audio = any(variant in ("mono", "stereo") for _, _, variant, _, _ in missing)
  services.check_services(AUDIO_SERVICES if needs_audio else TEXT_SERVICES)

  served = {schema["id"] for schema in api.request("GET", f"{core}/schemas")}
  for schema in sorted({schema for _, _, _, _, schema in missing}):
    if schema not in served:
      sys.exit(f"schema {schema} is not served by core (served: {sorted(served)}); "
               f"add insight-core/schemas/{schema}.json and restart core")


# The upload for one cell:
# text variants send the record json with a suffixed interaction id, audio variants send the wav.
# The stereo wav has the agent on channel 0, mono needs diarisation and gets no channel fields
def build_upload(batch, record, variant, pipeline, schema):
  form = {"pipeline": pipeline, "schema": schema}

  if variant in ("text", "oracle", "asr"):
    if variant == "asr":
      asr_file = datasets.DATASETS.joinpath(batch, "records", f"{record['interaction_id']}.asr.json")
      payload = json.loads(asr_file.read_text())
    else:
      payload = dict(record)
    payload["interaction_id"] = (f"{record['interaction_id']}--{variant}--{pipeline}--"
                                 f"{schema}--{uuid.uuid4().hex[:8]}")
    return form, f"{record['interaction_id']}.json", json.dumps(payload).encode(), "application/json"

  wav = datasets.DATASETS.joinpath(batch, "audio", f"{record['interaction_id']}-{variant}.wav")
  if variant == "stereo":
    form["split_channels"] = "true"
    form["agent_channel"] = "0"
  return form, wav.name, wav.read_bytes(), "audio/wav"


# The evidence core kept per field: the surviving citations from the record,
# the coercion flag and the dropped citations from the extract:<field> steps
def evidence_of(core, api_id, record_data):
  steps = request_retry("GET", f"{core}/interactions/{api_id}/steps")
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


# One cell against the live system: upload, poll until the record leaves
# pending or the deadline passes, then store everything core produced.
# A failed upload is stored as its own status, never retried blindly
def predict(core, form, file_name, file_bytes, content_type, timeout):
  body, headers = api.multipart(form, file_name, file_bytes, content_type)
  try:
    created = api.request("POST", f"{core}/interactions", body, headers)
  except (urllib.error.URLError, OSError, TimeoutError) as error:
    return {"status": "upload_failed", "api_id": None, "fields": {}, "lines": [],
            "citations": {}, "dropped_citations": {}, "coerced": {},
            "config_version": None, "error": str(error)}

  deadline = time.time() + timeout
  while time.time() < deadline:
    data = request_retry("GET", f"{core}/interactions/{created['id']}")
    status = (data.get("record") or {}).get("status")
    if status in ("complete", "failed"):
      extra = evidence_of(core, created["id"], data["record"])
      return {
        "status": status,
        "api_id": created["id"],
        "fields": {f["name"]: f["value"] for f in data["record"].get("fields", [])},
        "lines": data.get("lines", []),
        "citations": extra["citations"],
        "dropped_citations": extra["dropped_citations"],
        "coerced": extra["coerced"],
        "config_version": data["record"].get("config_version"),
      }
    time.sleep(2)

  return {"status": "timeout", "api_id": created["id"], "fields": {}, "lines": [],
          "citations": {}, "dropped_citations": {}, "coerced": {}, "config_version": None}


# Stage 3: every missing cell runs once
def collect(core, missing, timeout):
  for index, (batch, record, variant, pipeline, schema) in enumerate(missing, 1):
    target = cell_path(schema, batch, record["interaction_id"], variant, pipeline)
    print(f"[{index}/{len(missing)}] {schema} {batch} {record['interaction_id']} "
          f"{variant} {pipeline} ...", flush=True)
    form, file_name, file_bytes, content_type = build_upload(batch, record, variant, pipeline, schema)
    files.write_json(target, predict(core, form, file_name, file_bytes, content_type, timeout))


# Stage 4: the four rq scorers, each reads the store and writes its own
# outputs. One failing scorer never blocks the others, they are independent
def score():
  failed = []
  for rq in RQ_SCORERS:
    scorer = Path(__file__).parent.joinpath(rq, "run.py")
    print(f"+ python3 {scorer}", flush=True)
    result = subprocess.run([sys.executable, str(scorer)])
    if result.returncode != 0:
      failed.append(rq)
  if failed:
    sys.exit(f"scorers failed: {', '.join(failed)}")


def main():
  parser = argparse.ArgumentParser(description="run every cell once, score all four rqs")
  parser.add_argument("--core", default=services.ENDPOINTS["core"])
  parser.add_argument("--timeout", type=int, default=900, help="seconds per cell")
  parser.add_argument("--limit", type=int, help="only the first n records per batch (pilot)")
  parser.add_argument("--skip-scoring", action="store_true", help="collect only")
  args = parser.parse_args()

  # The --core flag overrides the endpoints table, so the gate probes the
  # same core the uploads will use
  services.ENDPOINTS["core"] = args.core

  all_records = prepare()
  seed(all_records)

  missing = missing_cells(all_records, args.limit)
  if missing:
    print(f"{len(missing)} cells to run")
    gate(args.core, missing)
    collect(args.core, missing, args.timeout)
  else:
    print("every cell exists, nothing to run")

  if not args.skip_scoring:
    score()


if __name__ == "__main__":
  main()
