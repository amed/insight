"""
EmoWOZ: task-oriented dialogues with gold per-turn user sentiment
=================================================================

Provides training examples for:
- sentiment

from the full corpus (multiwoz + dialmage files), training side only, no test batch is built from it.
The conversation label is the customer's last non-neutral gold sentiment, else neutral.

User turns carry an annotation list whose last entry is the adjudicated gold {emotion, sentiment},
encoded 0 neutral, 1 negative, 2 positive (per the official hugging face loader hhu-dsml/emowoz).
Turns alternate customer/agent, the customer speaks first.

Source: https://zenodo.org/record/6506504 (CC BY-NC 4.0)

=============================================================================
Data schema before/after preparation:

Before:
one EmoWOZ dialogue (emowoz-multiwoz.json / emowoz-dialmage.json, dict of id -> dialogue)

dialogue:
  log:
    - text:    str (one utterance, alternating customer/agent, customer first)
      emotion: [ {annotator, annotation}, ..., {emotion, sentiment} ]
               (last entry is the adjudicated gold; [] on agent turns)

After:
dataprep outputs

training example (out/training/sentiment.json):
  - text:  str (customer: ... agent: ...)
    label: str (positive | neutral | negative)
"""

import json

FILES = {
  "emowoz-multiwoz.json": "https://zenodo.org/record/6506504/files/emowoz-multiwoz.json",
  "emowoz-dialmage.json": "https://zenodo.org/record/6506504/files/emowoz-dialmage.json",
}

SENTIMENT = {0: "neutral", 1: "negative", 2: "positive"}


# Even turns are the customer, odd turns the agent, only even turns carry emotion annotations
def text(dialogue):
  parts = []
  for i, turn in enumerate(dialogue["log"]):
    speaker = "customer" if i % 2 == 0 else "agent"
    parts.append(f"{speaker}: {turn['text']}")
  return " ".join(parts)


# The customer's last non-neutral gold sentiment, else neutral
def sentiment_of(dialogue):
  label = 0
  for turn in dialogue["log"]:
    if turn["emotion"]:
      gold = turn["emotion"][-1]["sentiment"]
      if gold != 0:
        label = gold

  return SENTIMENT[label]


def training_examples(data):
  examples = []
  for name in FILES:
    dialogues = json.loads((data.joinpath(name)).read_text())
    for dialogue in dialogues.values():
      examples.append({"text": text(dialogue), "label": sentiment_of(dialogue)})

  return examples
