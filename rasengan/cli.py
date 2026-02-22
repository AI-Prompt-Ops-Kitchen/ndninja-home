#!/usr/bin/env python3
"""Rasengan CLI — interact with the event hub from the terminal."""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime

import subprocess

import httpx

BASE_URL = os.environ.get("RASENGAN_URL", "http://127.0.0.1:8050")
TIMEOUT = 10.0

# ── Deploy registry ─────────────────────────────────────────────────────────

DEPLOY_REGISTRY = {
    "sage_mode": "/home/ndninja/sage_mode/swarm-deploy.sh",
    "ndn_infra": "/home/ndninja/infra/deploy.sh",
    "landing": "/home/ndninja/server-landing/deploy.sh",
}

# ── ANSI colors ──────────────────────────────────────────────────────────────

C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_MAGENTA = "\033[35m"
C_CYAN = "\033[36m"
C_WHITE = "\033[37m"

# ── HTTP helpers ─────────────────────────────────────────────────────────────

def _die(msg: str):
    print(f"{C_RED}error:{C_RESET} {msg}", file=sys.stderr)
    sys.exit(1)


def _request(method: str, path: str, **kwargs):
    url = f"{BASE_URL}{path}"
    try:
        r = httpx.request(method, url, timeout=TIMEOUT, **kwargs)
    except httpx.ConnectError:
        _die(f"cannot connect to Rasengan at {BASE_URL}")
    except httpx.TimeoutException:
        _die(f"request timed out ({TIMEOUT}s)")
    if r.status_code >= 400:
        body = r.text[:300] if r.text else "(empty)"
        _die(f"HTTP {r.status_code} from {method} {path}: {body}")
    return r


def _get(path: str, **params):
    return _request("GET", path, params=params).json()


def _post(path: str, payload: dict):
    return _request("POST", path, json=payload)


def _patch(path: str):
    return _request("PATCH", path)


def _delete(path: str):
    return _request("DELETE", path)

# ── Display formatters ───────────────────────────────────────────────────────

def _ts(iso: str) -> str:
    """Format an ISO timestamp to a compact local string."""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso[:19] if iso else "?"


def fmt_event(ev: dict):
    eid = ev.get("id", "?")
    etype = ev.get("event_type", "?")
    source = ev.get("source", "?")
    ts = _ts(ev.get("created_at", ""))
    payload = ev.get("payload", {})
    payload_str = json.dumps(payload) if payload else ""

    print(
        f"  {C_DIM}#{eid}{C_RESET}  "
        f"{C_CYAN}{etype}{C_RESET}  "
        f"{C_YELLOW}{source}{C_RESET}  "
        f"{C_DIM}{ts}{C_RESET}"
    )
    if payload_str and payload_str != "{}":
        print(f"       {C_DIM}{payload_str}{C_RESET}")


def fmt_rule(rule: dict):
    rid = rule.get("id", "?")
    name = rule.get("name", "?")
    etype = rule.get("event_type", "*")
    enabled = rule.get("enabled", False)
    tag = f"{C_GREEN}ON{C_RESET}" if enabled else f"{C_RED}OFF{C_RESET}"
    cooldown = rule.get("cooldown_seconds", 0)
    action = rule.get("action", {})
    atype = action.get("type", "?")

    print(
        f"  {C_DIM}#{rid}{C_RESET}  "
        f"[{tag}]  "
        f"{C_BOLD}{name}{C_RESET}  "
        f"{C_CYAN}{etype}{C_RESET}  "
        f"→ {C_MAGENTA}{atype}{C_RESET}"
        + (f"  {C_DIM}cooldown={cooldown}s{C_RESET}" if cooldown else "")
    )


def fmt_execution(ex: dict):
    eid = ex.get("id", "?")
    rule_id = ex.get("rule_id", "?")
    etype = ex.get("event_type", "?")
    success = ex.get("success", False)
    ts = _ts(ex.get("created_at", ""))
    status = f"{C_GREEN}OK{C_RESET}" if success else f"{C_RED}FAIL{C_RESET}"

    print(
        f"  {C_DIM}#{eid}{C_RESET}  "
        f"rule={C_BOLD}{rule_id}{C_RESET}  "
        f"{C_CYAN}{etype}{C_RESET}  "
        f"[{status}]  "
        f"{C_DIM}{ts}{C_RESET}"
    )

