# insight-web

Minimal React frontend for Insight. Vite, JS only, React Query for data. No UI library.

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

Either way it serves on http://localhost:3000. The backend URL is `VITE_API_URL`
in `.env` (defaults to insight-core on `:4000`).
