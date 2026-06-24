#!/bin/bash
ollama serve &          # start server in background
pid=$!
until ollama list >/dev/null 2>&1; do sleep 1; done   # wait until ready
ollama pull llama3.1     # no-op if already pulled (stored in the volume)
wait $pid                # keep container running