# ── Command handlers ─────────────────────────────────────────────────────────

def cmd_status(_args):
    data = _get("/status")
    status = data.get("status", "unknown")
    color = C_GREEN if status == "operational" else C_RED
    print(f"\n{C_BOLD}Rasengan{C_RESET}  [{color}{status}{C_RESET}]")
    print(f"  events: {C_BOLD}{data.get('recent_event_count', 0)}{C_RESET}")

    sources = data.get("sources", {})
    if sources:
        print(f"\n  {C_BOLD}Sources:{C_RESET}")
        for src, count in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"    {C_YELLOW}{src}{C_RESET}: {count}")

    types = data.get("event_types", {})
    if types:
        print(f"\n  {C_BOLD}Event Types:{C_RESET}")
        for t, count in sorted(types.items(), key=lambda x: -x[1]):
            print(f"    {C_CYAN}{t}{C_RESET}: {count}")
    print()


def cmd_events(args):
    params = {}
    if args.type:
        params["event_type"] = args.type
    if args.source:
        params["source"] = args.source
    params["limit"] = args.limit

    events = _get("/events", **params)
    if not events:
        print(f"{C_DIM}no events found{C_RESET}")
        return

    print(f"\n{C_BOLD}Events{C_RESET} ({len(events)} shown):\n")
    for ev in events:
        fmt_event(ev)
    print()


def cmd_resume(_args):
    data = _get("/resume")
    print(f"\n{C_BOLD}Context Resume{C_RESET}  {C_DIM}{_ts(data.get('generated_at', ''))}{C_RESET}\n")

    git = data.get("git", {})
    if git:
        print(f"  {C_BOLD}Git:{C_RESET}")
        print(f"    branch: {C_CYAN}{git.get('branch', '?')}{C_RESET}")
        print(f"    last:   {git.get('last_commit', '?')}")
        dirty = git.get("dirty_files", 0)
        if dirty:
            print(f"    dirty:  {C_YELLOW}{dirty} files{C_RESET}")

    sharingan = data.get("sharingan", {})
    if sharingan:
        print(f"\n  {C_BOLD}Sharingan:{C_RESET} {sharingan.get('total_scrolls', 0)} scrolls")
        for s in sharingan.get("recent", []):
            print(
                f"    {C_MAGENTA}{s.get('name', '?')}{C_RESET}  "
                f"{C_DIM}{s.get('level', '?')}{C_RESET}  "
                f"{s.get('domain', '')}"
            )

    deploys = data.get("deploys", {})
    services = deploys.get("services", {})
    if services:
        print(f"\n  {C_BOLD}Deploys:{C_RESET}")
        for svc, info in services.items():
            last_event = info.get("last_event", "?")
            if "completed" in last_event:
                status_color = C_GREEN
                status_icon = "OK"
            elif "failed" in last_event:
                status_color = C_RED
                status_icon = "FAIL"
            else:
                status_color = C_YELLOW
                status_icon = "..."
            dur = info.get("duration_seconds")
            dur_str = f" ({dur}s)" if dur is not None else ""
            print(
                f"    {C_BOLD}{svc}{C_RESET}  "
                f"[{status_color}{status_icon}{C_RESET}]  "
                f"{C_DIM}{_ts(info.get('last_at', ''))}{dur_str}{C_RESET}"
            )

    recent = data.get("recent_events", [])
    if recent:
        print(f"\n  {C_BOLD}Recent Events:{C_RESET}")
        for ev in recent:
            fmt_event(ev)
    print()


def cmd_emit(args):
    payload = {}
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except json.JSONDecodeError as e:
            _die(f"invalid JSON payload: {e}")

    body = {"event_type": args.type, "source": args.source, "payload": payload}
    r = _post("/events", body)
    ev = r.json()
    print(f"{C_GREEN}emitted{C_RESET} #{ev.get('id', '?')}  {C_CYAN}{args.type}{C_RESET}")


