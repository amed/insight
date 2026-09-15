"""
Service endpoints and availability
==================================

Every service url in one place, host ports as published in docker-compose.yml.
The rq runners read this table instead of hard coding urls, and call
check_services at the beginning of a run, so a half-up stack stops the run
before any upload instead of producing failed records half way through.
"""

import sys
import urllib.error
import urllib.request

ENDPOINTS = {
  "core": "http://localhost:4000",
  "whisper": "http://localhost:8001",
  "embeddings": "http://localhost:8002",
  "diarization": "http://localhost:8003",
  "baseline": "http://localhost:8004",
  "ollama": "http://localhost:11434",
}


# A service that answers anything, even a 404, is up.
# A refused connection is down and the run stops here with every down service named
def check_services(names):
  down = []
  for name in names:
    try:
      urllib.request.urlopen(ENDPOINTS[name], timeout=10)
    except urllib.error.HTTPError:
      pass
    except OSError:
      down.append(f"{name} ({ENDPOINTS[name]})")
  if down:
    # sys.exit prints to stderr and exits 1. The escape codes make it red.
    lines = "\n".join(f"\t- {entry}" for entry in down)
    sys.exit(f"\033[31mError! Services not reachable:\n\n{lines}\n\033[0m")
  print("services up: " + ", ".join(names))
