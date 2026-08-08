# Data preparation

Multiple data sources are used in order to provide proper data for evaluation.  
**Check [docs/](./docs/) for more details about data sources**

Everything in this data preparation module is bound to schema v1: the mappings are stamped for it, every training label and gold value is checked against its value sets at build time, and every output manifest carries its name and content hash.
A new schema (not v1) is possible in theory, but it makes `validate.py` fail until the data is rebuilt. New Schema will need chaning in mapping functions between datasets in order to train specific fields for P1.


```bash
python3 prepare.py    # download corpora, write training files, build test batches
python3 validate.py   # check everything prepare.py produced
```

To rebuild from scratch, delete output (a file under `out/training/`, a batch directory
under `out/testing/`, a corpus under `data/`).

## Layout

```
data/            raw corpora, downloaded once (about 3.5 gb, mostly hvb audio)
out/training/    baseline training files: one [{text, label}] json per field,
                 plus maia_holdout.json (dialogue ids reserved for testing)
out/testing/     one directory per batch: records/, gold.json, manifest.json
corpora/         one module per corpus: files, structure, label rules,
                 plus the reviewed mapping files (abcd_mapping.json, hvb_mapping.json)
```

## What is prepared

Training (used only by the baseline, `baseline/train.py` reads `out/training/`):

| field | source |
|---|---|
| intent | ABCD train split, subflow mapping |
| issue_type | ABCD train split, flow mapping |
| agent_action | ABCD train split, grouped action buttons |
| sentiment | EmoWOZ + MAIA train part, gold emotion annotations |
| resolution_status | MAIA train part, task success + dropped annotations |

Testing (uploaded to the pipelines by the evaluation, never trained on):

| batch | content | gold |
|---|---|---|
| abcd-text | 186 text records, ABCD test split | intent, issue_type, agent_action |
| maia-text | held-out MAIA dialogues | sentiment, resolution_status |
| hvb-audio | 50 calls: oracle + asr text records, mono + stereo wavs | intent, speakers |

## Split discipline

- ABCD ships pre-split; training uses the train split, the batch the test split
- MAIA has no official split: dialogues are deduplicated by id (the released
  files overlap), sorted, and every fifth is held out; the holdout ids are
  written to `out/training/maia_holdout.json` and the batch is built from
  exactly those ids by the same code
- EmoWOZ is training-side only; HVB is testing-side only
- `validate.py` proves it: no training text equals any test record text

## Licenses

ABCD MIT, HVB CC BY 4.0, EmoWOZ CC BY-NC 4.0 (non-commercial), MAIA-DQE CC
BY-ND 4.0 (no derivatives: the converted maia records must stay out of any
public repository). `data/` and `out/` are gitignored. The MAIA customer side
is machine-translated english; state this as a limitation when reporting.