def cmd_rules(args):
    sub = args.rules_cmd or "list"

    if sub == "list":
        rules = _get("/rules")
        if not rules:
            print(f"{C_DIM}no rules defined{C_RESET}")
            return
        print(f"\n{C_BOLD}Rules{C_RESET} ({len(rules)}):\n")
        for r in rules:
            fmt_rule(r)
        print()

    elif sub == "add":
        if not args.json_str:
            _die("usage: rules add '<json>'")
        try:
            rule_data = json.loads(args.json_str)
        except json.JSONDecodeError as e:
            _die(f"invalid JSON: {e}")
        r = _post("/rules", rule_data)
        rule = r.json()
        print(f"{C_GREEN}created{C_RESET} rule #{rule.get('id', '?')}  {C_BOLD}{rule.get('name', '?')}{C_RESET}")

    elif sub == "toggle":
        if not args.rule_id:
            _die("usage: rules toggle <id>")
        r = _patch(f"/rules/{args.rule_id}/toggle")
        rule = r.json()
        state = f"{C_GREEN}enabled{C_RESET}" if rule.get("enabled") else f"{C_RED}disabled{C_RESET}"
        print(f"rule #{args.rule_id} {state}")

    elif sub == "delete":
        if not args.rule_id:
            _die("usage: rules delete <id>")
        _delete(f"/rules/{args.rule_id}")
        print(f"{C_GREEN}deleted{C_RESET} rule #{args.rule_id}")

    elif sub == "log":
        if args.rule_id:
            execs = _get(f"/rules/{args.rule_id}/executions", limit=args.limit)
        else:
            execs = _get("/rules/executions/recent", limit=args.limit)
        if not execs:
            print(f"{C_DIM}no executions found{C_RESET}")
            return
        print(f"\n{C_BOLD}Execution Log{C_RESET} ({len(execs)}):\n")
        for ex in execs:
            fmt_execution(ex)
        print()


def cmd_deploy(args):
    service = args.service

    if not service:
        # List known services
        print(f"\n{C_BOLD}Deploy Registry{C_RESET}:\n")
        for svc, script in sorted(DEPLOY_REGISTRY.items()):
            exists = os.path.isfile(script)
            tag = f"{C_GREEN}found{C_RESET}" if exists else f"{C_RED}missing{C_RESET}"
            print(f"  {C_BOLD}{svc}{C_RESET}  [{tag}]  {C_DIM}{script}{C_RESET}")
        print()
        return

    if service not in DEPLOY_REGISTRY:
        _die(f"unknown service '{service}'. Known: {', '.join(DEPLOY_REGISTRY)}")

    script = DEPLOY_REGISTRY[service]
    if not os.path.isfile(script):
        _die(f"deploy script not found: {script}")

    if args.dry:
        print(f"{C_YELLOW}[dry run]{C_RESET} Would run: rasengan-deploy {service} {script}")
        return

    deploy_hook = os.path.expanduser("~/.local/bin/rasengan-deploy")
    if not os.path.isfile(deploy_hook):
        # Fallback to script dir
        deploy_hook = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy-hook.sh")
    if not os.path.isfile(deploy_hook):
        _die("rasengan-deploy not found. Run install-hooks.sh first.")

    print(f"{C_BOLD}Deploying {service}{C_RESET} via rasengan-deploy...\n")
    result = subprocess.run([deploy_hook, service, script])
    sys.exit(result.returncode)


def cmd_ci(args):
    params = {"limit": args.limit}

    if args.git and not args.deploy:
        params["event_type_prefix"] = "git."
    elif args.deploy and not args.git:
        params["event_type_prefix"] = "deploy."
    else:
        # Both git + deploy — fetch both via prefix, merge
        # Use a broad enough approach: get git. and deploy. separately
        git_events = _get("/events", event_type_prefix="git.", limit=args.limit)
        deploy_events = _get("/events", event_type_prefix="deploy.", limit=args.limit)
        all_events = git_events + deploy_events
        all_events.sort(key=lambda e: e.get("created_at", ""), reverse=True)
        all_events = all_events[:args.limit]

        if not all_events:
            print(f"{C_DIM}no CI/CD events found{C_RESET}")
            return

        print(f"\n{C_BOLD}CI/CD Events{C_RESET} ({len(all_events)} shown):\n")
        for ev in all_events:
            fmt_event(ev)
        print()
        return

    events = _get("/events", **params)
    if not events:
        print(f"{C_DIM}no CI/CD events found{C_RESET}")
        return

    label = "Git" if args.git else "Deploy" if args.deploy else "CI/CD"
    print(f"\n{C_BOLD}{label} Events{C_RESET} ({len(events)} shown):\n")
    for ev in events:
        fmt_event(ev)
    print()


