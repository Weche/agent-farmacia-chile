#!/usr/bin/env python3
"""
Quick smoke test for chat endpoints on the running server.
Defaults to http://127.0.0.1:8004
"""
import os
import sys
import json
import requests

BASE_URL = os.environ.get("CHAT_API_BASE", "http://127.0.0.1:8004")

def check(resp, label):
    ok = resp.status_code == 200
    print(f"{label}: {'✅' if ok else '❌'} ({resp.status_code})")
    if not ok:
        try:
            print("  Body:", resp.text[:500])
        except Exception:
            pass
    return ok

def main():
    # 1) Simple test endpoint
    r = requests.post(f"{BASE_URL}/api/chat", json={"message": "emergencia maipu direcciones"}, timeout=20)
    if check(r, "POST /api/chat"):
        data = r.json()
        msg = data.get("message", "")
        print("   message length:", len(msg), "maps:", ("maps.google.com" in msg))

    # 2) Create session
    r = requests.post(f"{BASE_URL}/api/chat/session", timeout=10)
    if not check(r, "POST /api/chat/session"): 
        sys.exit(1)
    session_id = r.json().get("session_id")
    print("   session_id:", session_id)

    # 3) Send message using body session_id (should be accepted)
    payload = {"message": "emergencia maipu direcciones", "session_id": session_id}
    r = requests.post(f"{BASE_URL}/api/chat/message", json=payload, timeout=30)
    if check(r, "POST /api/chat/message (body session_id)"):
        try:
            data = r.json()
            # Agent usually returns keys like success/response; print a small preview
            keys = list(data.keys())
            preview = data.get("response") or data.get("reply") or str(data)[:200]
            print("   keys:", keys)
            if isinstance(preview, str):
                print("   preview:", preview[:160].replace('\n', ' ') + ("..." if len(preview) > 160 else ""))
        except Exception as e:
            print("   parsing error:", e)

    # 4) Test links page
    r = requests.get(f"{BASE_URL}/test-links", timeout=10)
    if check(r, "GET /test-links"):
        html = r.text
        print("   has pharmacy-link:", ("pharmacy-link" in html), "has tel:", ("tel:" in html), "has maps:", ("maps.google.com" in html))

if __name__ == "__main__":
    main()
