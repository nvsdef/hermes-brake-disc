"""
Ansys Agent MCP Server.

Exposes tools that let a Claude client execute Python scripts against the
local pyansys installation on this Windows machine, plus utilities for
reading results and consulting the skill reference sheets.

Setup:
  1. Install: `pip install "mcp[cli]"` in the ansys-agent venv.
  2. Register with your Claude client (.mcp.json for Claude Code,
     claude_desktop_config.json for Cowork). See INSTALL_MCP.md.
  3. Restart the client.
  4. In a new session, Claude will see the tools listed below.

SYNCHRONOUS vs BACKGROUND
-------------------------
`run_ansys_script` blocks until the script finishes. The MCP transport has its
own timeout ceiling -- well below `timeout_seconds` -- so anything longer than
a couple of minutes will return "Request timed out" even though the work keeps
running and completes. Observed with Fluent meshing: the mesh was written
correctly, but the call had already given up.

For anything long -- volume meshing, multi-step solves, parameter sweeps -- use
the job tools instead:

    submit_ansys_job(...)  ->  job_id      (returns immediately)
    job_status(job_id)     ->  state + a tail of the live log
    job_log(job_id)        ->  full stdout/stderr
    job_cancel(job_id)     ->  kill the process tree
    job_list()             ->  everything submitted

Jobs are fully detached: they survive this MCP server restarting, and they
survive the Claude session ending.

Tools exposed:
  - run_ansys_script(script_text, script_name?, timeout_seconds?)
  - submit_ansys_job(script_text, job_name?, cwd?)
  - job_status(job_id, tail_lines?, wait_seconds?)
  - job_log(job_id, stream?, max_chars?)
  - job_cancel(job_id)
  - job_list(limit?)
  - read_json_file(file_path)
  - list_case_results(results_root?)
  - read_skill_reference(skill, sheet_name)
  - list_skill_reference_sheets()
"""
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Paths.
#
# PROJECT_ROOT holds the SOURCE (this file, skills/) and is what gets shipped.
# RUNTIME_DIR holds MUTABLE state (venv, scripts, results, jobs) and should live
# outside OneDrive and outside git. When ANSYS_RUNTIME_DIR is unset they are the
# same directory, which is the historical behaviour -- nothing breaks.
# See brake-thermal-workflow/docs/PACKAGING.md.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent.resolve()
RUNTIME_DIR = Path(os.environ.get("ANSYS_RUNTIME_DIR", str(PROJECT_ROOT))).resolve()
VENV_PYTHON = Path(os.environ.get(
    "ANSYS_VENV_PYTHON", str(RUNTIME_DIR / ".venv" / "Scripts" / "python.exe")))

SCRIPTS_DIR = RUNTIME_DIR / "scripts"
RESULTS_ROOT = RUNTIME_DIR / "results"
JOBS_DIR = RUNTIME_DIR / "jobs"
SKILLS_DIR = PROJECT_ROOT / "skills"      # ships with the source, not runtime

for _d in (SCRIPTS_DIR, RESULTS_ROOT, JOBS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

IS_WIN = sys.platform == "win32"
SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")
CANCELLED_CODE = -15      # sentinel written by job_cancel

mcp = FastMCP("ansys-agent")


# ===========================================================================
# helpers
# ===========================================================================

def _win_flags(detached: bool = False) -> dict:
    if not IS_WIN:
        return {"stdin": subprocess.DEVNULL}
    flags = subprocess.CREATE_NO_WINDOW
    if detached:
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP -- outlives this server.
        flags = 0x00000008 | 0x00000200
    return {"creationflags": flags, "stdin": subprocess.DEVNULL}


def _pid_alive(pid: int) -> bool:
    """Best-effort liveness check. Only used to detect a runner that died
    without writing its exit-code sentinel."""
    if pid <= 0:
        return False
    try:
        if IS_WIN:
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not h:
                return False
            code = ctypes.c_ulong()
            ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
            ctypes.windll.kernel32.CloseHandle(h)
            return bool(ok) and code.value == 259   # STILL_ACTIVE
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _job_dir(job_id: str) -> Path:
    return JOBS_DIR / SAFE_NAME.sub("_", job_id)


def _read_meta(d: Path) -> dict:
    p = d / "meta.json"
    if not p.exists():
        return {}
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"unreadable meta.json: {e}"}


def _tail(path: Path, n: int) -> str:
    if not path.exists() or n <= 0:
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-n:])
    except Exception as e:
        return f"<could not read {path.name}: {e}>"


