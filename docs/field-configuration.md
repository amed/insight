# BI field configuration (schemas)

Extraction is driven by schemas.
A schema is a versioned set of BI fields where each upload (or batch of uploads) chooses the schema it is extracted under,
and the same schema later drives how results are aggregated and charted.

Production runs on the LLM pipelines (p2 or p3), which absorb any schema dynamically.
The classical baseline (p1) is an evaluation instrument only.
It is trained for one frozen schema when a measurement requires it, and it never shapes schema design.

Schemas are fully separated from each other.
Every record, summary, chart, and any work derived from them belongs to exactly one schema.
Nothing is ever computed across schemas.
The separation is logical, not physical (one set of tables, every record stamped with its schema reference, every query partitioned by it).


For current behavior, see [schemas](schemas.md).
These decisions guide schema changes and comparisons.

- The default evaluation schema is `v1`.
  Its five fields and value sets are used by the prepared training data and evaluation runs.
- Each record keeps the schema name, version, and content hash used for extraction.
  When a schema already has records or evaluation results, create a new schema file for a change so earlier results keep their meaning.
- Each field has a question and a closed set of values.
  `unknown` is implicit.
  Missing output is counted separately because it can indicate a failed extraction stage.
- P2 retrieves conversation lines with the field question.
  P3 sends the full conversation.
  Both use the same question and answer values so their outputs can be compared.
- P1 is trained for `v1`.
  Core rejects a prediction when its schema claim does not match the record.
  P1 does not automatically support new schemas.
- Schema summaries show value counts.
  Accuracy scores are produced by the evaluation runners, which compare predictions with dataset labels.
