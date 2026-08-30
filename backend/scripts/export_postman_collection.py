#!/usr/bin/env python3
"""
Regenerates backend/postman_collection.json from the live OpenAPI spec.

Requires: the backend running locally, and the `openapi-to-postmanv2` CLI
(npm install -g openapi-to-postmanv2).

Run: cd backend && python3 scripts/export_postman_collection.py
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
OPENAPI_URL = "http://localhost:8000/openapi.json"
RAW_SPEC_PATH = BACKEND_DIR / "openapi.json"
COLLECTION_PATH = BACKEND_DIR / "postman_collection.json"


def main():
    print(f"Fetching {OPENAPI_URL} ...")
    try:
        with urllib.request.urlopen(OPENAPI_URL, timeout=5) as resp:
            spec = json.load(resp)
    except Exception as exc:
        print(f"Could not reach the backend at {OPENAPI_URL} - is it running? ({exc})", file=sys.stderr)
        sys.exit(1)

    RAW_SPEC_PATH.write_text(json.dumps(spec, indent=2))
    print(f"Wrote {RAW_SPEC_PATH} ({len(spec['paths'])} paths)")

    result = subprocess.run(
        ["openapi2postmanv2", "-s", str(RAW_SPEC_PATH), "-o", str(COLLECTION_PATH), "-p"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        print("openapi2postmanv2 failed - install it with: npm install -g openapi-to-postmanv2", file=sys.stderr)
        sys.exit(1)

    # Post-process: use {{userId}} for the temporary auth header instead of
    # a literal placeholder string, and point baseUrl at local dev by default.
    collection = json.loads(COLLECTION_PATH.read_text())

    for v in collection.get("variable", []):
        if v["key"] == "baseUrl":
            v["value"] = "http://localhost:8000"

    def patch_headers(items):
        for it in items:
            if "item" in it:
                patch_headers(it["item"])
                continue
            for h in it.get("request", {}).get("header", []):
                if h.get("key") == "X-User-Id":
                    h["value"] = "{{userId}}"
            for resp in it.get("response", []):
                for h in resp.get("originalRequest", {}).get("header", []):
                    if h.get("key") == "X-User-Id":
                        h["value"] = "{{userId}}"

    patch_headers(collection["item"])
    collection["info"]["description"] = (
        "Cloud Storage Service API - Postman collection generated from the live "
        "OpenAPI spec.\n\nImport the companion postman_environment.json alongside "
        "this collection, then set `userId` to a real user UUID from your "
        "database (auth isn't built yet - see app/core/deps.py - so every "
        "request authenticates via the X-User-Id header instead of a token)."
    )

    COLLECTION_PATH.write_text(json.dumps(collection, indent=2))
    RAW_SPEC_PATH.unlink()  # scratch file, not meant to be committed
    print(f"Wrote {COLLECTION_PATH}")


if __name__ == "__main__":
    main()