def _resolve(d: Path, state: dict) -> dict:
    """Determine a job's current state from files on disk, not memory."""
    ec_file = d / "exit_code.txt"
    if ec_file.exists():
        try:
            code = int(ec_file.read_text(encoding="utf-8").strip())
        except Exception:
            code = -99
        if code == 0:
            state["state"] = "succeeded"
        elif code == CANCELLED_CODE:
            state["state"] = "cancelled"
        else:
            state["state"] = "failed"
        state["exit_code"] = code
        try:
            state["finished_at"] = datetime.fromtimestamp(
                ec_file.stat().st_mtime).isoformat(timespec="seconds")
        except Exception:
            pass
        return state

    pid = int(state.get("runner_pid") or 0)
    if pid and not _pid_alive(pid):
        state["state"] = "lost"
        state["exit_code"] = None
        state["note"] = ("runner process is gone but no exit code was written -- "
                         "it was killed, or the machine restarted")
        return state

    state["state"] = "running"
    state["exit_code"] = None
    return state


# The per-job runner. Written into the job directory and launched detached.
# It exists so a real exit code is always recorded, even if this MCP server
# restarts while the job is in flight.
_RUNNER_SRC = '''\
import json, os, subprocess, sys
from datetime import datetime

JOB_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(JOB_DIR, "meta.json"), encoding="utf-8") as f:
    meta = json.load(f)

rc = -99
try:
    with open(os.path.join(JOB_DIR, "stdout.log"), "w",
              encoding="utf-8", errors="replace", buffering=1) as out, \\
         open(os.path.join(JOB_DIR, "stderr.log"), "w",
              encoding="utf-8", errors="replace", buffering=1) as err:
        proc = subprocess.Popen(
            [meta["python"], os.path.join(JOB_DIR, "script.py")],
            stdout=out, stderr=err, stdin=subprocess.DEVNULL,
            cwd=meta["cwd"], env=os.environ.copy(),
        )
        with open(os.path.join(JOB_DIR, "child_pid.txt"), "w") as f:
            f.write(str(proc.pid))
        rc = proc.wait()
finally:
    with open(os.path.join(JOB_DIR, "exit_code.txt"), "w") as f:
        f.write(str(rc))
'''


# ===========================================================================
# synchronous execution (unchanged behaviour)
# ===========================================================================

