# Insight

Platform to turn customer service interactions into structured business intelligence.  
Upload an interaction, choose an extraction pipeline, then review its fields, source lines and processing steps in the web app.


## Overview

1. The web app sends a transcript or audio file to insight-core API.
2. For audio, Whisper creates a transcript. Pyannote assign speaker turns if necessary.
3. The API runs **one** of three extractors:
 - **P1** a TF-IDF classifier.
 - **P2** an LLM given up to five relevant conversation lines per field by default.
 - **P3** an LLM given the full conversation.
4. The API checks values against a versioned schema and stores the interaction, fields, citations and processing trace in PostgreSQL.

P2 and P3 cite conversation lines. Citations are checked against the lines supplied to the model; this does not verify that a line actually supports its value.

The default schema extracts intent, issue type, sentiment, resolution status and agent action.

Three pre-trained models are orchestrated across two data spaces, audio and text:

- `Whisper`: transcribes calls (audio => text).
- `SBERT`: finds the conversation lines that support each answer (text => evidence).
- `LLM`: turns the conversation into a structured record (text => fields).

Each model runs as its own container. The LLM is provider-agnostic (runs locally via Ollama). The default pipieline for this system is **P2** (Grounded LLM)

## Prerequisites

To run the system, you need [Docker Compose](https://docs.docker.com/compose/), [Python 3.10+](https://www.python.org/downloads/), [Git](https://git-scm.com/install/) and [FFmpeg/ffprobe](https://ffmpeg.org/download.html).  

In order to run [evaluation module](evaluation/README.md), preparation downloads for the evaluation corpora need to be downloaded, including audio. Check [data preparation instructions](dataprep/README.md)


## Run the project

Copy the example settings:

```bash
cp .env.example .env
cp insight-core/.env.example insight-core/.env
cp insight-web/.env.example insight-web/.env
```

For audio speaker diarisation, accept the [pyannote model terms](https://huggingface.co/pyannote/speaker-diarization-community-1) and set `HF_TOKEN` in the root `.env`.

Prepare data before starting the baseline service:

```bash
python3 dataprep/prepare.py
python3 dataprep/validate.py
docker compose up --build
```

Open [localhost:3000](http://localhost:3000). The first startup downloads the service images and AI models.

To try a transcript, upload the included example:

```bash
curl -i -F "file=@examples/transcript.json" -F "pipeline=p2" http://localhost:4000/interactions
```

The API returns an interaction ID with `pending` status. Replace `1` with the returned ID to read the result and processing trace:

```bash
curl http://localhost:4000/interactions/1
curl http://localhost:4000/interactions/1/steps
```

More example inputs, including a recorded call in mono, stereo and every accepted audio format, are in `examples/README.md`.


## Run the tests

Unit tests run without Docker or the datasets. Each part has its own suite:

```bash
cd insight-core && npm test
cd evaluation && python3 -m unittest
cd dataprep && python3 -m unittest
```

Checks against the running services are in [docs/testing.md](docs/testing.md), and the built datasets are checked with `python3 dataprep/validate.py`.



## Repository contents

| Folder | Purpose |
|---|---|
| `insight-core/` | Upload API, orchestration, schemas and database migrations. |
| `insight-web/` | React interface for uploading and reviewing interactions. |
| `baseline/` | P1 classifier training and service. |
| `dataprep/` | Dataset downloads, preparation and validation. |
| `examples/` | Example uploads in every accepted format, with their licences. |
| `evaluation/` | Prediction runner and scorers for research questions RQ1-RQ4. |
| `whisper/`, `diarization/`, `embeddings/`, `ollama/` | Audio transcription, speaker diarisation, retrieval and LLM services. |
| `docs/` | Setup, testing and schema guides. |


## Documentations

- [Dataset preparation and licences](dataprep/README.md)
- [Evaluation](evaluation/README.md)
- [API and local development](insight-core/README.md)
- [MIT licence](LICENSE); datasets retain their own licences.


### Data licences

Insight's original source code and associated documentation are released under the MIT License to support reproducibility, independent evaluation and reuse. This explicitly permits users to run, modify and redistribute the implementation while retaining the copyright and licence notice. Third-party datasets, dependencies and model weights remain governed by their own licences. Separating the software licence from these external terms makes the implementation reusable without implying unrestricted rights to the underlying data.


The data preparation pipeline uses the following independently licensed datasets:

| Dataset and source | Licence | Reuse conditions |
|---|---|---|
| [ABCD (ASAPP Research)](https://github.com/asappresearch/abcd) | [MIT](https://github.com/asappresearch/abcd/blob/master/LICENSE) | Preserve the upstream copyright and licence notice when redistributing copies or substantial portions. |
| [HarperValleyBank (Wu et al., Gridspace/Stanford)](https://github.com/cricketclub/gridspace-stanford-harper-valley) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Give appropriate attribution, link the licence and indicate changes when sharing. |
| [EmoWOZ (Feng et al.)](https://zenodo.org/records/6506504) | [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) | Non-commercial use only under this licence; attribution, a licence link and an indication of changes are required when sharing. |
| [MAIA-DQE (Mendonca et al.)](https://github.com/johndmendonca/MAIA-DQE) | [CC BY-ND 4.0](https://github.com/johndmendonca/MAIA-DQE/blob/main/LICENSE.md) | Attribution is required when sharing; adapted material cannot be shared under this licence. Keep converted records local and regenerate them from the upstream source. |

Raw corpora and generated data under `dataprep/data/` and `dataprep/out/` are
excluded from version control. Reproduce the data locally using the
[data preparation instructions](dataprep/README.md), subject to each source's terms.
Do not publish converted MAIA-DQE records without separate permission. MIT's
permission for commercial code reuse does not grant commercial rights to EmoWOZ
or blanket permission to redistribute datasets or trained models. Dataset
citations and preparation details are in [data sources](dataprep/docs/data-sources.md).
