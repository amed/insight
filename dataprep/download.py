"""
Downloads every raw corpus into data/
=====================================

The download list comes from the corpora modules (each declares its own files),
so adding a corpus never touches this file:
- abcd, emowoz, maia: plain files via FILES (name -> url)
- harper-valley-bank: a git clone (3 gb)

Downloads are atomic: everything lands under a temporary name and is renamed
only after the write completes, so an interrupted run never leaves a truncated
file that looks finished. Existing files and directories are skipped, delete
one to fetch it again.
"""

import subprocess
import sys
import urllib.request

from corpora import abcd, emowoz, hvb, maia


# One plain file, temp name then rename, a failed download leaves nothing behind
def fetch_file(data, name, url):
  target = data.joinpath(name)
  if target.exists():
    return
  print(f"downloading {name} (once) ...")
  part = data.joinpath(f"{name}.part")
  try:
    with urllib.request.urlopen(url, timeout=120) as response:
      part.write_bytes(response.read())
  except Exception as error:
    part.unlink(missing_ok=True)
    sys.exit(f"download of {name} failed ({error}); preparation needs all corpora, aborting")

  part.rename(target)


# The hvb repository, cloned into a temp directory then renamed
def fetch_hvb(data):
  target = data.joinpath(hvb.CLONE_DIR)
  if target.exists():
    return
  print(f"cloning {hvb.CLONE_DIR} (3 gb, once) ...")
  part = data.joinpath(f"{hvb.CLONE_DIR}.part")
  result = subprocess.run(["git", "clone", "--depth", "1", hvb.CLONE_URL, str(part)])
  if result.returncode != 0:
    sys.exit(f"clone of {hvb.CLONE_URL} failed; preparation needs all corpora, aborting")

  part.rename(target)


def fetch_all(data):
  data.mkdir(exist_ok=True)
  for corpus in (abcd, emowoz, maia):
    for name, url in corpus.FILES.items():
      fetch_file(data, name, url)
  fetch_hvb(data)
