# Research Question 2 - Citation support

Are unsupported field values reduced by retrieval grounding compared with direct LLM extraction under matched conditions.

Compares P2 and P3 using unsupported-claim rate and first-attempt schema validity.

A claim counts as supported when at least one citation survives the supplied-line filter. This does not check semantic correctness. P1 has no citations and is excluded.

After [collecting predictions](../README.md), run from the repository root:

```bash
python3 evaluation/rq2/run.py
```

Writes `results.csv` and `scores.json` to `evaluation/rq2/out/`. Makes no model requests.