@mcp.tool()
def run_ansys_script(
    script_text: str,
    script_name: str = "",
    timeout_seconds: int = 3600,
) -> dict:
    """
    Execute a Python script against the local pyansys installation, BLOCKING
    until it finishes.

    Use this only for work that finishes in well under two minutes. The MCP
    transport times out sooner than `timeout_seconds` does, and when it fires
    you lose the result even though the script keeps running. For meshing,
    solving, or sweeps, use submit_ansys_job instead.

    The script runs in the ansys-agent venv (has pyansys-geometry,
    ansys-fluent-core, etc.) with access to your Ansys install.

    Args:
        script_text: Full Python script text to run. Self-contained.
        script_name: Optional filename for saving (default: timestamp-based).
        timeout_seconds: Kill the script if it hasn't finished (default 3600).

    Returns:
        Dict with: exit_code, stdout, stderr, script_path, duration_seconds.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = script_name or f"script_{ts}.py"
    if not name.endswith(".py"):
        name += ".py"
    script_path = SCRIPTS_DIR / name
    script_path.write_text(script_text, encoding="utf-8")

    start = datetime.now()
    try:
        proc = subprocess.run(
            [str(VENV_PYTHON), str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            **_win_flags(),
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "script_path": str(script_path),
            "duration_seconds": (datetime.now() - start).total_seconds(),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "exit_code": -1,
            "stdout": (e.stdout.decode() if e.stdout else ""),
            "stderr": f"Script timed out after {timeout_seconds}s",
            "script_path": str(script_path),
            "duration_seconds": (datetime.now() - start).total_seconds(),
        }
    except Exception as e:
        return {
            "exit_code": -2,
            "stdout": "",
            "stderr": f"{type(e).__name__}: {e}",
            "script_path": str(script_path),
            "duration_seconds": (datetime.now() - start).total_seconds(),
        }


# ===========================================================================
# background jobs
# ===========================================================================

@mcp.tool()
def submit_ansys_job(script_text: str, job_name: str = "", cwd: str = "") -> dict:
    """
    Start a Python script in the background and return immediately.

    This is the right tool for Fluent meshing, transient solves, and parameter
    sweeps -- anything that outlives an MCP call. The job is fully detached: it
    keeps running if this server restarts or the Claude session ends.

    Poll it with job_status(job_id). Fluent prints iteration progress to stdout,
    so the tail is genuinely informative while a solve runs.

    Args:
        script_text: Full Python script text. Self-contained.
        job_name: Optional label; a timestamp is appended to keep it unique.
        cwd: Working directory for the script. Defaults to the project root.
             Set this to the case directory so output files land there.

    Returns:
        Dict with job_id, job_dir, state, and the paths it will write.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = SAFE_NAME.sub("_", job_name.strip()) or "job"
    job_id = f"{label}_{ts}"
    d = _job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)

    work_dir = Path(cwd).resolve() if cwd else PROJECT_ROOT
    if not work_dir.exists():
        return {"error": f"cwd does not exist: {work_dir}"}

    (d / "script.py").write_text(script_text, encoding="utf-8")
    (d / "_runner.py").write_text(_RUNNER_SRC, encoding="utf-8")

    meta = {
        "job_id": job_id,
        "job_name": job_name,
        "python": str(VENV_PYTHON),
        "cwd": str(work_dir),
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }
    (d / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    try:
        runner = subprocess.Popen(
            [str(VENV_PYTHON), str(d / "_runner.py")],
            cwd=str(d), close_fds=True, **_win_flags(detached=True),
        )
    except Exception as e:
        return {"error": f"failed to launch runner: {type(e).__name__}: {e}"}

    meta["runner_pid"] = runner.pid
    (d / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return {
        "job_id": job_id,
        "job_dir": str(d),
        "state": "running",
        "runner_pid": runner.pid,
        "cwd": str(work_dir),
        "stdout_log": str(d / "stdout.log"),
        "stderr_log": str(d / "stderr.log"),
        "hint": "poll with job_status(job_id); it accepts wait_seconds to block briefly",
    }


@mcp.tool()
def job_status(job_id: str, tail_lines: int = 30, wait_seconds: int = 0) -> dict:
    """
    Check a background job, optionally waiting a little for it to finish.

    Args:
        job_id: From submit_ansys_job.
        tail_lines: How many trailing stdout lines to include (default 30).
        wait_seconds: Block up to this long waiting for completion. CAPPED AT
            60. Measured: wait_seconds=90 exceeded the MCP transport timeout and
            the call was lost (the job was unharmed). 45-50 is comfortable.
            0 returns immediately.

    Returns:
        Dict with state (running|succeeded|failed|lost), exit_code, elapsed
        seconds, and tails of stdout/stderr.
    """
    d = _job_dir(job_id)
    if not d.exists():
        return {"error": f"unknown job_id: {job_id}"}

    deadline = time.time() + max(0, min(int(wait_seconds), 60))
    while True:
        state = _resolve(d, dict(_read_meta(d)))
        if state["state"] != "running" or time.time() >= deadline:
            break
        time.sleep(2)

    try:
        submitted = datetime.fromisoformat(state["submitted_at"])
        state["elapsed_seconds"] = round((datetime.now() - submitted).total_seconds(), 1)
    except Exception:
        pass

    state["stdout_tail"] = _tail(d / "stdout.log", tail_lines)
    state["stderr_tail"] = _tail(d / "stderr.log", min(tail_lines, 20))
    state["job_dir"] = str(d)
    return state


@mcp.tool()
def job_log(job_id: str, stream: str = "stdout", max_chars: int = 40000) -> dict:
    """
    Read a job's full log.

    Args:
        job_id: From submit_ansys_job.
        stream: "stdout" or "stderr".
        max_chars: Truncate from the FRONT beyond this, keeping the tail --
            the end of a solver log is the interesting part.

    Returns:
        Dict with text, truncated flag, and total_chars.
    """
    d = _job_dir(job_id)
    if not d.exists():
        return {"error": f"unknown job_id: {job_id}"}
    if stream not in ("stdout", "stderr"):
        return {"error": "stream must be 'stdout' or 'stderr'"}

    p = d / f"{stream}.log"
    if not p.exists():
        return {"job_id": job_id, "stream": stream, "text": "", "total_chars": 0,
                "truncated": False, "note": "log not created yet"}

    text = p.read_text(encoding="utf-8", errors="replace")
    total = len(text)
    truncated = total > max_chars
    if truncated:
        text = "...[%d chars truncated]...\n" % (total - max_chars) + text[-max_chars:]
    return {"job_id": job_id, "stream": stream, "text": text,
            "total_chars": total, "truncated": truncated}


@mcp.tool()
def job_cancel(job_id: str) -> dict:
    """
    Kill a running job and its whole process tree, including Fluent itself.

    Args:
        job_id: From submit_ansys_job.

    Returns:
        Dict with the resulting state.
    """
    d = _job_dir(job_id)
    if not d.exists():
        return {"error": f"unknown job_id: {job_id}"}

    meta = _read_meta(d)
    killed = []
    for key, f in (("runner_pid", None), ("child_pid", d / "child_pid.txt")):
        pid = 0
        if f is not None and f.exists():
            try:
                pid = int(f.read_text().strip())
            except Exception:
                pid = 0
        else:
            pid = int(meta.get(key) or 0)
        if not pid or not _pid_alive(pid):
            continue
        try:
            if IS_WIN:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                               capture_output=True, **_win_flags())
            else:
                os.kill(pid, 9)
            killed.append(pid)
        except Exception as e:
            return {"error": f"kill {pid} failed: {type(e).__name__}: {e}"}

    ec = d / "exit_code.txt"
    if not ec.exists():
        ec.write_text(str(CANCELLED_CODE), encoding="utf-8")

    return {"job_id": job_id, "state": "cancelled", "killed_pids": killed}


@mcp.tool()
def job_list(limit: int = 20) -> list:
    """
    List submitted jobs, newest first.

    Args:
        limit: Maximum number to return (default 20).

    Returns:
        List of dicts with job_id, state, exit_code, submitted_at, cwd.
    """
    if not JOBS_DIR.exists():
        return []
    dirs = sorted((p for p in JOBS_DIR.iterdir() if p.is_dir()),
                  key=lambda p: p.stat().st_mtime, reverse=True)[:max(1, limit)]
    out = []
    for d in dirs:
        s = _resolve(d, dict(_read_meta(d)))
        out.append({k: s.get(k) for k in
                    ("job_id", "state", "exit_code", "submitted_at",
                     "finished_at", "cwd", "job_name")})
    return out


# ===========================================================================
# reading results and reference material
# ===========================================================================

@mcp.tool()
def read_json_file(file_path: str) -> dict:
    """
    Read a JSON file (results.json, params.json, etc.).

    Args:
        file_path: Absolute path or relative to project root.

    Returns:
        Parsed JSON dict, or {"error": "..."}.
    """
    p = Path(file_path)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    if not p.exists():
        return {"error": f"File not found: {p}"}
    try:
        with open(p, encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}


@mcp.tool()
def list_case_results(results_root: str = "results") -> list:
    """
    List all case-result directories under the given root, newest first.

    Args:
        results_root: Directory to search (default 'results' under the runtime dir).

    Returns:
        List of dicts with case_name, path, has_results_json, results_json_path.
    """
    root = Path(results_root)
    if not root.is_absolute():
        root = RUNTIME_DIR / root
    if not root.exists():
        return []
    cases = []
    for d in sorted(root.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        results_json = (
            next(d.glob("*_results.json"), None)
            or next(d.glob("results.json"), None)
        )
        cases.append({
            "case_name": d.name,
            "path": str(d),
            "has_results_json": results_json is not None,
            "results_json_path": str(results_json) if results_json else None,
        })
    return cases


@mcp.tool()
def read_skill_reference(skill: str, sheet_name: str) -> str:
    """
    Read a reference sheet from the skills directory.

    Args:
        skill: "spaceclaim-cad" or "ansys-fluent-cfd".
        sheet_name: Reference sheet filename (with or without .md extension).

    Returns:
        The reference sheet contents, or an error message.
    """
    valid_skills = ("spaceclaim-cad", "ansys-fluent-cfd")
    if skill not in valid_skills:
        return f"Error: unknown skill '{skill}'. Valid: {valid_skills}"

    if not sheet_name.endswith(".md"):
        sheet_name += ".md"

    path = SKILLS_DIR / skill / "reference" / sheet_name
    if not path.exists():
        ref_dir = SKILLS_DIR / skill / "reference"
        available = [f.name for f in ref_dir.glob("*.md")] if ref_dir.exists() else []
        return f"Error: sheet not found. Available in {skill}: {available}"

    return path.read_text(encoding="utf-8")


@mcp.tool()
def list_skill_reference_sheets() -> dict:
    """
    List all available reference sheets by skill.

    Returns:
        Dict keyed by skill name, values are lists of sheet filenames.
    """
    result = {}
    if not SKILLS_DIR.exists():
        return result
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        ref_dir = skill_dir / "reference"
        if ref_dir.exists():
            result[skill_dir.name] = sorted(f.name for f in ref_dir.glob("*.md"))
    return result


if __name__ == "__main__":
    mcp.run()
