# Research Question 1

How accurately are predefined BI fields extracted by the three pipelines when evaluated.

The module is dedicated to answer the first reasearch question, which is which one of the three extraction methods is best.

The build extracts fields in 3 ways: simple classifier, retrieval-grounded LLM, and LLM (P1, P2, and P3).


## Stages of evaluation

Evaluation schema is pinned to `insight-core/schemas/v1.json` through all phases.

### Prepare The Data (Stage 1)

Load the dataset directory and pair each record with its gold labels.

### Runner (Stage 2)

Run every record through each of the three pipelines via the core API and collect the predicted fields.

### Store Scores (Stage 3)

Compare predictions against gold labels and store per-field metrics for each pipeline.

### Report (Stage 4)

Aggregate the stored scores into a summary report comparing P1, P2, and P3.