# Testing each service

Every service runs on its own and can be tested in isolation, then together as the full pipeline.
Run these commands from the repository root.
Each section lists the service to start.

The host ports are listed below.

| service | host port | internal | notes |
|---|---|---|---|
| web | 3000 | 3000 | React app, talks to core |
| core | 4000 | 4000 | the API, needs db |
| whisper | 8001 | 8000 | audio to text |
| embeddings | 8002 | 8000 | SBERT retrieval |
| diarization | 8003 | 8000 | who spoke when, gated model |
| baseline | 8004 | 8000 | TF-IDF pipeline p1, needs prepared training data |
| ollama | 11434 | 11434 | LLM, needs the model pulled |
| db | 5432 | 5432 | postgres |

Core can also run locally with `npm run dev` (nodemon, port 4000).
Compose loads `insight-core/.env` into the core container, so the model service urls in that file point at the service names.
To run core locally, change them to the host ports above (`localhost:8001`, `:8002`, `:8003`, `:8004`, `:11434`).
Do not run both the local and the docker core at once, they both bind 4000.

---

## db (postgres)

```bash
docker compose up -d db
docker compose exec db pg_isready -U insight
docker compose exec db psql -U insight -d insight -c "\dt"
```

The expected output is `accepting connections`, then a table list (`SequelizeMeta`, `interactions`, `lines`, `insight_records`, `record_fields`, `field_citations`, `steps`).
Compose runs `npm run migrate:up` before starting core, so the tables appear after core has started once.
Running core locally, apply them with `npm run migrate:up`.

---

## whisper (audio to text)

```bash
docker compose up -d whisper

# The whole file is transcribed once by default (stereo is downmixed).
curl -s -F "file=@example.mp3" localhost:8001/transcribe
```

The tracked sample is mono.
To test `split=true`, use a multi-channel file with one speaker on each channel.

The expected response is JSON with `text`, `channels`, `split`, and `segments` as objects with `start` and `end` times.

```json
{
  "text": "...",
  "channels": 1,
  "split": false,
  "segments": [ { "channel": null, "start": 0.0, "end": 2.4, "text": "..." } ]
}
```

`channels` is the source channel count from ffprobe.
With `split=true` and two or more channels, each segment carries its source `channel` (0 or 1) and `split` is `true`.
Otherwise `channel` is `null` and `split` is `false`.
Core uses the `start` and `end` times to match diarization turns to transcript segments.

---

## embeddings (SBERT)

```bash
docker compose up -d embeddings
# Raw vectors.
curl -s localhost:8002/embed -H 'Content-Type: application/json' \
  -d '{"texts":["hello","I want a refund"]}'

# Ranked search (used by the pipeline).
curl -s localhost:8002/search -H 'Content-Type: application/json' \
  -d '{"query":"refund","lines":["how can I help?","I want my money back"],"top_k":2}'
```

The expected response from `/embed` is `{ "vectors": [[...],[...  ]] }`.
`/search` returns `{ "matches": [ { "index": 1, "score": 0.5 }, ... ] }` ordered best first.
`top_k` is capped at the number of lines.

---

## diarization (agent/customer who & when)

Uses `pyannote/speaker-diarization-community-1`, a gated model.
Before the first run, accept its terms on hugging face while logged in and put a read token in the repo-root `.env` as `HF_TOKEN=hf_...` (copy `.env.example`).
Compose passes it through.
The model is downloaded once into the `hfcache` volume and loaded at startup, so the first start and the first request are slow.
It runs on cpu.

```bash
docker compose up -d diarization

# Diarize an audio file (first call is slow, the model loads on startup).
curl -s -F "file=@example.mp3" localhost:8003/diarize
```

`/diarize` is expected to return anonymous speaker turns and the set of speaker labels.

```json
{
  "turns": [ { "start": 0.0, "end": 2.4, "speaker": "SPEAKER_00" }, ... ],
  "speakers": [ "SPEAKER_00", "SPEAKER_01" ]
}
```

The tracked sample contains one speaker, so it only checks that the service responds.
The labels are clusters, not roles.
Core overlaps these turns against the whisper segments and maps the clusters to agent and customer (first speaker is the agent unless `AGENT_SPEAKS_FIRST=false`).

---

## baseline (TF-IDF, pipeline p1)

Training data is prepared by the dataprep module (corpus downloads, label rules, train/test split discipline, see `dataprep/README.md`).
Training itself is one script with no configuration.

```bash
python3 dataprep/prepare.py   # Once, download corpora, build training and test data.
python3 baseline/train.py     # Fit one classifier per schema field.
```

