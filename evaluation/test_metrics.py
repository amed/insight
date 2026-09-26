"""
Tests for the scoring metrics
=============================

Every metric on a tiny hand-made input with a known answer.

run with:

  `$ python3 -m unittest`
"""

import unittest

from helper import metrics


class AccuracyTest(unittest.TestCase):

  def test_correct_over_total(self):
    self.assertEqual(metrics.accuracy([("a", "a"), ("a", "b")]), 0.5)

  # Nothing scored gives None, never a perfect score.
  def test_empty_is_none(self):
    self.assertIsNone(metrics.accuracy([]))


class MacroF1Test(unittest.TestCase):

  # Classes absent from gold are skipped, so the averaged set never depends on the predictions.
  # Here a scores f1 0.8, b scores 0, and c is not in gold.
  def test_averages_over_gold_classes_only(self):
    pairs = [("a", "a"), ("a", "a"), ("b", "a")]
    self.assertAlmostEqual(metrics.macro_f1(pairs, ["a", "b", "c"]), 0.4)

  # unknown is never a class, an abstention is only a miss on the gold class.
  def test_unknown_is_not_a_class(self):
    pairs = [("a", "unknown"), ("a", "a")]
    self.assertAlmostEqual(metrics.macro_f1(pairs, ["a", "b"]), 2 / 3)


class WerTest(unittest.TestCase):

  # One substitution, one deletion and one insertion over four reference words.
  def test_counts_edits_over_reference_words(self):
    self.assertAlmostEqual(metrics.wer("the card was lost", "a card lost today"), 0.75)

  # Case and punctuation are normalised away before comparing.
  def test_normalisation(self):
    self.assertEqual(metrics.wer("Hello, there!", "hello there"), 0.0)

  def test_empty_reference_is_none(self):
    self.assertIsNone(metrics.wer("", "anything"))


class RoleAccuracyTest(unittest.TestCase):

  # A line is judged against the reference turn sharing the most words, not the one at its position.
  def test_matches_by_word_overlap(self):
    turns = [
      {"speaker": "agent", "text": "hello how can i help"},
      {"speaker": "customer", "text": "i lost my card"},
    ]
    lines = [
      {"speaker": "customer", "text": "i lost my card"},
      {"speaker": "customer", "text": "hello how can i help"},
    ]
    self.assertEqual(metrics.role_accuracy(lines, turns), 0.5)


class BootstrapTest(unittest.TestCase):

  # The interval brackets the point estimate and repeats exactly for the same seed.
  def test_deterministic_interval(self):
    pairs = [("a", "a")] * 8 + [("a", "b")] * 2
    low, high = metrics.bootstrap_ci(pairs, metrics.accuracy, resamples=200, seed=1)
    self.assertLessEqual(low, 0.8)
    self.assertGreaterEqual(high, 0.8)
    self.assertEqual(metrics.bootstrap_ci(pairs, metrics.accuracy, resamples=200, seed=1), [low, high])

  def test_empty_is_none(self):
    self.assertIsNone(metrics.bootstrap_ci([], metrics.accuracy))


if __name__ == "__main__":
  unittest.main()
