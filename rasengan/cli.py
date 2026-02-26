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
    "dojo": "/home/ndninja/projects/ninja-dashboard/run.sh",
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


def fmt_schedule(sched: dict):
    sid = sched.get("id", "?")
    name = sched.get("name", "?")
    cron = sched.get("cron_expr", "?")
    etype = sched.get("event_type", "?")
    enabled = sched.get("enabled", False)
    tag = f"{C_GREEN}ON{C_RESET}" if enabled else f"{C_RED}OFF{C_RESET}"
    last = _ts(sched.get("last_run_at", "")) if sched.get("last_run_at") else "never"
    next_run = _ts(sched.get("next_run_at", "")) if sched.get("next_run_at") else "?"

    print(
        f"  {C_DIM}#{sid}{C_RESET}  "
        f"[{tag}]  "
        f"{C_BOLD}{name}{C_RESET}  "
        f"{C_CYAN}{cron}{C_RESET}  "
        f"→ {C_MAGENTA}{etype}{C_RESET}"
    )
    print(
        f"       {C_DIM}last: {last}  next: {next_run}{C_RESET}"
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

def fmt_pipeline(run: dict):
    job_id = run.get("job_id", "?")
    stage = run.get("current_stage", "?")
    status = run.get("status", "?")
    started = _ts(run.get("started_at", ""))
    updated = _ts(run.get("updated_at", ""))

    status_colors = {
        "active": C_CYAN, "completed": C_GREEN,
        "failed": C_RED, "stalled": C_YELLOW,
    }
    color = status_colors.get(status, C_WHITE)

    print(
        f"  {C_BOLD}{job_id[:12]}{C_RESET}  "
        f"[{color}{status.upper()}{C_RESET}]  "
        f"stage={C_MAGENTA}{stage}{C_RESET}  "
        f"{C_DIM}started={started}  updated={updated}{C_RESET}"
    )
    error = run.get("error")
    if error:
        print(f"       {C_RED}error: {error[:100]}{C_RESET}")


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


def cmd_resume(args):
    if hasattr(args, 'push') and args.push:
        result = _post("/push-targets/push", {}).json()
        targets = result.get("targets", 0)
        if targets == 0:
            print(f"{C_DIM}no push targets configured{C_RESET}")
            return
        for r in result.get("results", []):
            name = r.get("name", "?")
            res = r.get("result", {})
            if "error" in res:
                print(f"  {C_RED}FAIL{C_RESET}  {name}: {res['error']}")
            else:
                print(f"  {C_GREEN}OK{C_RESET}  {name}: {json.dumps(res)}")
        print(f"\n{C_GREEN}Pushed to {targets} target(s){C_RESET}")
        return

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

    pipes = data.get("pipelines", {})
    if pipes:
        active = pipes.get("active", [])
        stalled = pipes.get("stalled", [])
        last = pipes.get("last_completed")
        if active or stalled or last:
            print(f"\n  {C_BOLD}Pipelines:{C_RESET}")
            for p in active:
                print(
                    f"    {C_CYAN}ACTIVE{C_RESET}  "
                    f"{C_BOLD}{p['job_id'][:12]}{C_RESET}  "
                    f"stage={C_MAGENTA}{p['stage']}{C_RESET}"
                )
            for p in stalled:
                print(
                    f"    {C_YELLOW}STALLED{C_RESET}  "
                    f"{C_BOLD}{p['job_id'][:12]}{C_RESET}  "
                    f"stage={C_MAGENTA}{p['stage']}{C_RESET}"
                )
            if last:
                dur = last.get("duration_seconds")
                dur_str = f" ({dur}s)" if dur is not None else ""
                print(
                    f"    {C_GREEN}LAST OK{C_RESET}  "
                    f"{C_BOLD}{last['job_id'][:12]}{C_RESET}"
                    f"{dur_str}"
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


def cmd_schedules(args):
    sub = args.sched_cmd or "list"

    if sub == "list":
        scheds = _get("/schedules")
        if not scheds:
            print(f"{C_DIM}no schedules defined{C_RESET}")
            return
        print(f"\n{C_BOLD}Schedules{C_RESET} ({len(scheds)}):\n")
        for s in scheds:
            fmt_schedule(s)
        print()

    elif sub == "add":
        if not args.sched_name or not args.sched_cron or not args.sched_event:
            _die("usage: schedules add <name> <cron> <event_type> [--payload '{}']")
        payload = {}
        if args.sched_payload:
            try:
                payload = json.loads(args.sched_payload)
            except json.JSONDecodeError as e:
                _die(f"invalid JSON payload: {e}")
        body = {
            "name": args.sched_name,
            "cron_expr": args.sched_cron,
            "event_type": args.sched_event,
            "payload": payload,
        }
        r = _post("/schedules", body)
        sched = r.json()
        print(
            f"{C_GREEN}created{C_RESET} schedule #{sched.get('id', '?')}  "
            f"{C_BOLD}{sched.get('name', '?')}{C_RESET}"
        )

    elif sub == "toggle":
        if not args.sched_id:
            _die("usage: schedules toggle <id>")
        r = _patch(f"/schedules/{args.sched_id}/toggle")
        sched = r.json()
        state = f"{C_GREEN}enabled{C_RESET}" if sched.get("enabled") else f"{C_RED}disabled{C_RESET}"
        print(f"schedule #{args.sched_id} {state}")

    elif sub == "delete":
        if not args.sched_id:
            _die("usage: schedules delete <id>")
        _delete(f"/schedules/{args.sched_id}")
        print(f"{C_GREEN}deleted{C_RESET} schedule #{args.sched_id}")


def cmd_push_targets(args):
    sub = args.pt_cmd or "list"

    if sub == "list":
        targets = _get("/push-targets")
        if not targets:
            print(f"{C_DIM}no push targets configured{C_RESET}")
            return
        print(f"\n{C_BOLD}Push Targets{C_RESET} ({len(targets)}):\n")
        for t in targets:
            tid = t.get("id", "?")
            name = t.get("name", "?")
            ttype = t.get("type", "?")
            enabled = t.get("enabled", False)
            tag = f"{C_GREEN}ON{C_RESET}" if enabled else f"{C_RED}OFF{C_RESET}"
            config = t.get("config", {})
            dest = config.get("path") or config.get("url") or "?"
            print(
                f"  {C_DIM}#{tid}{C_RESET}  "
                f"[{tag}]  "
                f"{C_BOLD}{name}{C_RESET}  "
                f"{C_CYAN}{ttype}{C_RESET}  "
                f"→ {C_DIM}{dest}{C_RESET}"
            )
        print()

    elif sub == "add":
        if not args.pt_name or not args.pt_type or not args.pt_config:
            _die("usage: push-targets add <name> <type> '<config_json>'")
        try:
            config = json.loads(args.pt_config)
        except json.JSONDecodeError as e:
            _die(f"invalid JSON config: {e}")
        body = {"name": args.pt_name, "type": args.pt_type, "config": config}
        r = _post("/push-targets", body)
        target = r.json()
        print(f"{C_GREEN}created{C_RESET} push target #{target.get('id', '?')}  {C_BOLD}{target.get('name', '?')}{C_RESET}")

    elif sub == "toggle":
        if not args.pt_id:
            _die("usage: push-targets toggle <id>")
        r = _patch(f"/push-targets/{args.pt_id}/toggle")
        target = r.json()
        state = f"{C_GREEN}enabled{C_RESET}" if target.get("enabled") else f"{C_RED}disabled{C_RESET}"
        print(f"push target #{args.pt_id} {state}")

    elif sub == "delete":
        if not args.pt_id:
            _die("usage: push-targets delete <id>")
        _delete(f"/push-targets/{args.pt_id}")
        print(f"{C_GREEN}deleted{C_RESET} push target #{args.pt_id}")


def cmd_pipelines(args):
    sub = args.pipe_cmd or "list"

    if sub == "list":
        params = {"limit": args.limit}
        if args.pipe_status:
            params["status"] = args.pipe_status
        runs = _get("/pipelines", **params)
        if not runs:
            print(f"{C_DIM}no pipeline runs found{C_RESET}")
            return
        print(f"\n{C_BOLD}Pipeline Runs{C_RESET} ({len(runs)}):\n")
        for r in runs:
            fmt_pipeline(r)
        print()

    elif sub == "get":
        if not args.pipe_job_id:
            _die("usage: pipelines get <job_id>")
        run = _get(f"/pipelines/{args.pipe_job_id}")
        fmt_pipeline(run)
        stages = run.get("stages", [])
        if stages:
            print(f"\n  {C_BOLD}Stage History:{C_RESET}")
            for s in stages:
                entered = _ts(s.get("entered_at", ""))
                exited = _ts(s.get("exited_at", "")) if s.get("exited_at") else "..."
                print(
                    f"    {C_MAGENTA}{s['stage']:12s}{C_RESET}  "
                    f"{C_DIM}{entered} → {exited}{C_RESET}"
                )
        print()

    elif sub == "stats":
        stats = _get("/pipelines/stats")
        print(f"\n{C_BOLD}Pipeline Stats{C_RESET}:\n")
        print(f"  Runs (24h):    {C_BOLD}{stats.get('total_runs_24h', 0)}{C_RESET}")
        print(f"  Success rate:  {C_BOLD}{stats.get('success_rate_24h', 0):.0%}{C_RESET}")
        print(f"  Active:        {C_CYAN}{stats.get('active_runs', 0)}{C_RESET}")
        print(f"  Stalled:       {C_YELLOW}{stats.get('stalled_runs', 0)}{C_RESET}")
        avg = stats.get("avg_duration_seconds", {})
        if avg:
            print(f"\n  {C_BOLD}Avg Duration (7d):{C_RESET}")
            for stage, secs in avg.items():
                print(f"    {C_MAGENTA}{stage:12s}{C_RESET}  {secs:.0f}s")
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
    rs = sub.add_parser("resume", help="Context recovery snapshot")
    rs.add_argument("--push", action="store_true", help="Push resume to all configured targets")

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

    # schedules
    sc = sub.add_parser("schedules", help="Manage scheduled triggers")
    sc.add_argument("sched_cmd", nargs="?", default="list",
                     choices=["list", "add", "toggle", "delete"],
                     help="Subcommand (default: list)")
    sc.add_argument("sched_name", nargs="?", default=None, help="Schedule name (for add)")
    sc.add_argument("sched_cron", nargs="?", default=None, help="Cron expression (for add)")
    sc.add_argument("sched_event", nargs="?", default=None, help="Event type (for add)")
    sc.add_argument("--payload", dest="sched_payload", default=None, help="JSON payload (for add)")
    sc.add_argument("sched_id", nargs="?", default=None, help="Schedule ID (for toggle/delete)")

    # pipelines
    pl = sub.add_parser("pipelines", help="View pipeline run state and stats")
    pl.add_argument("pipe_cmd", nargs="?", default="list",
                     choices=["list", "get", "stats"],
                     help="Subcommand (default: list)")
    pl.add_argument("pipe_job_id", nargs="?", default=None, help="Job ID (for get)")
    pl.add_argument("--status", dest="pipe_status", default=None,
                     help="Filter: active, completed, failed, stalled")
    pl.add_argument("--limit", "-n", type=int, default=20, help="Max results (default 20)")

    # push-targets
    pt = sub.add_parser("push-targets", help="Manage resume push targets")
    pt.add_argument("pt_cmd", nargs="?", default="list",
                     choices=["list", "add", "toggle", "delete"],
                     help="Subcommand (default: list)")
    pt.add_argument("pt_name", nargs="?", default=None, help="Target name (for add)")
    pt.add_argument("pt_type", nargs="?", default=None, help="Target type: file|webhook (for add)")
    pt.add_argument("pt_config", nargs="?", default=None, help="JSON config (for add)")
    pt.add_argument("pt_id", nargs="?", default=None, help="Target ID (for toggle/delete)")

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

    # Handle schedules subcommand ID parsing — sched_name doubles as sched_id for toggle/delete
    if args.command == "schedules" and args.sched_cmd in ("toggle", "delete"):
        if args.sched_name and not args.sched_id:
            args.sched_id = args.sched_name
            args.sched_name = None

    # Handle push-targets subcommand ID parsing
    if args.command == "push-targets" and args.pt_cmd in ("toggle", "delete"):
        if args.pt_name and not args.pt_id:
            args.pt_id = args.pt_name
            args.pt_name = None

    handlers = {
        "status": cmd_status,
        "events": cmd_events,
        "resume": cmd_resume,
        "emit": cmd_emit,
        "rules": cmd_rules,
        "schedules": cmd_schedules,
        "pipelines": cmd_pipelines,
        "push-targets": cmd_push_targets,
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
