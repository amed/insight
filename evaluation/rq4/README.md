# Research Question 4 - Schema extension

Can new BI fields be introduced through configuration without retraining or code changes while acceptable accuracy and evidential support are maintained.

Evaluates the `banking_task` field added through schema v2, using HarperValleyBank oracle transcripts.

Measures accuracy, validity and citation support. P1's schema mismatch is an expected refusal because its model was trained for v1.

After [collecting predictions](../README.md), run from the repository root:

```bash
python3 evaluation/rq4/run.py
```

Writes `results.csv` and `scores.json` to `evaluation/rq4/out/`. Makes no model requests.
