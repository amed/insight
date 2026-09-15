# Insight Core

API that processes uploads through P1, P2 or P3 and stores records, citations and processing traces in PostgreSQL. Use the [root setup](../README.md#run) to run it in Docker.  

Use the [root setup](../README.md#run) to run it in Docker.

## Local development (without docker)

Stop the Docker core with `docker compose stop core`. From this directory, copy `.env.example` to `.env` if needed and replace Docker service addresses with:

| Setting | Local value |
|---|---|
| `DATABASE_URL` | `postgres://insight:insight@localhost:5432/insight` |
| `WHISPER_URL` | `http://localhost:8001` |
| `EMBEDDINGS_URL` | `http://localhost:8002` |
| `DIARIZATION_URL` | `http://localhost:8003` |
| `BASELINE_URL` | `http://localhost:8004` |
| `LLM_BASE_URL` | `http://localhost:11434/v1` |

Keep the other services running, then:

```bash
npm install
npm run migrate:up
npm run dev
```

## API

```bash
curl -i -F "file=@examples/transcript.json" -F "pipeline=p2" http://localhost:4000/interactions
curl http://localhost:4000/interactions/1
curl http://localhost:4000/interactions/1/steps
```

Replace `1` with the returned ID.  
Poll `record.status` until it leaves `pending`.  
Uploads accept `pipeline=p1|p2|p3` (default `p2`) and a schema name from `GET /schemas` (default `v1`).  
Audio with separate speakers per channel can use `split_channels=true` and `agent_channel=0` or `1`.  
`GET /` lists endpoints.  
`GET /schemas` lists schemas.  
Each JSON filename in [schemas](schemas/) must match its `name`.  
Rebuild core to apply changes in Docker.  
P1 requires a matching trained schema. [Check P1 basline](../baseline/README.md).

## Tests

```bash
npm test -- --runInBand
```
