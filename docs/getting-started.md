# Getting started

Bringing the full system up with Docker.
At the end every service runs in a container and you can upload a conversation and read back its extracted fields.

## Prerequisites

- Docker and Docker Compose.
- A Hugging Face account and a read token.
  The diarization model is gated, so this is required, not optional.
- Around 6 GB of free disk for the models, and patience on the first run.
- Python 3.10+, Git and FFmpeg/ffprobe for data preparation (evaluation only, see step 4).

## 1. Environment files and token

1. Accept the model terms at `https://hf.co/pyannote/speaker-diarization-community-1` while logged in (required step).
2. Create a read token at `https://hf.co/settings/tokens`.
3. Copy the env files (root, core, and web) and set the token.

```bash
cp .env.example .env                            # Repo root, holds HF_TOKEN.
cp insight-core/.env.example insight-core/.env
cp insight-web/.env.example insight-web/.env
# Edit .env and set HF_TOKEN=hf_yourtoken.
```

## 2. Bring up the stack

Run from the repository root.
Core applies database migrations automatically.

```bash
docker compose up --build
```

This builds and starts everything (postgres, whisper, embeddings, diarization, ollama, baseline, core, and web).
Core listens on `:4000`.
Open the web interface at [localhost:3000](http://localhost:3000) when the services are ready.

The first run is slow.
Images build, ollama pulls `llama3.1` (about 4.7 GB), and whisper, SBERT, and pyannote download their models.
Ollama and pyannote use persistent cache volumes.
Other downloads may repeat when containers are recreated.

The baseline container stops at startup until its training data is prepared (step 4).
This does not affect running the system, which extracts with the LLM pipelines (p2 by default).

## 3. Test

```bash
# List every endpoint.
curl -s localhost:4000/

# Upload the example transcript and read the resulting record.
id=$(curl -s -F "file=@examples/transcript.json" localhost:4000/interactions | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
curl -s "localhost:4000/interactions/$id"
```

The upload needs embeddings and ollama.
It returns before extraction finishes, so poll the record until its status leaves `pending`.
Per-service checks (whisper, embeddings, diarization, ollama) are in `docs/testing.md`.

## 4. Prepare data for the evaluation (optional)

This step is only for the evaluation.
Skip if you are not evaluating pipelines.

Prepare the data before starting the baseline, which trains automatically on startup.
Then start the baseline again so it trains on the prepared data.

```bash
python3 dataprep/prepare.py
python3 dataprep/validate.py
docker compose up -d baseline
```

Running the evaluation itself is documented in [evaluation](../evaluation/README.md).

## Ports

| service | port | notes |
|---|---|---|
| core | 4000 | the api |
| db | 5432 | postgres |
| whisper | 8001 | audio to text |
| embeddings | 8002 | SBERT retrieval |
| diarization | 8003 | who spoke when, gated model |
| baseline | 8004 | TF-IDF pipeline p1, trains on start |
| ollama | 11434 | LLM, pulls the model on first start |
| web | 3000 | react app |
