---
name: debug-zombies
description: Diagnose and fix zombie processes from subprocess-spawned commands
version: 1.0.0
category: debugging
args: ["[--process-name]", "[--parent-pid]"]
when_to_use: "User reports zombie processes, orphaned SSH connections, or subprocess management issues. Common in Celery, Ansible, or any system that spawns subprocesses."
tags: [debugging, processes, subprocess, ssh, celery, ansible]
---

# Debug Zombie Processes

Diagnose and fix zombie (defunct) processes, especially those spawned by subprocesses like SSH connections from Ansible, Celery tasks, or other automation tools.

## What Are Zombie Processes?

**Zombie Process**: A terminated process whose parent hasn't called `wait()` to read its exit status. Shows as `<defunct>` in `ps` output.

**Common Causes:**
- Parent process doesn't reap child processes
- Subprocess spawns children (e.g., Ansible → SSH) and doesn't wait for them
- Signal handlers not properly configured
- Process fork bombs or resource exhaustion

**Why They Matter:**
- Consume process table entries (can exhaust PID space)
- Indicate resource leaks or buggy code
- Can accumulate over time and degrade system performance

## Usage

```bash
# Diagnose zombie processes
/debug-zombies

# Filter by process name
/debug-zombies --process-name ssh

# Debug specific parent PID
/debug-zombies --parent-pid 12345
```

## Diagnostic Workflow

### Step 1: Identify Zombie Processes

```bash
# List all zombie processes
ps aux | grep defunct

# Count zombies
ps aux | grep defunct | wc -l

# Show zombies with parent info
ps -eo pid,ppid,stat,cmd | grep Z
```

**Key columns:**
- `PID`: Zombie process ID
- `PPID`: Parent process ID (who created the zombie)
- `STAT`: Process state (Z = zombie)
- `CMD`: Original command (shows as `[process] <defunct>`)

### Step 2: Identify Parent Process

```bash
# Find parent of zombie
ps -p <ZOMBIE_PID> -o ppid=

# Get parent details
ps -p <PARENT_PID> -o pid,ppid,cmd

# Full process tree
pstree -p <PARENT_PID>
```

**Common Parent Culprits:**
- Celery workers (especially with subprocess tasks)
- Ansible playbooks (SSH connection zombies)
- Shell scripts with `&` backgrounding
- Systemd services without proper cleanup

### Step 3: Analyze Parent Process Behavior

```bash
# Check if parent is still running
ps -p <PARENT_PID>

# Check parent's open files and sockets
lsof -p <PARENT_PID> | grep -E 'PIPE|FIFO|unix|TCP'

# Check parent's child processes
pgrep -P <PARENT_PID>

# Trace parent syscalls (if needed)
strace -p <PARENT_PID> -e trace=wait,waitpid 2>&1 | head -50
```

### Step 4: Root Cause Analysis

**Pattern 1: Subprocess Spawns Children Without Reaping**

Example: Celery task runs Ansible via `subprocess.run()`, Ansible spawns SSH, parent doesn't wait for grandchildren.

```python
# BAD: Doesn't reap SSH connections spawned by Ansible
subprocess.run(['ansible-playbook', 'deploy.yml'])

# GOOD: Use shell=False and wait for all descendants
subprocess.run(['ansible-playbook', 'deploy.yml'],
               check=True,
               timeout=300)
# Then explicitly reap any zombies
os.waitpid(-1, os.WNOHANG)
```

**Pattern 2: Signal Handler Interrupts wait()**

```python
# BAD: SIGCHLD handler doesn't call wait
signal.signal(signal.SIGCHLD, lambda signum, frame: None)

# GOOD: Properly reap in signal handler
def sigchld_handler(signum, frame):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except ChildProcessError:
            break

signal.signal(signal.SIGCHLD, sigchld_handler)
```

**Pattern 3: Daemonized Process Without Double Fork**

```python
# BAD: Single fork leaves zombies
if os.fork() == 0:
    os.setsid()
    subprocess.run(['long-running-task'])

# GOOD: Double fork to orphan process
if os.fork() == 0:
    os.setsid()
    if os.fork() == 0:
        subprocess.run(['long-running-task'])
    os._exit(0)  # First child exits immediately
```

### Step 5: Immediate Mitigation

**Option A: Kill Parent Process** (if safe)
```bash
# Killing parent will make init (PID 1) adopt zombies and reap them
kill <PARENT_PID>

# Or send SIGCHLD to force parent to reap
kill -SIGCHLD <PARENT_PID>
```

**Option B: Restart Service** (if parent is a service)
```bash
# For systemd services
sudo systemctl restart <service-name>

# For user services
systemctl --user restart <service-name>
```

**Option C: Manual Reaping** (if parent is your process)
```python
import os
# Reap all zombie children
while True:
    try:
        pid, status = os.waitpid(-1, os.WNOHANG)
        if pid == 0:
            break
        print(f"Reaped zombie: {pid}")
    except ChildProcessError:
        break
```

