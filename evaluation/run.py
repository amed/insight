"""
Evaluation runner
============================

The evaluation scores each pipeline using per-field metrics,


Stages
------
1. load_dataset    dataset dir -> records paired with gold labels
2. predict         one record through one pipeline -> predicted fields
3. score           predictions vs gold -> per field metrics
4. report          scores -> summary output
"""

FIELDS = [
  "intent",
  "issue_type",
  "sentiment",
  "resolution_status",
  "risk",
  "next_action",
]


def load_dataset(path):
  """return (record, gold) pairs from a dataset directory."""
  print("TODO")


def predict(core, record, pipeline):
  """run one record through one pipeline via the core api, return predicted fields."""
  print("TODO")


def score(predictions, gold):
  """compare predicted fields against gold, return per field metrics."""
  print("TODO")


def report(scores):
  """render scores into a summary."""
  print("TODO")


def main():
  """wire the stages: load, predict, score, report."""
  print("TODO")


# guarded so the module stays importable from tests
if __name__ == "__main__":
  main()
