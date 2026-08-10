"""
Core api calls
==============

predict runs one record through one pipeline: upload as multipart form data,
then poll until the record leaves pending or the deadline passes.

=============================================================================
Data shapes:

prediction (returned by predict, stored by the rq runners):
  status:         complete | failed | timeout
  fields:         {field: predicted value}
  config_version: str (what configuration produced the record)
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
      return {
        "status": status,
        "fields": {f["name"]: f["value"] for f in data["record"].get("fields", [])},
        "config_version": data["record"].get("config_version"),
      }
    time.sleep(2)

  return {"status": "timeout", "fields": {}, "config_version": None}