### Step 6: Permanent Fix

**For Python subprocess calls:**
```python
import subprocess
import signal

# Set subprocess to ignore SIGCHLD (auto-reap)
# Only works on Unix
if hasattr(signal, 'SIGCHLD'):
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

# Or use context manager for cleanup
from contextlib import contextmanager

@contextmanager
def subprocess_cleanup():
    processes = []
    try:
        yield processes
    finally:
        for proc in processes:
            proc.wait()
        # Reap any remaining zombies
        while True:
            try:
                os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
```

**For Celery tasks:**
```python
from celery import Task
import os

class SubprocessTask(Task):
    def after_return(self, *args, **kwargs):
        # Reap any zombie children after task completes
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
            except ChildProcessError:
                break
```

**For Ansible in subprocess:**
```python
import subprocess
import os

def run_ansible_playbook(playbook_path):
    # Use preexec_fn to set process group (Unix only)
    proc = subprocess.Popen(
        ['ansible-playbook', playbook_path],
        preexec_fn=os.setpgrp,  # Create new process group
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    try:
        stdout, stderr = proc.communicate(timeout=300)
    finally:
        # Kill entire process group (including SSH children)
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

        # Reap zombies
        while True:
            try:
                os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
```

## Common Scenarios

### Scenario 1: Celery + Ansible SSH Zombies

**Symptom:** Hundreds of `[ssh] <defunct>` processes after running Celery tasks that call Ansible.

**Root Cause:** Ansible spawns SSH connections as subprocesses. Celery worker doesn't wait for Ansible's grandchildren.

**Fix:**
```python
# In Celery task
from celery.signals import task_postrun
import os

@task_postrun.connect
def cleanup_zombies(sender=None, **kwargs):
    """Reap zombie processes after each task"""
    count = 0
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            count += 1
        except ChildProcessError:
            break
    if count > 0:
        print(f"Reaped {count} zombie process(es)")
```

### Scenario 2: Shell Script Backgrounding

**Symptom:** Zombies after running shell script with `command &`.

**Root Cause:** Parent shell doesn't wait for backgrounded processes.

**Fix:**
```bash
#!/bin/bash
# BAD
for host in $HOSTS; do
    ssh $host "command" &
done

# GOOD
for host in $HOSTS; do
    ssh $host "command" &
done
wait  # Wait for all background jobs
```

### Scenario 3: Docker Container Zombies

**Symptom:** Zombies accumulate in container.

**Root Cause:** Container init process (PID 1) doesn't reap orphaned processes.

**Fix:**
```dockerfile
# Use tini as init system
RUN apt-get update && apt-get install -y tini
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["your-application"]
```

## Monitoring & Prevention

**Continuous Monitoring:**
```bash
# Add to cron (check every hour)
0 * * * * ps aux | grep defunct | wc -l > /var/log/zombie_count.log

# Alert if zombies exceed threshold
if [ $(ps aux | grep defunct | wc -l) -gt 10 ]; then
    echo "High zombie count detected" | mail -s "Zombie Alert" admin@example.com
fi
```

**Preventive Measures:**
1. Always call `wait()` or `waitpid()` for child processes
2. Set `SIGCHLD` handler to auto-reap if appropriate
3. Use process groups for subprocess hierarchies
4. Test subprocess cleanup in unit tests
5. Monitor zombie count in production

## Output Format

```
🧟 Zombie Process Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Zombies: 16

Process Breakdown:
  ├─ ssh (defunct): 14 processes
  │   └─ Parent: celery [worker] (PID 12345)
  ├─ ansible (defunct): 2 processes
  │   └─ Parent: celery [worker] (PID 12345)

Root Cause Analysis:
  ⚠️  Celery worker (PID 12345) spawns Ansible via subprocess
  ⚠️  Ansible spawns SSH connections that aren't reaped
  ⚠️  No SIGCHLD handler or waitpid() calls in parent

Recommended Fix:
  1. Add task_postrun signal handler to reap zombies
  2. Use os.waitpid(-1, os.WNOHANG) after Ansible calls
  3. Consider using Ansible Python API instead of subprocess

Immediate Mitigation:
  sudo systemctl restart celery-worker
  # Or: kill -SIGCHLD 12345
```

## Related Skills

- `/db-health-check` - Check for zombie processes affecting database connections
- Plugin development guides - Proper subprocess handling in plugins

---

## 🧠 Learnings (Auto-Updated)

### 2026-01-05 Initial - Pattern
**Signal:** "Diagnosed and fixed 16 zombie SSH processes from Celery + Ansible"
**What Changed:** Created skill based on real-world debugging pattern
**Confidence:** High
**Source:** 2026-01-01-zombie-fix
**Rationale:** Recurring pattern in subprocess management worth documenting
