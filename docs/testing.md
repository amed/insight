# Testing each service

Every service runs on its own and can be tested in isolation, then together as the
full pipeline. Bring one up with:

```bash
docker compose up -d <service>   # whisper | embeddings | diarization | ollama | db | core | web
```

Host ports:

| service | host port | internal | notes |
|---|---|---|---|
| web | 3000 | 3000 | React app, talks to core |
| core | 4000 | 4000 | the API, needs db |
| whisper | 8001 | 8000 | audio to text |
| embeddings | 8002 | 8000 | SBERT retrieval |
| diarization | 8003 | 8000 | who spoke when, gated model |
| ollama | 11434 | 11434 | LLM, needs the model pulled |
| db | 5432 | 5432 | postgres |

Core can also run locally with `npm run dev` (nodemon, port 4000). Locally it reads
`insight-core/.env`, where the model service urls point at the host ports above
(`localhost:8001`, `:8002`, `:8003`, `:11434`). In docker it reads the compose
environment, where they point at the service names. Do not run both the local and the
docker core at once, they both bind 4000.

---

## db (postgres)

```bash
docker compose up -d db
docker compose exec db pg_isready -U insight
docker compose exec db psql -U insight -d insight -c "\dt"
```

Expected: `accepting connections`, then a table list (`SequelizeMeta`, `interactions`,
`lines`, `insight_records`, `record_fields`, `field_citations`, `steps`). In Docker the
core image runs the migrations on start (via `entrypoint.sh`), so the tables appear only
after core has come up once. Running core locally, apply them with `npm run migrate:up`.

---

## whisper (audio to text)

```bash
docker compose up -d whisper

# default: the whole file is transcribed once (stereo is downmixed)
curl -s -F "file=@assets/test1.mp3" localhost:8001/transcribe

# opt-in: per-channel split, only safe when each channel is a single speaker
curl -s -F "file=@assets/test1.mp3" -F "split=true" localhost:8001/transcribe
```

Expected: JSON with `text`, `channels`, `split`, and `segments` as objects with
`start` and `end` times:

```json
{
  "text": "...",
  "channels": 2,
  "split": false,
  "segments": [ { "channel": null, "start": 0.0, "end": 2.4, "text": "..." } ]
}
```

`channels` is the source channel count from ffprobe. With `split=true` and two or more
channels, each segment carries its source `channel` (0 or 1) and `split` is `true`;
otherwise `channel` is `null` and `split` is `false`. The `end` times are what
diarization overlaps against, so a stale image without them breaks role assignment.

---

## embeddings (SBERT)

```bash
docker compose up -d embeddings

# raw vectors
curl -s localhost:8002/embed -H 'Content-Type: application/json' \
  -d '{"texts":["hello","I want a refund"]}'

# ranked search (used by the pipeline)
curl -s localhost:8002/search -H 'Content-Type: application/json' \
  -d '{"query":"refund","lines":["how can I help?","I want my money back"],"top_k":2}'
```

Expected: `/embed` returns `{ "vectors": [[...],[...  ]] }`. `/search` returns
`{ "matches": [ { "index": 1, "score": 0.5 }, ... ] }` ordered best first. `top_k` is
capped at the number of lines.

---

## diarization (agent/customer who & when)

Uses `pyannote/speaker-diarization-community-1`, a gated model. Before the first run:
accept its terms on hugging face while logged in, put a read token in the repo-root
`.env` as `HF_TOKEN=hf_...` (copy `.env.example`), and compose passes it through. The
model is downloaded once into the `hfcache` volume and loaded at startup, so the first
build and the first request are slow. It runs on cpu.

```bash
docker compose up -d diarization

# diarize an audio file (first call is slow, the model loads on startup)
curl -s -F "file=@assets/test1.mp3" localhost:8003/diarize
```

Expected: `/diarize` returns anonymous speaker turns and the set of speaker labels:

```json
{
  "turns": [ { "start": 0.0, "end": 2.4, "speaker": "SPEAKER_00" }, ... ],
  "speakers": [ "SPEAKER_00", "SPEAKER_01" ]
}
```

The labels are clusters, not roles. Core overlaps these turns against the whisper
segments and maps the clusters to agent and customer (first speaker is the agent unless
`AGENT_SPEAKS_FIRST=false`).

---

## baseline (TF-IDF, pipeline p1)

Trains at container start on the 5 fixture conversations in `baseline/fixtures/`
(sub-second), so the model can never go stale against the fixture data. Fields and
allowed values come from the schema file (mounted from `insight-core/schemas`); a fixture
label outside the schema aborts the training. The trained version is a hash of the
fixture data, stored with every p1 record as `config_version`.

```bash
docker compose up -d baseline

curl -s localhost:8004/extract -H 'Content-Type: application/json' \
  -d '{"lines":[{"speaker":"customer","text":"I was charged twice, I want a refund"}]}'
```

