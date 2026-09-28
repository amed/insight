# Evaluation review

Findings from reviewing the evaluation suite and data against the written plan before the first real run. Each component was assumed wrong until its behaviour had been re-derived; a finding counted once reproduced. Two passes over the code, one over the data.

## Pass 1: evaluation suite (29 findings)

| Area | Finding | Fix |
|---|---|---|
| Schema | Two schema files, two hash lengths, default id mismatched; core failed at start and every P1 record would have failed its schema claim | One id `v1`, file name equals schema name, one hash length; the runner posts `schema=v1` and refuses a batch built for another hash |
| Runner | Result files written non-atomically; an interrupted write was treated as finished | Temp file then rename for every artefact; unreadable cells fail scoring |
| Baseline | No training path; P1 trained on five fixture records | `dataprep` builds training files from the corpus train splits |
| Metrics | Macro-F1 classes taken from predictions; `unknown` scored as a class | Classes from gold only; abstention reported separately |
| Metrics | Coerced values counted as abstentions | `coerced` kept separate in the trace and the store |
| Metrics | About 4 % of HVB reference words were `[noise]` markers | Markers stripped at conversion; validation check added |
| Metrics | Role accuracy aligned by position | Aligned by word overlap |
| Metrics | First-attempt validity not computed | Derived from extract traces |
| Metrics | Unsupported-claim rule differed from the plan wording | Any surviving citation counts as cited; plan aligned |
| Robustness | One transient network error ended the run | Bounded retry with backoff on reads |
| Robustness | Partial corpus downloads treated as complete | Temp name, fail on HTTP error, rename |
| Reporting | Latency percentiles mixed timeouts and resumed cells; HTML reporter incomplete | Both removed; scorers write CSV and JSON with the criteria judged inside |
| Docs | Stale counts, a plan listing files that did not exist, a compose variable disagreeing with the trainer | Corrected or deleted |

Not fixed by design: recall@5 needs an evidence-annotated subset and is stated as a criterion only; HVB intent gold covers 26 of 50 calls and is reported as such.

## Pass 2: rebuilt runner (6 findings)

Repeated after the suite became one runner. Among them a transient poll failure that would have aborted a thirty-hour run and a scoring scope error. All fixed before the clean run.

## Pass 3: data (1 finding)

MAIA-DQE releases overlap: 544 dialogues, 43 duplicated, 501 distinct. A split made before deduplication leaked 18 held-out dialogues into training. Fix: deduplicate by id before splitting, write the holdout ids to disk, build the test batch from those ids only. `dataprep/validate.py` checks on every run that no training text equals any test text.