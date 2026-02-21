#!/usr/bin/env python3
"""Seed default rules into Rasengan. Skips rules that already exist by name."""

import json
import sys
from pathlib import Path

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8050"

rules_file = Path(__file__).parent / "default_rules.json"
rules = json.loads(rules_file.read_text())

existing = {r["name"] for r in httpx.get(f"{BASE}/rules").json()}

created = 0
for rule in rules:
    if rule["name"] in existing:
        print(f"  skip  {rule['name']} (exists)")
        continue
    r = httpx.post(f"{BASE}/rules", json=rule)
    if r.status_code == 201:
        print(f"  created  {rule['name']} (id={r.json()['id']})")
        created += 1
    else:
        print(f"  FAILED  {rule['name']}: {r.status_code} {r.text}")

print(f"\nDone: {created} created, {len(rules) - created} skipped")