Expected: all field values, the model version, and the schema claim the artifact was
trained for (core fails any p1 record whose schema does not match it):

```json
{ "fields": [ { "name": "intent", "value": "refund_request" }, ... ],
  "model_version": "tfidf-logreg|6407b704569f21",
  "schema": "v1", "schema_hash": "346a2faee4f519" }
```

---

## ollama (LLM)

```bash
docker compose up -d ollama

# the model must be present first (pulled on first start, takes a while)
curl -s localhost:11434/api/tags

# a generation
curl -s localhost:11434/v1/chat/completions -H 'Content-Type: application/json' \
  -d '{"model":"llama3.1","messages":[{"role":"user","content":"reply with one word"}]}'
```

Expected: `/api/tags` lists a model containing `llama3.1`. The chat call returns an
OpenAI-style body with `choices[0].message.content`.

---

## core (the API)

Needs db. Background field extraction also needs embeddings and ollama; audio upload of
combined audio also needs whisper and diarization.

```bash
docker compose up -d db core   # or run core locally with: npm run dev

# list every endpoint
curl -s localhost:4000/

# list interactions (empty array at first)
curl -s localhost:4000/interactions
```

### upload a json transcript

The simplest path, no model services needed for ingest. Shape is
`{ "interaction_id": string, "turns": [{ "speaker", "text" }] }`.

```bash
curl -s -i -F "file=@insight-core/examples/transcript.json" localhost:4000/interactions
```

### upload audio

```bash
# combined audio: diarization infers the roles
curl -s -i -F "file=@assets/test1.mp3" localhost:4000/interactions

# separated channels: speaker comes from the channel, pick which one is the agent
curl -s -i -F "file=@assets/test1.mp3" \
  -F "split_channels=true" -F "agent_channel=0" localhost:4000/interactions
```

`split_channels` (`true`/`1`) transcribes each channel separately and labels by channel.
`agent_channel` (default `0`, the left channel, the amazon convention) says which channel
is the agent. Without `split_channels`, the file is treated as combined and diarization
assigns the roles; if diarization is down the speakers stay `unknown` and the upload
still succeeds.

### choose the extraction pipeline and schema

Any upload takes an optional `pipeline` form field: `p1` (TF-IDF baseline), `p2`
(retrieval-grounded LLM, the default), or `p3` (direct LLM, whole conversation, no
retrieval), and an optional `schema` form field (the base schema `v1` when
omitted, see `docs/schemas.md`). The pipeline, its effective configuration, and the
schema stamp are stored on the record.

```bash
# the loaded schemas
curl -s localhost:4000/schemas

# value counts for one schema version, optionally one pipeline
curl -s "localhost:4000/schemas/support/summary?version=1&pipeline=p2"
```

```bash
curl -s -i -F "file=@baseline/fixtures/fixture-001.json" -F "pipeline=p3" localhost:4000/interactions
```

To run all three pipelines on the 5 fixture conversations and print the records side by
side (needs the full stack up):

```bash
python3 evaluation/e2e.py
```

The script uploads sequentially, waits for each record, checks that all six fields were
produced, prints any error steps, and writes a run manifest to `evaluation/runs/`.

### read results and trace

```bash
# read one interaction back (use the id returned by the upload)
curl -s localhost:4000/interactions/1

# the per-step trace (ingest, retrieve, extract, ...) for debugging
curl -s localhost:4000/interactions/1/steps
```

Expected: `/` returns the endpoint list, `/interactions` returns an array, an upload
returns `202 {"id":...,"status":"pending"}` immediately. All the heavy work runs on the
background path, so a read taken right after the upload shows `status: pending` with empty
`lines`. The `lines` and the `fields` (each a `name`, `value`, and supporting `citations`)
appear together once the record reaches `complete`; if a stage fails it ends `failed`.
`/:id/steps` returns the ordered trace, each step with a `name`, `status`
(`ok`/`skipped`/`error`), and a `detail` object, which is the fastest way to see where a
call stalled. Poll the read until the status leaves `pending`.

---

## web

```bash
docker compose up -d web
```

Open http://localhost:3000. The Upload tab posts file, text, or audio to core; the
Interactions tab lists them and opens each one with its lines, fields, and steps. Calls
go from the browser to core on `:4000`.

---

## the full pipeline

```bash
docker compose up -d            # bring everything up
curl -s -i -F "file=@assets/test1.mp3" localhost:4000/interactions
# note the id, then poll until the record status leaves pending
curl -s localhost:4000/interactions/<id>
curl -s localhost:4000/interactions/<id>/steps
```

The upload returns at once; everything below runs in the background. Audio flows through
whisper then diarization in sequence (both are cpu heavy, so they are not overlapped),
the lines are stored, then for each field embeddings ranks the lines and ollama extracts a
grounded value. A json transcript skips whisper and diarization. The steps trace records
every stage either way.
