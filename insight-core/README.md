# insight-core

Backend API and orchestrator for Insight.

Upload a conversation transcript, it is stored as line-addressable units, and a (currently pending) insight record is created.

TODO:
A later slice plugs the real SBERT + LLM extraction into the processing seam (`src/services/processingService.js`). 

## Run

With Docker Compose from the repo root (starts Postgres + runs migrations + serves).

## Local development (without docker)

Run the dependencies in Docker and the API on your host with auto-reload (nodemon):

```bash
# start all services in Docker
docker compose up -d
# stop core
docker compose stop core

# install deps and apply migrations against it
npm install
npm run migrate:up

# run with reload on file changes
npm run dev
```

Connection and service URLs come from `.env` (see `.env.example`).

## Endpoints

```bash
# upload a transcript
curl -F "file=@examples/transcript.json" localhost:4000/interactions
# -> {"id":1,"status":"pending"}

# fetch the stored interaction + its lines + record
curl localhost:4000/interactions/1
```

Upload format:

```json
{
  "interaction_id": "demo-001",
  "turns": [
    { "speaker": "customer", "text": "..." },
    { "speaker": "agent", "text": "..." }
  ]
}
```

## Migrations

The schema is managed with `sequelize-cli`. Migrations apply automatically when
the container starts; the commands below are for local/manual use.

```bash
# create a new (empty) migration file in src/migrations/
npm run migrate:make -- add-record-fields

# apply all pending migrations
npm run migrate:up

# roll back the most recent migration
npm run migrate:down

# roll back every migration
npm run migrate:down:all
```

Each migration file has an `up` (apply) and a `down` (rollback). Keep `down` as
the exact inverse of `up` so rollbacks are clean.

The connection comes from `DATABASE_URL` (see `.env.example`).
