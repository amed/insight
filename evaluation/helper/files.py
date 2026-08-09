"""
Output writing
==============

write_json is atomic (temp name, then rename), so an interrupted write can
never leave a truncated file that a skip-if-exists resume would trust.
"""

import csv
import json


def write_json(path, data):
  path.parent.mkdir(parents=True, exist_ok=True)
  tmp = path.with_name(path.name + ".tmp")
  tmp.write_text(json.dumps(data, indent=2) + "\n")
  tmp.replace(path)


def write_csv(path, header, rows):
  path.parent.mkdir(parents=True, exist_ok=True)
  with open(path, "w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(header)
    writer.writerows(rows)
