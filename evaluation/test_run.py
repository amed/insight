"""
Tests for the evaluation runner
===============================

The parts that decide what runs and what gets stored, without any service up.

run with:

  `$ python3 -m unittest`
"""

import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

import run
from helper import api


class CellPathTest(unittest.TestCase):

  # One file per cell, named so the scorers can split it back into its parts.
  def test_cell_path_layout(self):
    path = run.cell_path("v1", "abcd-text", "abcd-1", "text", "p2")
    self.assertEqual(path.parent, run.OUT.joinpath("v1"))
    self.assertEqual(path.name, "abcd-text__abcd-1__text__p2.json")


class MissingCellsTest(unittest.TestCase):

  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.original_out = run.OUT
    run.OUT = Path(self.tmp.name)
    self.records = {
      "abcd-text": [{"interaction_id": "abcd-1"}, {"interaction_id": "abcd-2"}],
      "maia-text": [],
      "hvb-audio": [],
    }

  def tearDown(self):
    run.OUT = self.original_out
    self.tmp.cleanup()

  # Every plan cell of the records is missing on an empty store, two records times three pipelines.
  def test_all_cells_missing_on_empty_store(self):
    self.assertEqual(len(run.missing_cells(self.records, None)), 6)

  # A cell that already has a file is never run again.
  def test_existing_cell_is_skipped(self):
    path = run.cell_path("v1", "abcd-text", "abcd-1", "text", "p2")
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    missing = run.missing_cells(self.records, None)
    self.assertEqual(len(missing), 5)
    self.assertNotIn(("abcd-text", self.records["abcd-text"][0], "text", "p2", "v1"), missing)

  # The limit takes the first records of every batch, for a pilot run.
  def test_limit_caps_records_per_batch(self):
    self.assertEqual(len(run.missing_cells(self.records, 1)), 3)


class BuildUploadTest(unittest.TestCase):

  # A text cell sends the record as json with a suffixed id, so reruns never collide in core.
  def test_text_variant_upload(self):
    record = {"interaction_id": "abcd-1", "turns": [{"speaker": "agent", "text": "hi"}]}
    form, file_name, file_bytes, content_type = run.build_upload("abcd-text", record, "text", "p3", "v1")
    payload = json.loads(file_bytes)
    self.assertEqual(form, {"pipeline": "p3", "schema": "v1"})
    self.assertEqual(file_name, "abcd-1.json")
    self.assertEqual(content_type, "application/json")
    self.assertTrue(payload["interaction_id"].startswith("abcd-1--text--p3--v1--"))
    self.assertEqual(payload["turns"], record["turns"])


class PredictTest(unittest.TestCase):

  # A failed upload is stored as its own status instead of raising or retrying.
  def test_failed_upload_is_stored_as_status(self):
    original = api.request

    def refuse(*args, **kwargs):
      raise urllib.error.URLError("connection refused")

    api.request = refuse
    try:
      result = run.predict("http://localhost:1", {}, "x.json", b"{}", "application/json", timeout=1)
    finally:
      api.request = original
    self.assertEqual(result["status"], "upload_failed")
    self.assertEqual(result["fields"], {})


if __name__ == "__main__":
  unittest.main()
