# The ansys MCP server: tools, jobs, preflight and licence

Open this before your first `ansys` tool call. The session design built on
these tools is in `persistent-session.md`.

## How the server runs your code

The `ansys` MCP server (`ansys-agent/ansys_mcp_server.py`) is a thin runner. It
writes your Python **source text** to a file and runs it with the ansys-agent
venv python (`ansys-geometry-core` 0.15.5, `ansys-fluent-core` 0.41.0,
`psutil`, `numpy`, `pyvista` 0.48.4, `vtk`, `matplotlib` 3.11.1, `Pillow`).
Every call is a **new** Python process. No state persists between calls, which
is why the SpaceClaim session lives in one long job and every step connects to
it.

Hermes exposes the tools as `mcp_ansys_<name>` or `mcp__ansys__<name>`. Match on
the suffix.

| Tool | Arguments (exact names) | Returns | Use it for |
|---|---|---|---|
| `run_ansys_script` | `script_text` (required), `script_name`, `timeout_seconds` (default 3600) | `exit_code`, `stdout`, `stderr`, `script_path`, `duration_seconds` | preflight, step scripts under about 60 s, pure-Python steps, syntax checks |
| `submit_ansys_job` | `script_text` (required), `job_name`, `cwd` | `job_id`, `job_dir`, `state`, `runner_pid`, `cwd`, `stdout_log`, `stderr_log` | the session holder; any step over about 60 s |
| `job_status` | `job_id`, `tail_lines` (default 30), `wait_seconds` (default 0, capped at 60) | `state`, `exit_code`, `elapsed_seconds`, `stdout_tail`, `stderr_tail` | polling |
| `job_log` | `job_id`, `stream` ("stdout" or "stderr"), `max_chars` | `text`, `truncated`, `total_chars` | whole logs |
| `job_cancel` | `job_id` | `state` "cancelled", `killed_pids` | your own job only; kills the whole process tree (`taskkill /F /T`), including the SpaceClaim the holder launched |
| `job_list` | `limit` | newest-first rows | finding a job after a lost call |
| `read_json_file` | `file_path` (absolute) | parsed JSON or `{"error": ...}` | `cad_report.json`, `session.json`, step JSON, `tag_report.json` |

## Transport facts (read in the server source)

1. **`run_ansys_script` blocks, and the transport gives up first.** Hermes gives
   the server about 180 s per call. Keep steps under 60 s. A timed-out call does
   not stop the script: check the step's JSON file before rerunning.
2. **`run_ansys_script` runs with `cwd` = the folder of `ansys_mcp_server.py`**,
   the ansys-agent source folder inside OneDrive (`PROJECT_ROOT`). The script
   file itself is saved under `<ANSYS_RUNTIME_DIR>\scripts`. So every step starts
   with `os.chdir(STAGE)` and uses absolute paths.
3. **`submit_ansys_job` defaults `cwd` to the same OneDrive folder.** Always pass
   `cwd=r"C:\brake-runs\<run-id>\20_spaceclaim"`. The folder must exist, or the
   tool returns `{"error": "cwd does not exist: ..."}`.
4. **Jobs are detached.** They survive the MCP server restarting. The job folder
   (`job_dir`) holds `script.py`, `meta.json`, `stdout.log`, `stderr.log`,
   `child_pid.txt` and `exit_code.txt`. Record the holder's `job_id`.
5. **`wait_seconds` above 60 is capped**, and 90 once lost the call. Use 45 to 50.

Job states come from files: `succeeded`, `failed`, `cancelled`, `running`, and
`lost` (runner gone, no exit code). `lost` is not proof of failure: read
`session.json` and check the SpaceClaim PID before anything else.

## Python rule

Never type bare `python` or `python3` in a terminal on this machine (AGENTS.md
section 5). Python for SpaceClaim work always runs through the two tools above.
A syntax check is itself a `run_ansys_script` call:
`compile(text, "holder.py", "exec")`, printing `OK` or the error.

## Preflight probe (step 2 of SKILL.md)

One short `run_ansys_script`, no `ansys.geometry` connection:

| Item | How | Pass |
|---|---|---|
| Stage folder | `os.makedirs(r"C:\brake-runs\<run-id>\20_spaceclaim", exist_ok=True)` | exists |
| No stale control files | delete `STOP` and `session.json` left from an earlier attempt of **this** run, after checking that the recorded PID is gone | none left |
| STEP hash | `hashlib.sha256` in 1 MB chunks | equals Gate 1 `step.sha256` |
| `cad_report.json` hash | same | recorded |
| Foreign Ansys processes | `psutil.process_iter(["pid", "name", "create_time"])` for `spaceclaim.exe`, `discovery.exe`, `fluent.exe`, `cx*.exe`, `cortex.exe` | none |
| Install | `os.environ.get("AWP_ROOT261")` | the v261 folder |
| Library | `importlib.metadata.version("ansys-geometry-core")` | 0.15.5; any other version: re-check `api-verified.md` in a probe first |
| Holder syntax | `compile(holder_text, "holder.py", "exec")` | OK |

If a foreign Ansys process is listed, stop and report it to the lead with PID
and start time. Never kill it.

## Licence

The Student licence allows one geometry or solver session at a time. A launch
while another SpaceClaim or Fluent is open dies with `Connection reset ... 10054`
or a licence error. Retrying in a loop does not help. The fluent-engineer cannot
start until your session is stopped and your PID is gone, so the stop step is
part of the stage, not an afterthought.

## If something hangs

- A step that hangs inside `run_ansys_script` returns after the transport limit;
  the session holder is unaffected. Read the step's JSON file, then retry once.
- A holder that is `running` with `session.json` still `ready` is normal: it is
  waiting for `STOP`.
- A modal dialog in SpaceClaim can block the API with no error. A window capture
  of your PID shows it. Only then `job_cancel` the holder, and prove the PID is
  gone.
