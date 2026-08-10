"""
Core api calls
==============

predict runs one record through one pipeline: upload as multipart form data,
then poll until the record leaves pending or the deadline passes. The stored
prediction also carries the evidence core kept per field (citations, dropped
citations, coercion), so rq2 can be answered from the same files without
uploading anything twice.

=============================================================================
Data shapes:

prediction (returned by predict, stored by the rq runners):
  status:            complete | failed | timeout
  api_id:            int (the interaction id in core, for later lookups)
  fields:            {field: predicted value}
  citations:         {field: [line ids that survived the grounding filter]}
  dropped_citations: {field: [cited line ids the filter rejected]}
  coerced:           {field: bool (the first answer was off-schema)}
  config_version:    str (what configuration produced the record)
"""

import json
import time
import urllib.request
import uuid


# Multipart body built by hand, stdlib has no builder (RFC 7578)
def multipart(fields, file_name, file_bytes):
  boundary = f"----rq{uuid.uuid4().hex}"
  parts = b""
  for name, value in fields.items():
    parts += (f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'
              f"\r\n\r\n{value}\r\n").encode()
  parts += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{file_name}"\r\nContent-Type: application/json\r\n\r\n').encode()
  body = parts + file_bytes + f"\r\n--{boundary}--\r\n".encode()

  return body, {"Content-Type": f"multipart/form-data; boundary={boundary}"}


def request(method, url, body=None, headers=None):
  req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
  with urllib.request.urlopen(req, timeout=60) as res:
    return json.loads(res.read())


# The per-field evidence, read from the record and its step trace. Core writes
# one extract:<field> step per field with the coercion flag and the citations
# its grounding filter dropped
def evidence(core, api_id, record_data):
  steps = request("GET", f"{core}/interactions/{api_id}/steps")
  coerced = {}
  dropped = {}
  for step in steps:
    if step["name"].startswith("extract:") and step["status"] == "ok":
      field = step["name"].split(":", 1)[1]
      coerced[field] = bool(step["detail"].get("coerced", False))
      dropped[field] = step["detail"].get("dropped_citations", [])

  return {
    "citations": {f["name"]: f.get("citations", []) for f in record_data.get("fields", [])},
    "dropped_citations": dropped,
    "coerced": coerced,
  }


# One record through one pipeline via the core api:
# upload, then poll until the record leaves pending or the deadline passes.
# The interaction id is suffixed so reruns never collide with the unique constraint
def predict(core, record, pipeline, timeout=900):
  payload = dict(record)
  payload["interaction_id"] = f"{record['interaction_id']}--{pipeline}--{uuid.uuid4().hex[:8]}"
  body, headers = multipart({"pipeline": pipeline, "schema": "v1"},
                            f"{record['interaction_id']}.json",
                            json.dumps(payload).encode())
  created = request("POST", f"{core}/interactions", body, headers)

  deadline = time.time() + timeout
  while time.time() < deadline:
    data = request("GET", f"{core}/interactions/{created['id']}")
    status = (data.get("record") or {}).get("status")
    if status in ("complete", "failed"):
      extra = evidence(core, created["id"], data["record"])
      return {
        "status": status,
        "api_id": created["id"],
        "fields": {f["name"]: f["value"] for f in data["record"].get("fields", [])},
        "citations": extra["citations"],
        "dropped_citations": extra["dropped_citations"],
        "coerced": extra["coerced"],
        "config_version": data["record"].get("config_version"),
      }
    time.sleep(2)

  return {"status": "timeout", "api_id": created["id"], "fields": {}, "citations": {},
          "dropped_citations": {}, "coerced": {}, "config_version": None}
