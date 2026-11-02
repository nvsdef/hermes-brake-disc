# One SpaceClaim session, many short step scripts

Open this before step 3 of SKILL.md. It is the fix for run 1, where every
attempt was a 700 to 1 100 line script that launched SpaceClaim, crashed on one
line, and launched again: about 25 launches in 60 minutes, and the stage never
passed. Every call here is on the verified sheet (`api-verified.md`).

## The pattern

| Piece | Tool | Lives | Does |
|---|---|---|---|
| Session holder | `submit_ansys_job`, `cwd` = stage folder | the whole stage | launches SpaceClaim once (visible), writes `session.json`, sleeps until `STOP` exists, then closes SpaceClaim |
| Step script | `run_ansys_script` (under 60 s) or `submit_ansys_job` (longer) | seconds | connects to the port, does **one** step, prints one compact JSON line, writes its JSON file, disconnects without closing |
| Pure-Python step | `run_ansys_script` | seconds | works on JSON or `.npz` files only (screenshots, `tag_report.json`); no connection at all |

A crash in a step costs the seconds of that step. SpaceClaim, the imported
design and every named selection stay alive in the session holder.

## Session holder (launch #1)

API idiom (part 1, launch and publish):

```python
import json, time, logging, psutil
from pathlib import Path
from ansys.geometry.core import launch_modeler_with_spaceclaim
STAGE = Path(r"C:\brake-runs\<run-id>\20_spaceclaim")
def sc_pids(): return {p.pid for p in psutil.process_iter(["name"]) if (p.info["name"] or "").lower() == "spaceclaim.exe"}
before = sc_pids()
m = launch_modeler_with_spaceclaim(version=261, hidden=False, transport_mode="wnua",
        server_working_dir=str(STAGE), client_log_level=logging.WARNING, timeout=150)
host, port = m.client.get_name().split(":")
new = sorted(sc_pids() - before)
info = {"state": "ready", "host": host, "port": int(port), "transport_mode": "wnua",
        "pid": new[0] if len(new) == 1 else None, "backend_version": str(m.client.backend_version),
        "launched_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
(STAGE / "session.json").write_text(json.dumps(info, indent=1)); print(json.dumps(info), flush=True)
```

API idiom (part 2, hold and release):

```python
t0 = time.time()
try:
    while not (STAGE / "STOP").exists() and time.time() - t0 < 5400:
        if info["pid"] and not psutil.pid_exists(info["pid"]):
            info["state"] = "died"; break
        time.sleep(5)
finally:
    m.close()                    # launch process ONLY: server shutdown + SIGTERM to its PID
    if info["state"] != "died": info["state"] = "closed"
    info["closed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (STAGE / "session.json").write_text(json.dumps(info, indent=1))
```

Rules:

- Before submitting, syntax-check the holder text once with
  `run_ansys_script` running `compile(text, "holder.py", "exec")`. The holder is
  the only script whose crash costs a launch.
- `pid` must be one new PID. If it is `None`, stop and report: you cannot prove
  which process is yours.
- The 5 400 s ceiling (90 min) means a forgotten session releases the licence
  by itself.
- Wait for `session.json` with `job_status(job_id, wait_seconds=45)` and
  `read_json_file`. Boot takes 30 to 60 s. `state` = `ready` is done.
- Record the holder `job_id`. It is your only handle for `job_cancel`.

## Step script

API idiom (the frame of every step; the middle is the step):

```python
import json, os, time
from pathlib import Path
from ansys.geometry.core import Modeler
STAGE = Path(r"C:\brake-runs\<run-id>\20_spaceclaim"); os.chdir(STAGE)
s = json.loads((STAGE / "session.json").read_text())
m = Modeler(host=s["host"], port=s["port"], transport_mode=s["transport_mode"], timeout=20)
with open(STAGE / "connects.log", "a") as f: f.write(time.strftime("%H:%M:%S") + " S5_signatures\n")
try:
    design = m.read_existing_design()
    out = {"step": "S5_signatures"}          # ... one step, results into out ...
    (STAGE / "s5_signatures.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out)[:3000], flush=True)
finally:
    m.client.close()                          # NEVER m.close() / m.exit(): they close the design
```

Rules:

- `os.chdir(STAGE)` first. `run_ansys_script` runs with the working directory
  of the ansys-agent source folder, which is inside OneDrive.
- 20 to 80 lines per step. If a step needs more, it is two steps.
- One compact JSON line on stdout, truncated to about 3 000 characters. The full
  result goes to the step's JSON file in the stage folder.
- Each step re-reads the design and re-identifies what it needs **by measured
  signature**. Python objects never cross a step, and ids are re-checked, not
  trusted (they change after a deletion).
- A step that mutates (delete, name, export) checks the state first and is
  safe to rerun: if the calliper is already gone, it proves the deletion instead
  of deleting again; if a selection name exists, it deletes it and recreates it.
- Over about 60 s (the face snapshot can be): submit the same step with
  `submit_ansys_job` and `cwd`. It still only connects.
- `connects.log` gives `session.connect_calls` for `tag_report.json`.

## Stop

Write `20_spaceclaim\STOP` from a pure-Python `run_ansys_script`. Poll the holder
until `succeeded`. Read `session.json`: `state` = `closed`. Then prove with
`psutil.pid_exists(pid)` that the PID is gone; if it survives 30 s, terminate
**that PID only** and record it.

## Launch budget

| Launches | When | Required |
|---|---|---|
| 1 | always | the holder above |
| 2 | only if SpaceClaim died (`state` = `died`, PID gone) or the holder crashed before `ready` | a written reason in `tag_report.json` `session.relaunch_reason`, and the second launch restarts from the import step |
| 3 | never | HALT: stop and return both failures to the lead |

A step-script crash is **not** a reason to relaunch. It is a code error: fix
the step and rerun it. Crash budget: 3 reruns per step, 12 per stage. Beyond
that, stop and report the tracebacks.

## If connect-to-existing is refused (fallback)

The client source allows a second client (`api-verified.md` section 3). Whether
SpaceClaim's server accepts it is UNVERIFIED until step 3 of SKILL.md. If the
connect probe fails while the holder PID is alive and `session.json` is
`ready`:

1. Write `STOP`, wait for the holder to release, prove the PID is gone.
2. Build **one** job script from the step bodies you would have run, in order,
   each wrapped in its own `try/except` that writes that step's JSON with the
   exception text, and stop at the first failing gate.
3. Syntax-check the full text with `compile(...)` in a `run_ansys_script` before
   submitting. Also test every step body that needs no SpaceClaim (screenshots,
   report) on the files of earlier steps.
4. Submit it as launch #2 with `relaunch_reason` = "connect-to-existing refused:
   <error text>". Close with `modeler.close()` in `finally`.

## Timing

A clean stage: preflight 10 s, launch 30 to 60 s, about 12 steps of 5 to 60 s,
stop 15 s. Budget 8 to 12 min in total (lead plan). Record `started_at`,
`finished_at`, `tool_calls` and `app_launches` for `timing` in `tag_report.json`.
