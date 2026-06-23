# Transcriber

Production-oriented local/internal transcription stack with exactly two containers:
1. **Public API**: Express + TypeScript (`api`)
2. **Private Whisper service**: FastAPI + faster-whisper (`whisper`)

It accepts common audio/video uploads and returns either structured JSON or transcript files (`.json`, `.txt`, `.srt`, `.vtt`).

## Architecture

```text
Client
  |
  v
Express API (public, :3000)
  |- validates input, stores files/jobs on local disk
  |- sync endpoint (/v1/transcriptions)
  |- async queue + job endpoints (/v1/jobs/*)
  |- OpenAPI docs (/docs, /openapi.json)
  |
  v
FastAPI Whisper (internal only, docker network)
  |- model loaded once at startup
  |- /internal/transcribe
```

Single-node disk storage directories:
- `/data/uploads`
- `/data/results`
- `/data/jobs`

## Requirements
- Docker + Docker Compose
- For GPU: NVIDIA driver + NVIDIA Container Toolkit

## Quickstart (CPU)
```bash
cp .env.example .env
docker compose up --build
```

## Quickstart (GPU)
```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
```

## API Docs
- `http://localhost:3000/docs`
- `http://localhost:3000/openapi.json`

## Example cURL

Sync JSON:
```bash
curl -X POST "http://localhost:3000/v1/transcriptions" \
  -F "file=@sample.mp3" \
  -F "task=transcribe" \
  -F "output_format=json"
```

Sync JSON using local test file path (`../assets/test-dialog`):
```bash
curl -X POST "http://localhost:3000/v1/transcriptions" \
  -F "file=@../assets/test-dialog" \
  -F "task=transcribe" \
  -F "output_format=json"
```

Sync TXT download:
```bash
curl -X POST "http://localhost:3000/v1/transcriptions" \
  -F "file=@sample.mp3" \
  -F "task=transcribe" \
  -F "output_format=txt" \
  -F "return_file=true" \
  -o transcript.txt
```

Sync SRT download:
```bash
curl -X POST "http://localhost:3000/v1/transcriptions" \
  -F "file=@sample.mp3" \
  -F "task=transcribe" \
  -F "output_format=srt" \
  -F "return_file=true" \
  -o transcript.srt
```

Sync SRT download using local test file path:
```bash
curl -X POST "http://localhost:3000/v1/transcriptions" \
  -F "file=@../assets/test-dialog" \
  -F "task=transcribe" \
  -F "output_format=srt" \
  -F "return_file=true" \
  -o transcript.srt
```

Create async job:
```bash
curl -X POST "http://localhost:3000/v1/jobs" \
  -F "file=@sample.mp3" \
  -F "task=transcribe" \
  -F "output_format=vtt"
```

Job status:
```bash
curl "http://localhost:3000/v1/jobs/<job_id>"
```

Job JSON result:
```bash
curl "http://localhost:3000/v1/jobs/<job_id>/result"
```

Job file download:
```bash
curl -L "http://localhost:3000/v1/jobs/<job_id>/download" -o transcript.out
```

Delete job:
```bash
curl -X DELETE "http://localhost:3000/v1/jobs/<job_id>"
```

## Example JSON Response
```json
{
  "id": "uuid",
  "filename": "sample.mp3",
  "task": "transcribe",
  "model": "large-v3",
  "language": "de",
  "language_probability": 0.98,
  "duration": 123.45,
  "text": "Full transcript text",
  "segments": [
    { "start": 0, "end": 4.2, "text": "Segment text" }
  ],
  "metadata": {
    "created_at": "2026-05-16T00:00:00.000Z",
    "processing_seconds": 12.34
  }
}
```

## Model Guidance
- `large-v3`: best multilingual accuracy.
- `medium` / `small`: lower resource use.
- CPU local default: `WHISPER_COMPUTE=int8`.
- GPU fast path: `WHISPER_DEVICE=cuda` and `WHISPER_COMPUTE=float16`.

## Multilingual Notes
- Leave `language` unset for auto-detect.
- Mixed-language recordings can still be imperfect.
- Frequent language switching may improve with chunked pre-segmentation.

## File Size & Timeouts
- Configure upload limit with `MAX_UPLOAD_BYTES`.
- Configure API->Whisper timeout with `WHISPER_REQUEST_TIMEOUT_MS` (`0` disables timeout).

## Security Notes
- Optional API key: set `API_KEY` and send `x-api-key`.
- Whisper service is internal-only by default.
- Upload limits and rate-limit are enabled.

## Job Recovery and Retention
- Jobs persist as JSON under `/data/jobs`.
- On startup: `queued` jobs are re-queued, `processing` jobs are marked failed.
- Temp cleanup removes old upload files using `TEMP_FILE_TTL_HOURS`.
- Optional job retention via `JOB_RETENTION_HOURS`.

## Troubleshooting
- **ffmpeg decode errors**: verify source media and container ffmpeg install.
- **Slow first request**: model download can take time on first boot.
- **RAM pressure**: switch to smaller model or reduce concurrency.
- **CUDA not detected**: verify NVIDIA toolkit and GPU compose usage.
- **Volume permissions**: ensure Docker can write mounted `/data` volumes.

## Environment Variables
See `.env.example` for all options.