`train.py` reads `dataprep/out/training/` (one `[{text, label}]` json per field) and trains all five v1 fields.
The schema comes from `insight-core/schemas` (mounted read-only).
A label outside the schema aborts the training.
An existing `model.joblib` is reused only while its schema claim matches the current schema, so a schema change retrains automatically.
The trained version is a hash of the training data, stored with every p1 record as `config_version`.

```bash
docker compose up -d baseline

curl -s localhost:8004/extract -H 'Content-Type: application/json' \
  -d '{"lines":[{"speaker":"customer","text":"I was charged twice, I want a refund"}]}'
```

The expected response holds all field values, the model version, and the schema claim the artifact was trained for (core fails any p1 record whose schema does not match it).

```json
{ "fields": [ { "name": "intent", "value": "refund_request" }, ... ],
  "model_version": "tfidf-logreg|3eef3375eda46d",
  "schema": "v1", "schema_hash": "3a499d748778e7" }
```

---

## ollama (LLM)

```bash
docker compose up -d ollama

# The model must be present first (pulled on first start, takes a while).
curl -s localhost:11434/api/tags

# A generation.
curl -s localhost:11434/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"llama3.1","messages":[{"role":"user","content":"reply with one word"}]}'
```

`/api/tags` is expected to list a model containing `llama3.1`.
The chat call returns an OpenAI-style body with `choices[0].message.content`.

---

## core (the API)

Needs db.
P1 also needs baseline.
P2 needs embeddings and ollama.
P3 needs ollama.
Audio needs whisper, and combined audio also needs diarization.

```bash
docker compose up -d db core   # Or run core locally with npm run dev.

# List every endpoint.
curl -s localhost:4000/

# List interactions (empty array at first).
curl -s localhost:4000/interactions
```

### upload a json transcript

The simplest path, no model services needed for ingest.
Shape is `{ "interaction_id": string, "turns": [{ "speaker", "text" }] }`.

```bash
id=$(curl -s -F "file=@examples/transcript.json" localhost:4000/interactions | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')
echo "$id"
```

### upload audio

For combined audio, upload the tracked sample used in the Whisper check.
It is mono and contains one speaker, so it does not test speaker separation.
For `split_channels`, use a multi-channel file with one speaker on each channel and set `agent_channel` to `0` or `1`.
Without `split_channels`, the file is treated as combined and diarization assigns roles.
If diarization is unavailable, the upload can still succeed with speakers marked unknown.

```bash
curl -s -i -F "file=@example.mp3" localhost:4000/interactions
```

### choose the extraction pipeline and schema

Any upload takes an optional `pipeline` form field, `p1` (TF-IDF baseline), `p2` (retrieval-grounded LLM, the default), or `p3` (direct LLM, whole conversation, no retrieval).
It also takes an optional `schema` form field (the base schema `v1` when omitted, see `docs/schemas.md`).
The pipeline, its effective configuration, and the schema stamp are stored on the record.

```bash
# The loaded schemas.
curl -s localhost:4000/schemas

# Value counts for one schema version, optionally one pipeline.
curl -s "localhost:4000/schemas/v1/summary?pipeline=p2"
```

```bash
curl -s -i -F "file=@examples/transcript.json" -F "pipeline=p3" localhost:4000/interactions
```

The research evaluation runner is documented in [evaluation](../evaluation/README.md).

### read results and trace

```bash
# Read one interaction back with the id returned by the upload.
curl -s "localhost:4000/interactions/$id"

# The per-step trace (ingest, retrieve, extract, ...) for debugging.
curl -s "localhost:4000/interactions/$id/steps"
```

`/` is expected to return the endpoint list, `/interactions` an array, and an upload `202 {"id":...,"status":"pending"}` immediately.
All the heavy work runs on the background path, so a read taken right after the upload shows `status: pending` with empty `lines`.
The `lines` appear once ingest finishes, and the `fields` (each a `name`, `value`, and supporting `citations`) once the record reaches `complete`.
Lines from audio carry `start` and `end` in seconds, lines from a transcript carry `null` unless the turns included them.
A failure before extraction, or a failed p1 call, ends the record as `failed`.
A failed field extraction in p2 or p3 is traced, and the record still completes without that field.
`/:id/steps` returns the ordered trace, each step with a `name`, `status` (`ok`/`skipped`/`error`), and a `detail` object, which is the fastest way to see where a call stalled.
Poll the read until the status leaves `pending`.

---

## web

```bash
docker compose up -d web
```

Open http://localhost:3000.
The Upload tab posts file, text, or audio to core.
The Interactions tab lists them and opens each one with its lines, fields, and steps.
Calls go from the browser to core on `:4000`.

---

For full-stack setup and an end-to-end upload, see [getting started](getting-started.md).
