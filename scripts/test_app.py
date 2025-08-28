#!/usr/bin/env python3
"""
Lightweight API smoke tests using Flask's test client.
Runs without starting a server and without external services.

Usage:
  python scripts/test_app.py

Notes:
  - Uses demo-mode and reset endpoints to ensure predictable data.
  - Writes files under enhanced_autonomous_pm/data/ops (safe sandbox).
  - Email test is invoked but not required to succeed (no SMTP in CI).
"""

import os
import sys
import argparse
import json
import io
from unittest.mock import patch
from types import SimpleNamespace


def main():
    # Args
    ap = argparse.ArgumentParser(description="API smoke tests (local or live)")
    ap.add_argument('--live', action='store_true', help='Run against a live server instead of Flask test client')
    ap.add_argument('--base-url', default='http://127.0.0.1:5000', help='Base URL for live server')
    ap.add_argument('--require-email', action='store_true', help='Fail if email test fails (live mode)')
    args = ap.parse_args()

    # Ensure repo root is importable
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Optional: set an admin token for protected endpoints
    os.environ.setdefault("ADMIN_TOKEN", "apitest-token")
    admin_headers = {"X-Admin-Token": os.environ.get("ADMIN_TOKEN", "")} if os.environ.get("ADMIN_TOKEN") else {}

    if args.live:
        client = LiveClient(args.base_url)
    else:
        # Import the Flask app after env setup
        import flask_app as appmod
        app = appmod.app
        client = app.test_client()

    results = []

    def step(name, fn):
        try:
            fn()
            results.append((name, True, ""))
        except AssertionError as e:
            results.append((name, False, str(e)))
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {e}"))

    step("health", lambda: assert_health(client))

    step(
        "enable_demo_mode",
        lambda: assert_json_ok(
            client.post("/api/v1/admin/demo-mode", json={"enabled": True}, headers=admin_headers)
        ),
    )
    step(
        "reset_demo_data",
        lambda: assert_json_ok(client.post("/api/v1/admin/reset-demo-data", headers=admin_headers)),
    )

    # Read-only analytics endpoints
    for ep in [
        "/api/v1/projects/health",
        "/api/v1/projects/resource-utilization",
        "/api/v1/projects/budget-burndown",
        "/api/v1/projects/timeline",
        "/api/v1/projects/team-performance",
        "/api/v1/analytics/predictions",
    ]:
        step(ep, lambda ep=ep: assert_json_ok(client.get(ep)))

    # NLP inference preview -> confirm write_file
    step(
        "nlp_infer_write_preview",
        lambda: assert_infer_preview(client, "Please write file note.txt with hello world"),
    )
    step(
        "nlp_write_file_confirm",
        lambda: assert_write_file(client, "note.txt", "hello world", headers=admin_headers),
    )
    step(
        "ops_file_read",
        lambda: assert_ops_read_contains(client, "note.txt", "hello world"),
    )

    # RAG upload/query if Chroma available
    step("rag_upload_query", lambda: maybe_test_rag(client, admin_headers))

    # Email test
    if args.live:
        # Live: try real endpoint; do not fail unless --require-email
        def live_email():
            try:
                j = client.post('/api/v1/email/test', json={}, headers=admin_headers).get_json(silent=True)
                if args.require_email:
                    assert j and j.get('success') is True, f"Email test failed: {j}"
            except Exception as e:
                if args.require_email:
                    raise
        step("email_test_live", live_email)
    else:
        # Local in-process: mock SMTP for deterministic success
        step("email_test_mock_smtp", lambda: test_email_with_mock(client, admin_headers))

    # Summary
    passed = sum(1 for _, ok, _ in results if ok)
    failed = len(results) - passed
    print("\n=== API Smoke Test Summary ===")
    for name, ok, msg in results:
        print(f"[{ 'OK' if ok else 'FAIL'}] {name}{': ' + msg if msg else ''}")
    print(f"Total: {len(results)}  Passed: {passed}  Failed: {failed}")
    if failed:
        raise SystemExit(1)


