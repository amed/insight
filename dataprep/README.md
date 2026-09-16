# Data Preparation

Downloads ABCD, EmoWOZ, MAIA-DQE and HarperValleyBank, then builds schema-v1 training and evaluation data.

Everything in this data preparation module is bound to schema v1. The mappings are stamped, every training label and gold value is checked against its value sets at build time, and every output manifest carries its name and content hash.  

From the repository root:

```bash
python3 dataprep/prepare.py
python3 dataprep/validate.py
```





Requires Python 3.10+, Git and FFmpeg/ffprobe. Existing downloads, completed training files and test batches are skipped. Delete the relevant folder under `data/` or `out/` to rebuild it.

## Output

| Directory | Contents |
|---|---|
| `data/` | Downloaded corpora. |
| `out/training/` | Labelled examples for the five baseline fields. |
| `out/testing/abcd-text/` | 186 text records. |
| `out/testing/maia-text/` | 101 held-out dialogues. |
| `out/testing/hvb-audio/` | 50 calls as oracle/ASR transcripts and mono/stereo audio. |

Validation checks schema stamps, labels, train/test separation and audio properties. 

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


See [dataset mappings](docs/datasets.md) for label and split rules.


## Split discipline

- ABCD ships pre-split; training uses the train split, the batch the test split
- MAIA has no official split: dialogues are deduplicated by id (the released
  files overlap), sorted, and every fifth is held out; the holdout ids are
  written to `out/training/maia_holdout.json` and the batch is built from
  exactly those ids by the same code
- EmoWOZ is training-side only; HVB is testing-side only
- `validate.py` proves it: no training text equals any test record text


## Licences

- ABCD: MIT (Retain upstream copyright and licence notices).
- HarperValleyBank: CC BY 4.0 (attribute the source and indicate changes).
- EmoWOZ: CC BY-NC 4.0 (non-commercial use with attribution).
- MAIA-DQE: CC BY-ND 4.0 (keep converted records local).


## Notes

Raw and generated data are gitignored. See [sources and attribution](docs/data-sources.md).

**Check [docs/](./docs/) for more details about data sources**

A new schema (not v1) for evaluation is possible in theory, but it will make `validate.py` fail until the data is rebuilt.  
New Schema will need changing in mapping functions between datasets, in order to train specific fields for P1.
