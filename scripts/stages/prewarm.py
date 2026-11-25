"""Pre-open SpaceClaim and Fluent while SolidWorks builds (fast run profile).

Launched ONCE, fire-and-forget, by the solidworks-engineer at the start of Gate 1:
  submit_ansys_job(script_text=<launcher setting BRAKE_RUN and running this file>, cwd=<RUN>\\00_lead)
The CAD stage takes about 5 minutes; SpaceClaim (45 to 80 s) and Fluent (30 to 110 s) boot in
parallel during it, so Gates 2 and 3 start with their application already open.
Licence check 2026-11-25 (Ansys Student 2026 R1): SpaceClaim and Fluent run together.

Writes (the stage scripts read these and connect; if a file is missing or not "ready", or the
process is gone, they launch their own session exactly as before):
  <RUN>\\20_spaceclaim\\prewarm_spaceclaim.json   {state, host, port, transport_mode, pid, ready_at}
  <RUN>\\30_fluent\\prewarm_fluent.json           {state, server_info, pids, ready_at}
  <RUN>\\30_fluent\\prewarm_server_info.txt       ip:port + password (pyfluent server-info format)
SpaceClaim is held by this job until spaceclaim_prep.py writes <RUN>\\20_spaceclaim\\PREWARM_STOP
(or 60 min pass); then this job closes it. Fluent is launched with cleanup_on_exit=False and lives
on after this job; fluent_fast.py owns it from then on (left open on PASS, closed on FAIL).
"""
import json, logging, os, sys, threading, time, traceback
from pathlib import Path

RUN = Path(os.environ.get("BRAKE_RUN") or sys.argv[1])
SC_DIR = RUN / "20_spaceclaim"; FL_DIR = RUN / "30_fluent"
SC_DIR.mkdir(parents=True, exist_ok=True); FL_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("AWP_ROOT261", r"C:\Program Files\ANSYS Inc\ANSYS Student\v261")
os.chdir(RUN)
import psutil

SC_FILE = SC_DIR / "prewarm_spaceclaim.json"; FL_FILE = FL_DIR / "prewarm_fluent.json"
STOP = SC_DIR / "PREWARM_STOP"; HOLD_S = 3600
FLUENT_PROCS = ("fluent.exe", "fl2610.exe", "cx2610.exe", "fl_mpi2610.exe")
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%S")
def write(p, d): p.write_text(json.dumps(d, indent=1))
def say(k, v): print(k, json.dumps(v, default=str), flush=True)

busy = [(p.pid, p.name()) for p in psutil.process_iter(["name"])
        if (p.info["name"] or "").lower() in ("spaceclaim.exe", "discovery.exe") + FLUENT_PROCS]
if busy:
    for f in (SC_FILE, FL_FILE): write(f, {"state": "skipped", "reason": "Ansys already running", "busy": busy, "at": now()})
    say("SKIPPED", busy); sys.exit(0)            # stage scripts will see "skipped" and launch their own

state = {}

def spaceclaim():
    t = time.time(); write(SC_FILE, {"state": "launching", "launched_at": now()})
    try:
        from ansys.geometry.core import launch_modeler_with_spaceclaim
        before = {p.pid for p in psutil.process_iter()}
        m = launch_modeler_with_spaceclaim(version=261, hidden=False, transport_mode="wnua",
                                           server_working_dir=str(SC_DIR), client_log_level=logging.WARNING, timeout=300)
        host, port = m.client.get_name().split(":")
        pids = [p.pid for p in psutil.process_iter(["name"]) if p.pid not in before and (p.info["name"] or "").lower() == "spaceclaim.exe"]
        state["sc"] = m; state["sc_pid"] = pids[0] if pids else None
        write(SC_FILE, {"state": "ready", "host": host, "port": int(port), "transport_mode": "wnua", "pid": state["sc_pid"],
                        "boot_s": round(time.time() - t, 1), "ready_at": now()})
        say("SPACECLAIM_READY", {"boot_s": round(time.time() - t, 1), "pid": state["sc_pid"]})
    except Exception as e:
        write(SC_FILE, {"state": "failed", "error": repr(e)[:400], "at": now()}); say("SPACECLAIM_FAILED", repr(e)[:400])

def fluent():
    t = time.time(); write(FL_FILE, {"state": "launching", "launched_at": now()})
    try:
        import ansys.fluent.core as pyfluent
        before = {p.pid for p in psutil.process_iter()}
        s = pyfluent.launch_fluent(mode="meshing", precision="double", dimension=3, processor_count=4, ui_mode="gui",
                                   cwd=str(FL_DIR), product_version="26.1.0", cleanup_on_exit=False,
                                   start_transcript=False, start_timeout=300)
        cp = s.connection_properties
        si = FL_DIR / "prewarm_server_info.txt"; si.write_text(f"{cp.ip}:{cp.port}\n{cp.password}\n")
        pids = [p.pid for p in psutil.process_iter(["name"]) if p.pid not in before and (p.info["name"] or "").lower() in FLUENT_PROCS]
        write(FL_FILE, {"state": "ready", "server_info": str(si), "pids": pids, "boot_s": round(time.time() - t, 1), "ready_at": now()})
        say("FLUENT_READY", {"boot_s": round(time.time() - t, 1), "pids": pids})
    except Exception as e:
        write(FL_FILE, {"state": "failed", "error": repr(e)[:400], "at": now()}); say("FLUENT_FAILED", repr(e)[:400])

threads = [threading.Thread(target=spaceclaim), threading.Thread(target=fluent)]
[t.start() for t in threads]; [t.join() for t in threads]

# hold SpaceClaim until Gate 2 is done with it (or the hold expires)
t0 = time.time()
try:
    while "sc" in state and not STOP.exists() and time.time() - t0 < HOLD_S:
        if state.get("sc_pid") and not psutil.pid_exists(state["sc_pid"]): break
        time.sleep(3)
finally:
    if "sc" in state:
        try: state["sc"].close()
        except Exception as e: say("SPACECLAIM_CLOSE", repr(e)[:200])
        time.sleep(3)
        pid = state.get("sc_pid")
        if pid and psutil.pid_exists(pid):
            try: psutil.Process(pid).terminate()
            except Exception: pass
        d = json.loads(SC_FILE.read_text()); d.update(state="closed", closed_at=now(), stop_file=STOP.exists())
        write(SC_FILE, d); say("SPACECLAIM_CLOSED", d)
