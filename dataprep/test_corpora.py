"""
Tests for the label rules
=========================

The per-corpus mapping rules on tiny hand-made inputs, no downloads needed.

run with:

  `$ python3 -m unittest`
"""

import unittest

from corpora import abcd, emowoz, hvb, maia


class AbcdTest(unittest.TestCase):

  def convo(self, *buttons):
    return {"delexed": [{"targets": [None, None, button]} for button in buttons]}

  # The most consequential group wins when a conversation has several logged actions.
  def test_action_precedence(self):
    self.assertEqual(abcd.agent_action_of(self.convo("search-faq", "offer-refund", "update-account")), "refund_or_credit")
    self.assertEqual(abcd.agent_action_of(self.convo("update-order", "notify-team")), "escalate")

  # Verification buttons carry no action, the label is none.
  def test_none_without_grouped_button(self):
    self.assertEqual(abcd.agent_action_of(self.convo("pull-up-account", None)), "none")

  # Action events are system turns and never reach the transcript.
  def test_action_turns_are_dropped(self):
    convo = {"original": [["agent", "hi"], ["action", "Account has been pulled up"], ["customer", " ok "]]}
    self.assertEqual(abcd.turns(convo), [{"speaker": "agent", "text": "hi"}, {"speaker": "customer", "text": "ok"}])


class MaiaTest(unittest.TestCase):

  def dialogue(self, emotions, dropped=0, success=None):
    return {
      "turns": [{"floor": "inbound", "Emotion": emotions}],
      "dialog": {"Dropped conversation": dropped, "Task Sucess": success},
    }

  # The customer's last non-neutral emotion decides, neutral only when nothing else was felt.
  def test_sentiment_is_last_non_neutral(self):
    self.assertEqual(maia.sentiment_of(self.dialogue([6, 2, 0])), "positive")
    self.assertEqual(maia.sentiment_of(self.dialogue([0, 2, 5])), "negative")
    self.assertEqual(maia.sentiment_of(self.dialogue([2, 2])), "neutral")
    self.assertIsNone(maia.sentiment_of(self.dialogue([])))

  # Dropped calls are unresolved, high scores resolved, low scores unresolved, the midpoint has no label.
  def test_resolution_mapping(self):
    self.assertEqual(maia.resolution_of(self.dialogue([], dropped=1, success=5)), "unresolved")
    self.assertEqual(maia.resolution_of(self.dialogue([], success=4)), "resolved")
    self.assertEqual(maia.resolution_of(self.dialogue([], success=2)), "unresolved")
    self.assertIsNone(maia.resolution_of(self.dialogue([], success=3)))

  # Every fifth dialogue is held out and the rest train.
  def test_split_every_fifth(self):
    trainable, holdout = maia.split([{"id": str(i)} for i in range(10)])
    self.assertEqual([d["id"] for d in holdout], ["0", "5"])
    self.assertEqual(len(trainable), 8)


class EmowozTest(unittest.TestCase):

  # The adjudicated gold sits last in each turn's annotation list, agent turns carry none.
  def test_last_non_neutral_gold(self):
    dialogue = {"log": [
      {"text": "hi", "emotion": [{"sentiment": 1}, {"emotion": 0, "sentiment": 1}]},
      {"text": "hello", "emotion": []},
      {"text": "thanks", "emotion": [{"sentiment": 0}, {"emotion": 0, "sentiment": 2}]},
    ]}
    self.assertEqual(emowoz.sentiment_of(dialogue), "positive")
    self.assertEqual(emowoz.text(dialogue), "customer: hi agent: hello customer: thanks")


class HvbTest(unittest.TestCase):

  # Segments are ordered by time, markers are stripped, and marker-only segments are dropped.
  def test_turns(self):
    segments = [
      {"speaker_role": "caller", "start_ms": 900, "human_transcript": "hi [noise] there"},
      {"speaker_role": "agent", "start_ms": 100, "human_transcript": "hello"},
      {"speaker_role": "agent", "start_ms": 500, "human_transcript": "[noise]"},
    ]
    self.assertEqual(hvb.turns(segments, "human_transcript"),
                     [{"speaker": "agent", "text": "hello"}, {"speaker": "customer", "text": "hi there"}])

  # Calls are taken round robin over the tasks, so every task appears before any repeats.
  def test_select_calls_round_robin(self):
    calls = [("a1", "pay bill"), ("a2", "pay bill"), ("b1", "check balance")]
    self.assertEqual(hvb.select_calls(calls, 2), [("b1", "check balance"), ("a1", "pay bill")])


if __name__ == "__main__":
  unittest.main()
