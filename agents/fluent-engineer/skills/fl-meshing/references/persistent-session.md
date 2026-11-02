# The persistent Fluent session: one launch, short steps, long jobs

Open this before the first Ansys call of Gate 3. It replaces the old pattern of
one 700-line script per attempt, which is what cost run 1 about 25 SpaceClaim
relaunches in 60 minutes. Every API name here is in `api-verified.md` with its
label.

## Why

- Each `run_ansys_script` and `submit_ansys_job` is a **new Python process**. A
  monolithic script that fails at line 480 throws away the launch (1 to 2 min),
  the import and every step before it, and the next attempt pays them again.
- A Fluent session that stays up keeps its state on the server: the imported
  PMDB, the workflow tasks, the mesh, the settings. A short script that fails
  costs 10 to 20 seconds and changes nothing it did not reach.
- One launch also means one licence use, one GUI window for the user, and one
  transcript.

## Files, all under `C:\brake-runs\<run-id>\30_fluent\session\`

| File | Written by | Content |
|---|---|---|
| `server_info.txt` | host job | line 1 `ip:port`, line 2 password |
| `session.json` | host job | Fluent PIDs, version, processor count, launch time, idle-timeout preference |
| `STOP` | you, at the very end | empty file; the host exits Fluent when it appears |
| `steps.jsonl` | you | one line per step: step name, job or script id, start, end, ok |

## 1. The host job (the only launch)

Submit once: `submit_ansys_job(script_text=HOST, job_name="<run-id>_fluent_host",
cwd=r"C:\brake-runs\<run-id>\30_fluent")`. The host launches Fluent Meshing with
the GUI visible, writes the two files, **detaches its own client**, and then
only watches for `STOP` and for Fluent dying. It never sends Fluent a command
while it idles, so only one client talks to Fluent at a time.

API idiom - launch and publish (SRC):
```python
S = pathlib.Path(r"C:\brake-runs\<run-id>\30_fluent\session"); S.mkdir(parents=True, exist_ok=True)
m = pyfluent.launch_fluent(mode="meshing", precision="double", dimension=3,
        processor_count=4, ui_mode="gui", cwd=str(S.parent), product_version="26.1.0",
        cleanup_on_exit=False, start_transcript=False, start_timeout=300)
cp = m.connection_properties
(S / "server_info.txt").write_text(f"{cp.ip}:{cp.port}\n{cp.password}\n")
pids = [p for p in (cp.fluent_host_pid, cp.cortex_pid) if p]
try: idle = m.preferences.General.IdleTimeout()          # UNVERIFIED; must not kill the host
except Exception as e: idle = f"unread: {e}"[:80]
(S / "session.json").write_text(json.dumps({"pids": pids, "version": str(m.get_fluent_version()),
        "processor_count": 4, "idle_timeout_pref": idle}))
m.exit()                      # cleanup_on_exit=False: closes this client, Fluent stays up
print("READY", pids, flush=True)
```

API idiom - idle and stop (SRC; psutil is in the venv):
```python
while not (S / "STOP").exists():
    if not any(psutil.pid_exists(p) for p in pids):
        print("FLUENT GONE", flush=True); raise SystemExit(3)
    time.sleep(10)
s = pyfluent.connect_to_fluent(server_info_file_name=str(S / "server_info.txt"), start_transcript=False)
try: s.application_runtime.exit()
except Exception as e: print("exit call:", e, flush=True)
for _ in range(60):
    if not any(psutil.pid_exists(p) for p in pids): break
    time.sleep(2)
print("STOPPED alive=", [p for p in pids if psutil.pid_exists(p)], flush=True)
```
If PIDs survive, the host calls `s.force_exit()` and prints the survivors again.

Poll the host only to see `READY` (about 1 to 3 min after submit), and once at
the very end to see `STOPPED`. Do not poll it in between.

## 2. Short steps (20 to 80 lines each, `run_ansys_script`)

