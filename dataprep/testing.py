"""
Writes the test batches into out/testing/
=========================================

The batches, each fed by one corpus module:
- abcd-text   186 text records, gold: intent, issue_type, agent_action
- maia-text   101 holdout records, gold: sentiment, resolution_status
- hvb-audio   50 calls, oracle + asr text records, mono + stereo wavs,
              gold: intent, speakers

Every non-null gold value on a schema field is checked against the pinned v1
schema before anything is written, and every manifest is stamped with the v1
name and content hash. A batch with an existing manifest.json is skipped,
delete the batch directory to rebuild it.

=============================================================================
What each batch contains:

out/testing/<batch>/records/<id>.json:
  interaction_id: str
  turns:
    - speaker: agent | customer
      text:    str

out/testing/<batch>/gold.json:
  record id -> gold fields (null = field excluded for that record)

out/testing/<batch>/manifest.json:
  schema, schema_hash, batch counts, mapping coverage, created_utc

out/testing/hvb-audio/audio/:
  hvb-<id>-mono.wav, hvb-<id>-stereo.wav
"""

import json
import sys
import time

import schema
from corpora import abcd, hvb, maia


# Gold is checked against the pinned schema, then records, gold, and the
# v1-stamped manifest are written
def write_batch(out, name, records, gold, manifest, schema_hash, allowed):
  for record_id, fields in gold.items():
    for field, value in fields.items():
      if field in allowed and value is not None and value not in allowed[field]:
        sys.exit(f"{name}: gold {field}={value!r} for {record_id} is not a "
                 f"{schema.NAME} schema value, nothing written")

  batch = out.joinpath(name)
  (batch.joinpath("records")).mkdir(parents=True, exist_ok=True)
  for record in records:
    (batch.joinpath("records", f"{record['interaction_id']}.json")).write_text(
      json.dumps(record, indent=2) + "\n")
  (batch.joinpath("gold.json")).write_text(json.dumps(gold, indent=2) + "\n")
  manifest = {"schema": schema.NAME, "schema_hash": schema_hash, **manifest}
  manifest["created_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
  (batch.joinpath("manifest.json")).write_text(json.dumps(manifest, indent=2) + "\n")


def write_abcd(data, out, schema_hash, allowed):
  entries = abcd.test_records(data)
  records = [record for _, record, _ in entries]
  gold = {record_id: g for record_id, _, g in entries}
  write_batch(out, "abcd-text", records, gold, {
    "batch": "abcd-text",
    "source": "abcd_v1.1 test split",
    "records": len(records),
    "gold_fields": ["intent", "issue_type", "agent_action"],
    "unmapped_intent": sum(1 for g in gold.values() if g["intent"] is None),
    "mapping_file": "corpora/abcd_mapping.json",
  }, schema_hash, allowed)
  print(f"testing/abcd-text ({len(records)} records)")


def write_maia(data, out, schema_hash, allowed):
  entries = maia.test_records(data)
  records = [record for _, record, _ in entries]
  gold = {record_id: g for record_id, _, g in entries}
  write_batch(out, "maia-text", records, gold, {
    "batch": "maia-text",
    "source": "maia-dqe holdout (every fifth deduplicated dialogue)",
    "records": len(records),
    "gold_fields": ["sentiment", "resolution_status"],
    "unlabeled_sentiment": sum(1 for g in gold.values() if g["sentiment"] is None),
    "unlabeled_resolution": sum(1 for g in gold.values() if g["resolution_status"] is None),
    "license_note": "cc by-nd 4.0, do not redistribute these records",
    "text_note": "customer side is machine-translated english",
  }, schema_hash, allowed)
  print(f"testing/maia-text ({len(records)} records)")


def write_hvb(data, out, schema_hash, allowed):
  entries = hvb.test_records(data)
  batch = out.joinpath("hvb-audio")
  (batch.joinpath("audio")).mkdir(parents=True, exist_ok=True)

  records = []
  gold = {}
  for record_id, call_id, oracle, asr, g in entries:
    records.append({"interaction_id": record_id, "turns": oracle})
    records.append({"interaction_id": f"{record_id}.asr", "turns": asr})
    gold[record_id] = g
    hvb.build_audio(data, call_id, batch.joinpath("audio"))

  write_batch(out, "hvb-audio", records, gold, {
    "batch": "hvb-audio",
    "source": "gridspace-stanford-harper-valley",
    "calls": len(entries),
    "variants": ["oracle", "asr", "mono", "stereo"],
    "gold_fields": ["intent", "speakers"],
    "unmapped_intent": sum(1 for g in gold.values() if g["intent"] is None),
    "mapping_file": "corpora/hvb_mapping.json",
  }, schema_hash, allowed)
  print(f"testing/hvb-audio ({len(entries)} calls, {2 * len(entries)} text records, "
        f"{2 * len(entries)} wavs)")


def write_all(data, out):
  schema_hash, allowed = schema.load()
  for name, writer in (("abcd-text", write_abcd), ("maia-text", write_maia),
                       ("hvb-audio", write_hvb)):
    if (out.joinpath(name, "manifest.json")).exists():
      print(f"testing/{name} exists, skipped (delete the directory to rebuild)")
    else:
      writer(data, out, schema_hash, allowed)
