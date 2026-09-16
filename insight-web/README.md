# insight-web

Minimal React frontend for Insight.

## Run

Local dev (auto-reload):

```bash
npm install
npm run dev
```

Or with the rest of the stack via Docker Compose from the repo root:

```bash
docker compose up --build web
```

Either way it serves on http://localhost:3000.  
Set `VITE_API_URL=http://localhost:4000` in `insight-web/.env` before starting the dev server or building the Docker image.  
The provided `.env.example` contains this setting.
