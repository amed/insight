# Getting started

Bringing the full system up with Docker. At the end every service runs in a container and
you can upload a conversation and read back its extracted fields.

## Prerequisites

- Docker and Docker Compose.
- A Hugging Face account and a read token. The diarization model is gated, so this is
  required, not optional.
- Around 6 GB of free disk for the models, and patience on the first run.

## 1. Environment files and token

1. Accept the model terms at `https://hf.co/pyannote/speaker-diarization-community-1` while
   logged in. (required step)
2. Create a read token at `https://hf.co/settings/tokens`.
3. Copy the env files (root, core, and web) and set the token:

```bash
cp .env.example .env                            # repo root, holds HF_TOKEN
cp insight-core/.env.example insight-core/.env
cp insight-web/.env.example insight-web/.env
# edit .env and set HF_TOKEN=hf_yourtoken
```

## 2. Bring up the stack

```bash
docker compose up --build
```

This builds and starts everything: postgres, whisper, embeddings, diarization, ollama,
core, and web. Core runs the database migrations on start, then listens on `:4000`.

The first run is slow: images build, ollama pulls `llama3.1` (about 4.7 GB), and whisper,
SBERT, and pyannote each download their model once into a volume. Later runs reuse the
volumes and start quickly.

## 3. Test

```bash
# list every endpoint
curl -s localhost:4000/

# upload the example transcript (no models needed for a transcript)
curl -s -i -F "file=@insight-core/examples/transcript.json" localhost:4000/interactions

# note the id from the response, then poll until status leaves pending
curl -s localhost:4000/interactions/1
```

The record reaches `complete` with cited fields once embeddings and ollama have answered.
Per-service checks (whisper, embeddings, diarization, ollama) are in `docs/testing.md`.

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
