"""
MAIA-DQE: genuine customer support conversations with human annotations
=======================================================================

Provides training examples for:
- sentiment
- resolution_status

from the train part, and test records with gold for the same two fields from the holdout part.
The corpus ships as five overlapping files (43 duplicated dialogues), so dialogues are
deduplicated by id first (544 released, 501 unique), sorted, and every fifth one is held out
for testing, the rest train. The same split code produces both sides, so they can never overlap.

The sentiment label is the customer's last non-neutral sentence emotion mapped to polarity.
The resolution_status label comes from the human outcome judgements: dropped conversations are
unresolved, task success 4-5 resolved, 1-2 unresolved, 3 ambiguous and unlabelled.
The customer side is machine-translated english (text_mt), stated as a limitation wherever
results are reported.

Source:
https://github.com/johndmendonca/MAIA-DQE (CC BY-ND 4.0)
PS: Converted records must stay out of any public repository

=============================================================================
Data schema before/after preparation:

Before:
one MAIA dialogue (maia-*.json, five files, each a list of dialogues)

dialogue:
  id:    str (e.g. "en_pt-br_#CLIENT-04#_2021-01-03-1")
  turns:
    - text_mt:  [str] (sentences, machine-translated english)
      text_src: [str] (sentences, original german/portuguese)
      floor:    str (inbound = customer, outbound = agent)
      Emotion:  [int] (per sentence, 0-7 in the paper's taxonomy order: happiness,
                empathy, neutral, disappointment, confusion, frustration, anger,
                anxiety; only customer sentences are annotated)
  dialog:
    Dropped conversation: 0 | 1
    Task Sucess:          1-5 (typo is in the data)

After:
dataprep outputs

training example (out/training/sentiment.json, out/training/resolution_status.json):
  - text:  str (customer: ... agent: ...)
    label: str (sentiment: positive | neutral | negative,
                resolution_status: resolved | unresolved)

holdout (out/training/maia_holdout.json):
  [dialogue ids reserved for testing, never trained]

test record (out/testing/maia-text/records/maia-<id>.json):
  interaction_id: str
  turns:
    - speaker: agent | customer
      text:    str

gold (out/testing/maia-text/gold.json):
  "maia-<id>":
    sentiment:         str | null (null = no annotated customer sentence)
    resolution_status: str | null (null = ambiguous task success 3)
"""

import json

FILES = {
  "maia-de_client_01.json": "https://raw.githubusercontent.com/johndmendonca/MAIA-DQE/main/data/de_client_01.json",
  "maia-de_client_02.json": "https://raw.githubusercontent.com/johndmendonca/MAIA-DQE/main/data/de_client_02.json",
  "maia-pt_br_client_02.json": "https://raw.githubusercontent.com/johndmendonca/MAIA-DQE/main/data/pt_br_client_02.json",
  "maia-pt_br_client_04.json": "https://raw.githubusercontent.com/johndmendonca/MAIA-DQE/main/data/pt_br_client_04.json",
  "maia-pt_pt_client_03.json": "https://raw.githubusercontent.com/johndmendonca/MAIA-DQE/main/data/pt_pt_client_03.json",
}

# Emotion ints mapped to sentiment. Empathy stays neutral because a polite
# "i understand" is not satisfaction, all five distress emotions are negative
SENTIMENT = {
  0: "positive",   # happiness
  1: "neutral",    # empathy
  2: "neutral",    # neutral
  3: "negative",   # disappointment
  4: "negative",   # confusion
  5: "negative",   # frustration
  6: "negative",   # anger
  7: "negative",   # anxiety
}


# Dialogues are deduplicated by id, first occurrence in file order wins, then sorted by id
def load(data):
  by_id = {}
  for name in FILES:
    for dialogue in json.loads((data.joinpath(name)).read_text()):
      if dialogue["id"] not in by_id:
        by_id[dialogue["id"]] = dialogue

  return [by_id[key] for key in sorted(by_id)]


# Every fifth dialogue is held out for testing, the rest train
def split(dialogues):
  holdout = [d for i, d in enumerate(dialogues) if i % 5 == 0]
  trainable = [d for i, d in enumerate(dialogues) if i % 5 != 0]

  return trainable, holdout


# A turn is a list of sentences, inbound is the customer, outbound the agent
def turns(dialogue):
  result = []
  for turn in dialogue["turns"]:
    speaker = "customer" if turn["floor"] == "inbound" else "agent"
    sentence_text = " ".join(turn["text_mt"]).strip()
    if sentence_text:
      result.append({"speaker": speaker, "text": sentence_text})

  return result


def text(dialogue):
  return " ".join(f"{t['speaker']}: {t['text']}" for t in turns(dialogue))


# The customer's last non-neutral sentence emotion, neutral when only neutral
# annotations exist, None when no customer sentence is annotated
def sentiment_of(dialogue):
  label = None
  for turn in dialogue["turns"]:
    if turn["floor"] != "inbound":
      continue
    for emotion in turn.get("Emotion") or []:
      sentiment = SENTIMENT.get(emotion)
      if sentiment is None:
        continue
      if label is None or sentiment != "neutral":
        label = sentiment

  return label


# Dropped conversations ended without a conclusion. Task success is a human
# 1-5 score, 3 is ambiguous (partial success) and gives no label
def resolution_of(dialogue):
  annotations = dialogue.get("dialog") or {}
  if annotations.get("Dropped conversation") == 1:
    return "unresolved"
  success = annotations.get("Task Sucess")
  if success in (4, 5):
    return "resolved"
  if success in (1, 2):
    return "unresolved"

  return None


def gold_of(dialogue):
  return {
    "sentiment": sentiment_of(dialogue),
    "resolution_status": resolution_of(dialogue),
  }


def training_examples(data):
  trainable, holdout = split(load(data))
  examples = {"sentiment": [], "resolution_status": []}
  for dialogue in trainable:
    dialogue_text = text(dialogue)
    gold = gold_of(dialogue)
    if gold["sentiment"]:
      examples["sentiment"].append({"text": dialogue_text, "label": gold["sentiment"]})
    if gold["resolution_status"]:
      examples["resolution_status"].append({"text": dialogue_text, "label": gold["resolution_status"]})

  return examples, [d["id"] for d in holdout]


def test_records(data):
  records = []
  for dialogue in split(load(data))[1]:
    record_id = f"maia-{dialogue['id']}"
    record = {"interaction_id": record_id, "turns": turns(dialogue)}
    records.append((record_id, record, gold_of(dialogue)))

  return records
