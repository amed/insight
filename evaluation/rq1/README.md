# Research Question 1 - Extraction accuracy

How accurately are predefined BI fields extracted by the three pipelines when evaluated.  

Compares P1, P2 and P3 against available gold labels using per-field accuracy, macro-F1 and bootstrap intervals.

Uses schema v1 and text/oracle inputs.

After [collecting predictions](../README.md), run from the repository root:

```bash
python3 evaluation/rq1/run.py
```

Writes `results.csv` and `scores.json` to `evaluation/rq1/out/`. Makes no model requests.
