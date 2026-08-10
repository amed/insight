# Research Question 2

Are unsupported field values reduced by retrieval grounding compared with direct LLM extraction under matched conditions.

The module is dedicated to answer the second research question, which is whether grounding actually pays off.

Only P2 and P3 are compared here. Both use the same model, schema, prompt, and settings, the only difference is retrieval: P2 sees the top-5 lines per field, P3 sees the whole conversation. P1 cannot cite evidence, so it is out of scope for this question.

The measurement comes from what core already stores per field: the citations, the dropped citations, and the coercion trace. No extra data is needed.


## Stages of evaluation

Evaluation schema is pinned to `insight-core/schemas/v1.json` through all phases.

### Prepare The Data (Stage 1)

Load the same records rq1 evaluates, straight from the dataprep batches. rq2 is self-contained: everything it produces lives under its own out/ directory, rq1's files are never modified.

### Collect (Stage 2)

One evidence prediction per record x P2/P3 in rq2's own out/predictions: copied from rq1's stored prediction when that file already carries the evidence keys, run fresh through the core API otherwise, skipped when it already exists (resume).

### Extract Evidence (Stage 3)

From each stored prediction, collect per field: the surviving citations, the dropped citations, and whether the value was coerced to unknown.

### Store Scores (Stage 4)

Compute the unsupported-claim rate per pipeline (claim-bearing values that are uncited or only invalidly cited) and the first-attempt validity, written as results.csv and scores.json.

### Report (Stage 5)

Compare P2 against P3. The pre-committed criteria are UCR(P2) < UCR(P3) and first-attempt validity at least 95 percent for both. The presentation layer is not built yet, scores.json carries the criteria verdicts.
