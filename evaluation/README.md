# Evaluation: The Reports of Research Questions

The step-by-step guide through the evaluation suite. All commands in this document runs from the repository root, not this directoy.


## What this produces

Three pipelines (p1 tf-idf baseline, p2 retrieval-grounded llm, p3 direct llm) are run
over the same conversations in every input variant (verified transcript, provided
machine transcript, mono audio, stereo audio). The suite scores the results against gold
labels and renders one report per batch plus a cross-batch verdict comparing the
pipelines. Every number is traceable to a stored raw artifact.


## Prerequisites

- python 3.10+
- ffmpeg
- git and curl
- disk: about 4 gb free
- for the run stages: the docker stack up (`docs/getting-started.md`) and the migrations
  applied


### Build and Validate the Datasets


All datasets come from the dataprep module, which downloads the corpora, builds
the training files and the three test batches, and stamps everything for schema
v1 (see `dataprep/README.md` and `dataprep/datasets.md`):

```bash
python3 dataprep/prepare.py    # download, build training files, build batches
python3 dataprep/validate.py   # 30+ checks incl. v1 stamps and split discipline
```

Batches:
- `abcd-text` (~180 records; gold intent, issue_type, agent_action)
- `maia-text` (~100 records; gold sentiment, resolution_status)
- `hvb-audio` (~50 calls as oracle/asr text records plus mono/stereo wavs. Gold intent, speakers)

The taxonomy decisions live in `dataprep/corpora/abcd_mapping.json` and `hvb_mapping.json`

## Running and Generating the Report

TODO: add 
