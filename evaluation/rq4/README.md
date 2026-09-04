# Research Question 4

Can new BI fields be introduced through configuration without retraining or code changes while acceptable accuracy and evidential support are maintained.

The module is dedicated to answer the fourth research question, which is whether the schema mechanism actually delivers extension by configuration.

The new field is `banking_task` (the 8 HarperValleyBank task types), added through schema v2 which is v1 plus that one field. Gold needs no new annotation: every hvb call's task label is already stored as `intent_source` in the batch gold. P1 is part of the answer by design: its artifact claims schema v1, so a v2 record fails on the claim mismatch, the supervised pipeline structurally cannot follow a configuration-only change.


## Stages of evaluation

The new field is pinned to `insight-core/schemas/v2.json` (v1 plus banking_task), everything else stays v1.

### Add The Schema (Stage 1)

Drop v2.json into `insight-core/schemas/` and restart core. The registry validates and serves it, no code changes, no retraining.

### Prepare The Data (Stage 2)

Reuse the hvb-audio oracle records, the banking_task gold is derived from `intent_source` in the batch gold (50/50 coverage).

### Runner (Stage 3)

The one cycle (`evaluation/run.py`) uploads every record with `schema=v2` through all three pipelines, P1's cells record the designed refusal (schema claim mismatch, record fails with a traced reason). This module only reads the v2 prediction store.

### Store Scores (Stage 4)

Store schema validity, banking_task accuracy against the task gold, and the citation support of the new field.

### Report (Stage 5)

Judge against the pre-committed criteria: first-attempt validity at least 95 percent, banking_task accuracy within 10 points of intent accuracy on the same calls.
