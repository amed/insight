# Evaluation - The Reports of Research Questions

Runs all three pipelines on prepared conversations and scores four research questions.

Requires the [data](../dataprep/README.md) and [running stack](../README.md#run-the-project). Run commands from the repository root.

## Run

```bash
# Small test: first five records per batch, across variants and pipelines
python3 evaluation/run.py --limit 5 --skip-scoring

# Full collection and scoring
python3 evaluation/run.py
```

Predictions go to `evaluation/out/predictions/`. Existing files are skipped, including failures and timeouts; move a saved file out of the store to recollect that cell.

## Score existing predictions

```bash
python3 evaluation/rq1/run.py
python3 evaluation/rq2/run.py
python3 evaluation/rq3/run.py
python3 evaluation/rq4/run.py
```

Each scorer writes `results.csv` and `scores.json` to its own `rqN/out/` directory.

| Question | Measures |
|---|---|
| [RQ1](rq1/README.md) | Field accuracy and macro-F1. |
| [RQ2](rq2/README.md) | Citation support and schema validity. |
| [RQ3](rq3/README.md) | Transcription errors and downstream prediction changes. |
| [RQ4](rq4/README.md) | Adding a field through schema configuration. |

The full plan has 1,611 cells: 186 ABCD conversations, 101 MAIA conversations and 50 HarperValleyBank calls across input variants, pipelines and schemas. Pilot scores are partial. Citation support checks line references, not whether the cited text proves the answer.
