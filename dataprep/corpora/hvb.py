"""
HarperValleyBank: spoken bank calls with per-party audio and transcripts
========================================================================

Provides the audio test batch, four variants per call, testing only, no training:
- oracle   text record from the human-corrected transcript
- asr      text record from the dataset's machine transcript
- mono     wav, both parties mixed into one channel, diarisation must infer speakers
- stereo   wav, agent on channel 0, caller on channel 1, roles known by channel

Speaker roles per line come with the corpus, so role accuracy has ground truth by construction.
Gold intent comes from the call's task via the reviewed mapping file hvb_mapping.json
(null = the schema has no value for it, intent is excluded there).
The raw task in intent_source doubles as the banking_task gold for the schema v2 test (RQ4).
Non-speech markers like [noise] are stripped from all text, they are not words and would
inflate wer against the asr output.

Source:
https://github.com/cricketclub/gridspace-stanford-harper-valley (CC BY 4.0)

=============================================================================
Data schema before/after preparation:

Before:
one HVB call (three files per call inside the cloned repository)

data/transcript/<id>.json:
  - speaker_role:     str (agent | caller)
    start_ms:         int (segment start, sort key)
    human_transcript: str (corrected text, may contain [noise] markers)
    transcript:       str (machine text)
data/metadata/<id>.json:
  ... nested, the task sits at agent.responses[].data.task_type ...
data/audio/agent/<id>.wav, data/audio/caller/<id>.wav (per-party recordings)

After:
dataprep outputs

test records (out/testing/hvb-audio/records/):
  hvb-<id>.json      {interaction_id, turns} from the human transcript
  hvb-<id>.asr.json  {interaction_id, turns} from the machine transcript
  turns:
    - speaker: agent | customer
      text:    str (markers stripped)

audio (out/testing/hvb-audio/audio/):
  hvb-<id>-mono.wav   (1 channel, both parties mixed)
  hvb-<id>-stereo.wav (2 channels, agent = channel 0)

gold (out/testing/hvb-audio/gold.json):
  "hvb-<id>":
    intent:        str | null (null = task outside the schema, 4 of 8 tasks)
    intent_source: str (the raw task, also the banking_task gold for v2)
    speakers:      [agent | customer] (one per oracle turn, for role scoring)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

CLONE_DIR = "harper-valley-bank"
CLONE_URL = "https://github.com/cricketclub/gridspace-stanford-harper-valley"

MAPPING_FILE = Path(__file__).parent.joinpath("hvb_mapping.json")

ROLE = {"agent": "agent", "caller": "customer"}
MARKERS = re.compile(r"\[[^\]]*\]")


# Same contract as the abcd mapping: a missing file gets a template with every
# task found in the corpus and the run stops for review, a malformed file fails
# with a clear message instead of a KeyError
def load_mapping(tasks):
  if not MAPPING_FILE.exists():
    template = {
      "schema": "v1",
      "_note": "null means unmapped: intent is excluded from scoring for that record. review before building.",
      "task_to_intent": {task: None for task in sorted(tasks)},
    }
    MAPPING_FILE.write_text(json.dumps(template, indent=2) + "\n")
    sys.exit(f"{MAPPING_FILE.name} was missing; a template was written, review it and run again")
  mapping = json.loads(MAPPING_FILE.read_text())
  if mapping.get("schema") != "v1":
    sys.exit(f"{MAPPING_FILE.name} is stamped for schema {mapping.get('schema')!r}, "
             f"this module builds data for v1 only")
  if "task_to_intent" not in mapping:
    sys.exit(f"{MAPPING_FILE.name} is missing 'task_to_intent'; fix the file, or delete it to regenerate the template")

  return mapping["task_to_intent"]


# Segments are sorted by start time, markers stripped, marker-only segments dropped
def turns(segments, text_key):
  result = []
  for segment in sorted(segments, key=lambda s: s.get("start_ms", 0)):
    text = MARKERS.sub(" ", str(segment.get(text_key, "")))
    text = re.sub(r"\s+", " ", text).strip()
    role = ROLE.get(segment.get("speaker_role"))
    if text and role:
      result.append({"speaker": role, "text": text})

  return result


# The task is the intent source. Metadata nesting is looked up tolerantly and
# the preparation fails naming the call when no task is found
def task_of(metadata, call_id):
  queue = [metadata]
  while queue:
    node = queue.pop(0)
    if isinstance(node, dict):
      for key, value in node.items():
        if key in ("task", "task_type", "tasks") and value:
          first = value[0] if isinstance(value, list) else value
          if isinstance(first, dict):
            first = first.get("task_type") or first.get("name") or first.get("task")
          if first:
            return str(first)
        queue.append(value)
    elif isinstance(node, list):
      queue.extend(node)

  sys.exit(f"call {call_id}: no task found in metadata")


# Every call in the corpus with its task, sorted by id
def all_calls(data):
  source = data.joinpath(CLONE_DIR, "data")
  calls = []
  for path in sorted((source.joinpath("transcript")).glob("*.json")):
    metadata = json.loads((source.joinpath("metadata", f"{path.stem}.json")).read_text())
    calls.append((path.stem, task_of(metadata, path.stem)))
  if not calls:
    sys.exit(f"no transcripts found under {source.joinpath('transcript')}")

  return calls


# Deterministic task-stratified selection: round-robin over tasks, sorted ids
def select_calls(calls, count):
  by_task = {}
  for call_id, task in calls:
    by_task.setdefault(task, []).append(call_id)

  selected = []
  rank = 0
  while len(selected) < min(count, len(calls)):
    added = False
    for task in sorted(by_task):
      if rank < len(by_task[task]) and len(selected) < count:
        selected.append((by_task[task][rank], task))
        added = True
    if not added:
      break
    rank += 1

  return selected


# Agent is the left ffmpeg input, caller the right. amix folds both into one
# channel, amerge keeps them apart as channels 0 and 1
def build_audio(data, call_id, out_dir):
  source = data.joinpath(CLONE_DIR, "data", "audio")
  agent_wav = source.joinpath("agent", f"{call_id}.wav")
  caller_wav = source.joinpath("caller", f"{call_id}.wav")
  if not agent_wav.exists() or not caller_wav.exists():
    sys.exit(f"call {call_id}: per-party wav missing under {source}")
  merge = ["ffmpeg", "-y", "-i", str(agent_wav), "-i", str(caller_wav)]
  subprocess.run(merge + ["-filter_complex", "[0][1]amix=inputs=2", "-ac", "1",
                          str(out_dir.joinpath(f"hvb-{call_id}-mono.wav"))],
                 capture_output=True, check=True)
  subprocess.run(merge + ["-filter_complex", "[0][1]amerge=inputs=2", "-ac", "2",
                          str(out_dir.joinpath(f"hvb-{call_id}-stereo.wav"))],
                 capture_output=True, check=True)


# One entry per call: the two text variant records, gold, and the call id for audio
def test_records(data, count=50):
  source = data.joinpath(CLONE_DIR, "data")
  calls = all_calls(data)
  to_intent = load_mapping({task for _, task in calls})
  records = []
  for call_id, task in select_calls(calls, count):
    segments = json.loads((source.joinpath("transcript", f"{call_id}.json")).read_text())
    record_id = f"hvb-{call_id}"
    oracle = turns(segments, "human_transcript")
    asr = turns(segments, "transcript")
    gold = {
      "intent": to_intent[task],
      "intent_source": task,
      "speakers": [t["speaker"] for t in oracle],
    }
    records.append((record_id, call_id, oracle, asr, gold))

  return records
