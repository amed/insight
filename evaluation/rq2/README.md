# Research Question 2

Are unsupported field values reduced by retrieval grounding compared with direct LLM extraction under matched conditions.

The module is dedicated to answer the second research question, which is whether grounding actually pays off.

Only P2 and P3 are compared here. Both use the same model, schema, prompt, and settings, the only difference is retrieval: P2 sees the top-5 lines per field, P3 sees the whole conversation. P1 cannot cite evidence, so it is out of scope for this question.

The measurement comes from what core already stores per field: the citations, the dropped citations, and the coercion trace. No extra data is needed.


## Stages of evaluation

Evaluation schema is pinned to `insight-core/schemas/v1.json` through all phases.

### Prepare The Data (Stage 1)

Collect rq1's stored P2 and P3 prediction files. Nothing is uploaded twice: rq1 already runs both pipelines on every record and its predictions carry the citations and trace flags core kept per field.

### Backfill (Stage 2)

Prediction files written before the evidence fields existed are upgraded in place from core's stored interactions (found by their interaction id prefix, the newest complete one wins).

### Extract Evidence (Stage 3)

From each stored prediction, collect per field: the surviving citations, the dropped citations, and whether the value was coerced to unknown.

### Store Scores (Stage 4)

Compute the unsupported-claim rate per pipeline (claim-bearing values that are uncited or only invalidly cited) and the first-attempt validity, written as results.csv and scores.json.

### Report (Stage 5)

Compare P2 against P3. The pre-committed criteria are UCR(P2) < UCR(P3) and first-attempt validity at least 95 percent for both. The presentation layer is not built yet, scores.json carries the criteria verdicts.