async def cmd_tail(args):
    import websockets

    ws_url = BASE_URL.replace("http://", "ws://").replace("https://", "wss://")
    ws_url += "/ws/feed"

    print(f"{C_BOLD}Tailing Rasengan{C_RESET}  {C_DIM}{ws_url}{C_RESET}")
    if args.type or args.source:
        filters = []
        if args.type:
            filters.append(f"type={args.type}")
        if args.source:
            filters.append(f"source={args.source}")
        print(f"  filter: {', '.join(filters)}")
    print(f"  {C_DIM}Ctrl+C to stop{C_RESET}\n")

    try:
        async with websockets.connect(ws_url) as ws:
            async for msg in ws:
                try:
                    ev = json.loads(msg)
                except json.JSONDecodeError:
                    continue

                # Client-side filtering
                if args.type and ev.get("event_type") != args.type:
                    continue
                if args.source and ev.get("source") != args.source:
                    continue

                fmt_event(ev)
    except KeyboardInterrupt:
        print(f"\n{C_DIM}stopped{C_RESET}")
    except Exception as e:
        _die(f"websocket error: {e}")

# ── Argument parser ──────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="rasengan",
        description="Rasengan CLI — event hub & rules engine",
    )
    sub = p.add_subparsers(dest="command")

    # status
    sub.add_parser("status", help="System health + activity summary")

    # events
    ev = sub.add_parser("events", help="Query event history")
    ev.add_argument("--type", "-t", help="Filter by event_type")
    ev.add_argument("--source", "-s", help="Filter by source")
    ev.add_argument("--limit", "-n", type=int, default=20, help="Max results (default 20)")

    # resume
    sub.add_parser("resume", help="Context recovery snapshot")

    # emit
    em = sub.add_parser("emit", help="Fire an event")
    em.add_argument("type", help="Event type (e.g. test.cli)")
    em.add_argument("source", help="Source name (e.g. cli)")
    em.add_argument("payload", nargs="?", default=None, help="JSON payload (optional)")

    # rules
    ru = sub.add_parser("rules", help="Manage rules engine")
    ru.add_argument("rules_cmd", nargs="?", default="list",
                     choices=["list", "add", "toggle", "delete", "log"],
                     help="Subcommand (default: list)")
    ru.add_argument("json_str", nargs="?", default=None, help="JSON for add, or rule ID")
    ru.add_argument("rule_id", nargs="?", default=None, help="Rule ID for toggle/delete/log")
    ru.add_argument("--limit", "-n", type=int, default=20, help="Limit for log")

    # deploy
    dp = sub.add_parser("deploy", help="Run deploy scripts with event tracking")
    dp.add_argument("service", nargs="?", default=None, help="Service to deploy (omit to list)")
    dp.add_argument("--dry", action="store_true", help="Dry run — show what would execute")

    # ci
    ci = sub.add_parser("ci", help="View git + deploy events")
    ci.add_argument("--git", action="store_true", help="Only git events")
    ci.add_argument("--deploy", action="store_true", help="Only deploy events")
    ci.add_argument("--limit", "-n", type=int, default=20, help="Max results (default 20)")

    # tail
    ta = sub.add_parser("tail", help="Live event stream (WebSocket)")
    ta.add_argument("--type", "-t", help="Filter by event_type")
    ta.add_argument("--source", "-s", help="Filter by source")

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Handle rules subcommand ID parsing — json_str doubles as rule_id for toggle/delete/log
    if args.command == "rules" and args.rules_cmd in ("toggle", "delete", "log"):
        if args.json_str and not args.rule_id:
            args.rule_id = args.json_str
            args.json_str = None

    handlers = {
        "status": cmd_status,
        "events": cmd_events,
        "resume": cmd_resume,
        "emit": cmd_emit,
        "rules": cmd_rules,
        "deploy": cmd_deploy,
        "ci": cmd_ci,
    }

    if args.command == "tail":
        try:
            asyncio.run(cmd_tail(args))
        except KeyboardInterrupt:
            print(f"\n{C_DIM}stopped{C_RESET}")
    elif args.command in handlers:
        handlers[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
