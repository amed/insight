"""
Validates everything prepare.py produced
========================================

Read-only, prints one PASS/FAIL line per check and exits nonzero when anything fails.

Checked:
- every manifest is stamped for v1 and its hash matches the current v1.json
  (a stale hash means the schema changed after the build, rebuild required)
- every training label and gold value sits inside the v1 schema's value sets
- no training text appears in any test record (split discipline, exact text)
- the maia test batch is exactly the held-out dialogue ids
- batch shapes: record counts, turn shapes, gold coverage, speaker alignment
- hvb audio: one mono (1 channel) and one stereo (2 channels) wav per call
- no non-speech [markers] survive in any hvb text

Usage
-----
  python3 validate.py
"""

import json
import subprocess
import sys
from pathlib import Path

import schema

TRAINING = Path(__file__).parent.joinpath("out", "training")
TESTING = Path(__file__).parent.joinpath("out", "testing")

FIELDS = ("intent", "issue_type", "agent_action", "sentiment", "resolution_status")

failures = []


def check(name, ok, detail=""):
  print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))
  if not ok:
    failures.append(name)


def record_text(record):
  return " ".join(f"{t['speaker']}: {t['text']}" for t in record["turns"])


def load_batch(name):
  batch = TESTING.joinpath(name)
  records = [json.loads(path.read_text()) for path in sorted((batch.joinpath("records")).glob("*.json"))]
  gold = json.loads((batch.joinpath("gold.json")).read_text())
  return records, gold


def main():
  schema_hash, allowed = schema.load()
  check("schema v1 has the five trained fields", set(allowed) == set(FIELDS))

  # Every output must be stamped for v1 with the hash of the current v1.json
  manifests = [TRAINING.joinpath("manifest.json")] + [
    TESTING.joinpath(name, "manifest.json") for name in ("abcd-text", "maia-text", "hvb-audio")]
  for path in manifests:
    label = path.parent.name if path.parent != TRAINING else "training"
    if not path.exists():
      check(f"{label}: manifest stamped for v1", False, "manifest.json missing")
      continue
    manifest = json.loads(path.read_text())
    check(f"{label}: manifest stamped for v1",
          manifest.get("schema") == schema.NAME, str(manifest.get("schema")))
    check(f"{label}: schema hash is current",
          manifest.get("schema_hash") == schema_hash,
          f"built {manifest.get('schema_hash')}, current {schema_hash}")

  # Training files: labels inside the schema, no empty texts
  training_texts = set()
  for field in FIELDS:
    examples = json.loads((TRAINING.joinpath(f"{field}.json")).read_text())
    labels = {example["label"] for example in examples}
    check(f"training {field}: labels within schema", labels <= allowed[field],
          f"{len(examples)} examples, classes {sorted(labels)}")
    check(f"training {field}: no empty texts", all(example["text"].strip() for example in examples))
    training_texts.update(example["text"] for example in examples)

  # Batches: shapes and gold
  abcd_records, abcd_gold = load_batch("abcd-text")
  maia_records, maia_gold = load_batch("maia-text")
  hvb_records, hvb_gold = load_batch("hvb-audio")

  check("abcd-text: 186 records", len(abcd_records) == 186, str(len(abcd_records)))
  check("abcd-text: gold for every record",
        {r["interaction_id"] for r in abcd_records} == set(abcd_gold))
  for field in ("intent", "issue_type", "agent_action"):
    values = {g[field] for g in abcd_gold.values() if g[field] is not None}
    check(f"abcd-text: gold {field} within schema", values <= allowed[field],
          f"{sum(g[field] is not None for g in abcd_gold.values())}/186 labeled")

  holdout = set(json.loads((TRAINING.joinpath("maia_holdout.json")).read_text()))
  maia_ids = {r["interaction_id"] for r in maia_records}
  check("maia-text: records are exactly the holdout ids",
        maia_ids == {f"maia-{i}" for i in holdout}, f"{len(maia_ids)} records")
  for field in ("sentiment", "resolution_status"):
    values = {g[field] for g in maia_gold.values() if g[field] is not None}
    check(f"maia-text: gold {field} within schema", values <= allowed[field],
          f"{sum(g[field] is not None for g in maia_gold.values())}/{len(maia_gold)} labeled")

  oracle = [r for r in hvb_records if not r["interaction_id"].endswith(".asr")]
  asr = [r for r in hvb_records if r["interaction_id"].endswith(".asr")]
  check("hvb-audio: 50 oracle + 50 asr records",
        len(oracle) == 50 and len(asr) == 50, f"{len(oracle)}+{len(asr)}")
  check("hvb-audio: gold for every call", {r["interaction_id"] for r in oracle} == set(hvb_gold))
  intents = {g["intent"] for g in hvb_gold.values() if g["intent"] is not None}
  check("hvb-audio: gold intent within schema", intents <= allowed["intent"],
        f"{sum(g['intent'] is not None for g in hvb_gold.values())}/50 labeled")
  by_id = {r["interaction_id"]: r for r in oracle}
  check("hvb-audio: gold speakers align with oracle turns",
        all(g["speakers"] == [t["speaker"] for t in by_id[i]["turns"]]
            for i, g in hvb_gold.items()))
  check("hvb-audio: no [markers] left in any text",
        all("[" not in t["text"] for r in hvb_records for t in r["turns"]))

  # Every record everywhere: non-empty turns, known speakers
  everything = abcd_records + maia_records + hvb_records
  check("all records: at least one turn", all(r["turns"] for r in everything))
  check("all records: speakers are agent/customer",
        all(t["speaker"] in ("agent", "customer") for r in everything for t in r["turns"]))

  # Split discipline: no training text equals any test record text
  test_texts = {record_text(r) for r in everything}
  overlap = training_texts & test_texts
  check("split discipline: training and test texts disjoint", not overlap,
        f"{len(training_texts)} training vs {len(test_texts)} test texts")

  # Audio: one mono and one stereo wav per call, with the right channel counts
  audio = TESTING.joinpath("hvb-audio", "audio")
  for suffix, channels in (("mono", "1"), ("stereo", "2")):
    wavs = sorted(audio.glob(f"*-{suffix}.wav"))
    good = all(subprocess.run(
      ["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries",
       "stream=channels", "-of", "csv=p=0", str(wav)],
      capture_output=True, text=True).stdout.strip() == channels for wav in wavs)
    check(f"hvb-audio: 50 {suffix} wavs with {channels} channel(s)",
          len(wavs) == 50 and good, str(len(wavs)))

  if failures:
    sys.exit(f"\n{len(failures)} check(s) failed: {failures}")
  print("\nall checks passed")


main()
