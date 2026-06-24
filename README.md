# Insight

AI platform that extracts structured, evidence-linked business intelligence from customer-support
interactions.

## Overview

Three pre-trained models are orchestrated across two data spaces, audio and text:

- Whisper: transcribes calls (audio => text).
- SBERT: finds the conversation lines that support each answer (text => evidence).
- LLM: turns the conversation into a structured record (text => fields).

Each model runs as its own container. The LLM is provider-agnostic (runs locally via Ollama) and can point at any OpenAI-compatible endpoint by changing URL.

## Run

```bash
docker compose up --build
```

insight-core `:4000`  
Postgres `:5432`   
Whisper `:8001`  
embeddings `:8002`  
Ollama `:11434`  

## Test

TODO: add unite/integration tests.

### Api
```bash
# transcribe
curl -F "file=@audio.wav" localhost:8001/transcribe

# search
curl localhost:8002/search -H "Content-Type: application/json" \
  -d '{"query":"refund","lines":["how can I help?","I want my money back"],"top_k":2}'

# generate
curl localhost:11434/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"llama3.1","messages":[{"role":"user","content":"hello"}]}'
```