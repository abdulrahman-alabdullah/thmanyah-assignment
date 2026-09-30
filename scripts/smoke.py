#!/usr/bin/env python3
import json
import time
import urllib.request
import uuid

BASE = "http://127.0.0.1:8080"

def call(path, body=None):
    req = urllib.request.Request(BASE + path,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.status, json.load(response)

for attempt in range(60):
    try:
        assert call("/health/ready")[0] == 200
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("Application did not become ready")
message = "assessment-smoke-" + str(uuid.uuid4())
status, created = call("/api/notes", {"message": message})
assert status == 201
assert any(n["id"] == created["id"] and n["message"] == message for n in call("/api/notes")[1])
print(json.dumps({"test": "proxy_app_database_round_trip", "result": "PASS", "id": created["id"]}))