One step does one thing: import, or local sizing, or the surface mesh, or the
materials, and so on. Skeleton (SRC):
```python
import json, ansys.fluent.core as pyfluent
SI = r"C:\brake-runs\<run-id>\30_fluent\session\server_info.txt"
s = pyfluent.connect_to_fluent(server_info_file_name=SI, start_transcript=False)
out = {"step": "<name>", "mode": type(s).__name__}
try:
    pass   # ONE step, then measure what it changed
    out["ok"] = True
except Exception as e:
    out.update(ok=False, error=f"{type(e).__name__}: {e}"[:400])
finally:
    s.exit()               # detach; never cleanup_on_exit=True
print(json.dumps(out))
```

Rules:
- Print **compact JSON** only: the measured numbers and `ok`. No transcripts.
- Absolute paths only. `run_ansys_script` runs in the ansys-agent source folder.
- Before submitting any script, compile it: `compile(text, "step", "exec")` in
  `execute_code`, or `C:/solidpilot/.venv/Scripts/python.exe -m py_compile <file>`.
  A `SyntaxError` found after a launch costs a launch.
- Use only names from `api-verified.md`. For anything else, run a probe step
  first (section 11 of that sheet).
- A step that changes state is **not** re-run blindly after a failure. Run a
  read-only step that inspects the state, then decide.

## 3. Long jobs (`submit_ansys_job`, connect to the same session)

Anything that can pass 2 minutes: the volume mesh (with write, switch to solver
and read-back), and the transient solve. The job connects with
`connect_to_fluent(server_info_file_name=SI)`, does its work, prints one
progress line per window with `flush=True`, writes its own JSON, and ends with
`s.exit()`. Fluent stays up for the next step.

While a long job runs, **run no step script**: one client at a time.

## 4. Waiting without burning turns

- `job_status(job_id, tail_lines=12, wait_seconds=60)`: 60 s is the server cap.
  Each call is one turn per minute. Do not add other calls between polls.
- For waits of several minutes (the solve), one `run_ansys_script` that sleeps
  and returns when the job ends or after 240 s is one turn per 4 minutes
  (Hermes allows 300 s for the `ansys` server; UNVERIFIED in practice, harmless
  if it times out because it only reads files). Use the `job_dir` returned by
  `submit_ansys_job`:
```python
import os, time, json
d = r"<job_dir>"; t0 = time.time()
while time.time() - t0 < 240 and not os.path.exists(os.path.join(d, "exit_code.txt")):
    time.sleep(10)
tail = open(os.path.join(d, "stdout.log"), encoding="utf-8", errors="replace").read().splitlines()[-6:]
print(json.dumps({"ended": os.path.exists(os.path.join(d, "exit_code.txt")), "waited_s": round(time.time() - t0), "tail": tail}))
```
- Expected durations on this machine (4 processes): volume mesh 1 to 3 min;
  solve 11 to 15 min. Plan the number of polls from these; a solve needs about
  4 long waits, not 15 short polls.

## 5. Launch budget and failure paths

- **1 Fluent launch per stage.** A 2nd launch needs a written reason in
  `mesh_report.json.session.relaunch_reason` (for example "host job state
  failed: FLUENT GONE at 12:41, transcript shows ..."). **Never a 3rd**: stop and
  return to the lead with both reasons.
- If `connect_to_fluent` fails at the first probe (the UNVERIFIED part of this
  pattern), do not loop. Stop the host (`STOP`), record the error, and use the
  one allowed relaunch for a single `submit_ansys_job` that runs the remaining
  mesh steps, `switch_to_solver()` and the measurements in one process (the
  predecessor's RUN pattern). Record it as the relaunch reason.
- If the host prints `FLUENT GONE`, inspect `30_fluent` (mesh file, transcript
  tail) before anything else. Resume from the last artifact on disk with the one
  relaunch; never replay steps whose output already exists.
- `job_cancel` on the host kills its process tree, and Fluent is in that tree.
  Use it only as the emergency stop, after `STOP` failed.
- After `STOPPED`, count `fluent.exe` and `cx*.exe` processes you own; record
  the count in the final report. A survivor holds the Student licence.

## 6. Timing record

Keep `started_at`, `finished_at`, `tool_calls` (approximate) and `app_launches`
(Fluent sessions started) for the stage, and copy them as `timing` into
`mesh_report.json`, `setup_report.json` and `results.json` (specs/handoffs.md).