def assert_json_ok(resp):
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.get_json(silent=True)
    assert data is not None, "No JSON returned"
    assert data.get("success") is True, f"Response not success: {data}"
    return data


def assert_health(client):
    data = assert_json_ok(client.get("/api/v1/health"))
    assert "data" in data, "Health missing data"
    return data


def assert_infer_preview(client, prompt: str):
    data = client.post("/api/v1/nlp/execute", json={"prompt": prompt}).get_json(silent=True)
    assert data and data.get("requires_confirmation") is True, f"Expected preview, got {data}"
    assert data.get("inferred_intent") in ("write_file", "read_file", "team_message", "exec_email", "leadership_update")


def assert_write_file(client, path: str, content: str, headers=None):
    headers = headers or {}
    data = assert_json_ok(
        client.post(
            "/api/v1/nlp/execute",
            json={"intent": "write_file", "args": {"path": path, "content": content}, "confirm": True},
            headers=headers,
        )
    )
    assert path in data.get("path", ""), f"Path mismatch: {data}"


def assert_ops_read_contains(client, path: str, needle: str):
    data = client.get(f"/api/v1/ops/file?path={path}").get_json(silent=True)
    assert data and data.get("success") is True, f"Failed to read ops file: {data}"
    assert needle in (data.get("content") or ""), f"Content mismatch"


def maybe_test_rag(client, admin_headers):
    health = assert_health(client)
    chroma_ok = False
    try:
        chroma_ok = bool(health["data"]["chromadb"]["ok"])  # type: ignore[index]
    except Exception:
        chroma_ok = False
    if not chroma_ok:
        # Skip RAG test gracefully
        return
    # Upload a small text file
    content = b"RAG test: Project RAG001 contains the token zebra-laser for retrieval."
    data = {
        'files': (io.BytesIO(content), 'rag_test.txt')
    }
    resp = client.post('/api/v1/files/upload', data=data, headers=admin_headers, content_type='multipart/form-data')
    j = resp.get_json(silent=True)
    assert j and j.get('success') is True, f"Upload failed: {j}"
    # Query RAG
    q = {"query": "Which document mentions zebra-laser?"}
    jq = client.post('/api/v1/rag/query', json=q).get_json(silent=True)
    assert jq and jq.get('success') is True, f"RAG query failed: {jq}"
    # contexts may be empty depending on vector search, but endpoint must succeed


def test_email_with_mock(client, admin_headers):
    class DummySMTP:
        def __init__(self, host, port, timeout=10):
            self.host = host; self.port = port
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False
        def starttls(self):
            return True
        def login(self, user, password):
            return True
        def sendmail(self, from_addr, to_addrs, msg):
            # Simulate success
            return {}

    os.environ.setdefault('SMTP_HOST', 'smtp.test')
    os.environ.setdefault('SMTP_PORT', '587')
    os.environ.setdefault('FROM_EMAIL', 'noreply@test')
    with patch('smtplib.SMTP', DummySMTP):
        j = client.post('/api/v1/email/test', json={'to': 'someone@example.com'}, headers=admin_headers).get_json(silent=True)
        assert j and j.get('success') is True, f"Email test failed: {j}"


if __name__ == "__main__":
    main()


# --- Live client adapter ----------------------------------------------
class LiveResponse:
    def __init__(self, r):
        self._r = r
        self.status_code = r.status_code
    def get_json(self, silent=True):
        try:
            return self._r.json()
        except Exception:
            return None if silent else (_ for _ in ()).throw(ValueError('Invalid JSON'))


class LiveClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        import requests  # lazy import
        self._req = requests
    def get(self, path, **kwargs):
        url = self.base_url + path
        return LiveResponse(self._req.get(url, **kwargs))
    def post(self, path, **kwargs):
        url = self.base_url + path
        return LiveResponse(self._req.post(url, **kwargs))
