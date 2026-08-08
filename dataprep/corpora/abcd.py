"""
ABCD: retail customer service dialogues with flow/subflow/action annotations
============================================================================

Provides training examples for:
- intent
- issue_type
- agent_action

from the train split, and test records with gold for the same three fields from the test split.
The splits ship with the corpus, so training and testing can never share a conversation.

The subflow -> intent and flow -> issue_type decisions live in the reviewed mapping file abcd_mapping.json
(null = the schema has no value for it, the field is excluded there)
The agent_action label is derived from the corpus's logged action buttons, grouped below.

Source: https://github.com/asappresearch/abcd (MIT)

=============================================================================
Data schema before/after preparation:

Before:
one ABCD conversation (abcd_v1.1.json, splits into train/dev/test)

conversation:
  convo_id:  int (unique identifier)
  scenario:
    flow:     str (1 of 10 categories)
    subflow:  str (1 of ~55 scenarios)
    personal: {...} (customer data)
    order:    {...} (purchase info)
    product:  {...} (item details)
  original:  [[speaker, utterance], ...] (speaker: agent | customer | action)
  delexed:
    - speaker:    str
      text:       str
      turn_count: int
      targets:    [intent, nextstep, action, values, utt_rank]
      candidates: [utterance ids]

After:
dataprep outputs

training example (out/training/<field>.json):
  - text:  str  (agent:... customer: ...)
    label: str (schema value via mapping / action rules)

test record (out/testing/abcd-text/records/abcd-<id>.json):
  interaction_id: str
  turns:
    - speaker: agent | customer
      text:    str

gold (out/testing/abcd-text/gold.json):
  "abcd-<convo_id>":
    intent:             str | null
    intent_source:      str
    issue_type:         str
    issue_type_source:  str
    agent_action:       str
"""

import gzip
import json
import sys
from pathlib import Path

FILES = {
  "abcd_v1.1.json.gz": "https://github.com/asappresearch/abcd/raw/master/data/abcd_v1.1.json.gz",
}

MAPPING_FILE = Path(__file__).parent.joinpath("abcd_mapping.json")


# The mapping is the project's reviewed taxonomy decision. A missing file gets a
# template with every subflow and flow found in the corpus, and the run stops so
# nothing is built on an unreviewed taxonomy. A malformed file fails with a clear
# message instead of a KeyError.
def load_mapping(corpus):
  if not MAPPING_FILE.exists():
    template = {
      "schema": "v1",
      "_note": "null means unmapped: the field is excluded from scoring for that record. review before building.",
      "subflow_to_intent": {s: None for s in sorted(
        {c["scenario"]["subflow"] for split in corpus.values() for c in split})},
      "flow_to_issue_type": {f: None for f in sorted(
        {c["scenario"]["flow"] for split in corpus.values() for c in split})},
    }
    MAPPING_FILE.write_text(json.dumps(template, indent=2) + "\n")
    sys.exit(f"{MAPPING_FILE.name} was missing; a template was written, review it and run again")
  mapping = json.loads(MAPPING_FILE.read_text())
  if mapping.get("schema") != "v1":
    sys.exit(f"{MAPPING_FILE.name} is stamped for schema {mapping.get('schema')!r}, "
             f"this module builds data for v1 only")
  for key in ("subflow_to_intent", "flow_to_issue_type"):
    if key not in mapping:
      sys.exit(f"{MAPPING_FILE.name} is missing '{key}'; fix the file, or delete it to regenerate the template")
  return mapping["subflow_to_intent"], mapping["flow_to_issue_type"]

# The logged action buttons grouped into the schema's agent_action values
# verification and bookkeeping buttons carry no resolution signal and are ignored
ACTION_GROUPS = {
  "notify-team": "escalate",
  "offer-refund": "refund_or_credit",
  "promo-code": "refund_or_credit",
  "update-order": "update_order",
  "make-purchase": "update_order",
  "update-account": "update_account",
  "make-password": "update_account",
  "log-out-in": "update_account",
  "membership": "update_account",
  "search-faq": "provide_information",
  "select-faq": "provide_information",
  "send-link": "provide_information",
  "instructions": "provide_information",
  "try-again": "provide_information",
  "subscription-status": "provide_information",
  "shipping-status": "provide_information",
  "search-membership": "provide_information",
  "search-pricing": "provide_information",
  "search-policy": "provide_information",
  "search-timing": "provide_information",
  "search-boots": "provide_information",
  "search-jeans": "provide_information",
  "search-jacket": "provide_information",
  "search-shirt": "provide_information",
}

# When a conversation contains several groups, the most consequential one wins
ACTION_PRECEDENCE = ("escalate", "refund_or_credit", "update_order", "update_account", "provide_information")


def load(data):
  with gzip.open(data.joinpath("abcd_v1.1.json.gz"), "rt", encoding="utf-8") as handle:
    return json.load(handle)


# Action turns are system events, not spoken text, and are kept out of every transcript.
# They also name the labels
def turns(convo):
  result = []
  for speaker, utterance in convo["original"]:
    if speaker == "action":
      continue
    text = str(utterance).strip()
    if text:
      result.append({"speaker": speaker, "text": text})
  return result


def text(convo):
  return " ".join(f"{t['speaker']}: {t['text']}" for t in turns(convo))


# Action buttons live in the delexed turn targets [intent, nextstep, action, ...]
def agent_action_of(convo):
  groups = set()
  for turn in convo["delexed"]:
    targets = turn.get("targets")
    button = targets[2] if targets else None
    if button in ACTION_GROUPS:
      groups.add(ACTION_GROUPS[button])
  for group in ACTION_PRECEDENCE:
    if group in groups:
      return group
  return "none"


# Direct indexing, an unknown subflow will abort, not silently drop examples
def gold_of(convo, to_intent, to_issue):
  scenario = convo["scenario"]
  return {
    "intent": to_intent[scenario["subflow"]],
    "intent_source": scenario["subflow"],
    "issue_type": to_issue[scenario["flow"]],
    "issue_type_source": scenario["flow"],
    "agent_action": agent_action_of(convo),
  }


def training_examples(data):
  corpus = load(data)
  to_intent, to_issue = load_mapping(corpus)
  examples = {"intent": [], "issue_type": [], "agent_action": []}
  for convo in corpus["train"]:
    convo_text = text(convo)
    gold = gold_of(convo, to_intent, to_issue)
    examples["issue_type"].append({"text": convo_text, "label": gold["issue_type"]})
    examples["agent_action"].append({"text": convo_text, "label": gold["agent_action"]})
    if gold["intent"]:
      examples["intent"].append({"text": convo_text, "label": gold["intent"]})
  return examples


# deterministic subflow-stratified selection: sorted ids, first n per subflow
def test_records(data, per_subflow=2):
  corpus = load(data)
  to_intent, to_issue = load_mapping(corpus)
  by_subflow = {}
  for convo in sorted(corpus["test"], key=lambda c: str(c["convo_id"])):
    by_subflow.setdefault(convo["scenario"]["subflow"], []).append(convo)

  records = []
  for subflow in sorted(by_subflow):
    for convo in by_subflow[subflow][:per_subflow]:
      record_id = f"abcd-{convo['convo_id']}"
      record = {"interaction_id": record_id, "turns": turns(convo)}
      records.append((record_id, record, gold_of(convo, to_intent, to_issue)))
  return records
