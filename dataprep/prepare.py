"""
Prepares all data for training and testing
==========================================

The one command. Downloads the raw corpora, writes the baseline training files,
and builds the test batches. Every step is skipped when its output exists, so
an interrupted run continues where it stopped. After a run, check everything
with validate.py.

Usage
-----
  python3 prepare.py

=============================================================================
What it produces:

data/          raw corpora (abcd, emowoz, maia, harper-valley-bank)
out/training/  one [{text, label}] json per schema field,
               maia_holdout.json (dialogue ids reserved for testing),
               manifest.json (schema v1 stamp + content hash)
out/testing/   abcd-text, maia-text, hvb-audio
               (each: records/, gold.json, manifest.json, hvb also audio/)
"""

from pathlib import Path

import download
import testing
import training

DATA = Path(__file__).parent.joinpath("data")
OUT = Path(__file__).parent.joinpath("out")


def main():
  download.fetch_all(DATA)
  training.write_all(DATA, OUT.joinpath("training"))
  testing.write_all(DATA, OUT.joinpath("testing"))
  print("done")


main()
