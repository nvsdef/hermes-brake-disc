"""Gate 2 (fast mode) - SpaceClaim geometry prep in ONE launch.

Run it with the ansys-agent MCP:  submit_ansys_job(script_text=<this file with RUN set>,
cwd=<RUN>\\20_spaceclaim).  It is a vetted stage script: the spaceclaim-engineer launches
it, then judges <RUN>\\20_spaceclaim\\tag_report.json against the gates printed below.

What it does, in order (PRD H1.2 sections 2 to 4):
  1. launch SpaceClaim once (visible), import the frozen brake.step
  2. identify all 28 bodies by measured volume + bounding box against cad_report.json
  3. delete the calliper (unique match), re-read the design (27 bodies)
  4. name the 27 bodies (one body named selection each)
  5. tag rotor faces wall-vent / wall-outer by geometric rule; leave full-contact faces untagged
  6. export brake.pmdb (a FOLDER holding brake.pmdb), hash the inner file
  7. write tag_report.json, close SpaceClaim, confirm the process is gone
No screenshots (fast mode). The contact graph is proven downstream by Fluent's 45 coupled pairs.
"""
import hashlib, json, logging, os, sys, time, traceback
from pathlib import Path

RUN = Path(os.environ.get("BRAKE_RUN") or sys.argv[1])            # e.g. C:\brake-runs\<run-id>
STAGE = RUN / "20_spaceclaim"; STAGE.mkdir(parents=True, exist_ok=True); os.chdir(STAGE)
STEP = RUN / "10_cad" / "brake.step"
CAD = RUN / "10_cad" / "cad_report.json"
os.environ.setdefault("AWP_ROOT261", r"C:\Program Files\ANSYS Inc\ANSYS Student\v261")

import numpy as np
import psutil

T0 = time.time()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%S")
rep = {"run_id": RUN.name, "prd_revision": "H1.2", "producing_role": "spaceclaim-engineer",
       "stage_script": "scripts/stages/spaceclaim_prep.py", "started_at": now(), "status": "RUNNING",
       "inputs_sha256": {"10_cad/brake.step": sha(STEP), "10_cad/cad_report.json": sha(CAD)},
       "checks": [], "phase_seconds": {}}


def chk(name, exp, meas, tol, rel=False):
    if meas is None:
        r = {"check": name, "expected": exp, "measured": None, "delta": None, "tolerance": tol, "pass": False}
    else:
        d = (meas - exp) / exp * 100 if rel else meas - exp
        r = {"check": name, "expected": exp, "measured": round(float(meas), 4), "delta": round(float(d), 5),
             "delta_unit": "pct" if rel else "abs", "tolerance": tol, "pass": abs(d) <= tol}
    rep["checks"].append(r)
    print("CHECK %-38s expected %-12s measured %-14s delta %-10s tol %-6s %s" % (
        name, exp, r["measured"], r["delta"], tol, "PASS" if r["pass"] else "FAIL"), flush=True)
    return r["pass"]


def phase(name, t):
    rep["phase_seconds"][name] = round(time.time() - t, 1); return time.time()


def write(status):
    rep["status"] = status; rep["finished_at"] = now(); rep["timing"]["seconds"] = round(time.time() - T0, 1)
    (STAGE / "tag_report.json").write_text(json.dumps(rep, indent=1, default=float))


rep["timing"] = {"started_at": rep["started_at"], "app_launches": {"spaceclaim_sessions": 0}}

# ---- 0. one Ansys session at a time (Student) ----------------------------------------
busy = [(p.pid, p.name()) for p in psutil.process_iter(["name"])
        if (p.info["name"] or "").lower() in ("spaceclaim.exe", "discovery.exe", "fluent.exe", "cx2610.exe", "fl2610.exe")]
if busy:
    rep["blocked_by"] = busy; write("BLOCKED"); print("BLOCKED: Ansys processes already running", busy); sys.exit(3)

# ---- reference signatures: Gate 1 MEASURED values ------------------------------------
cad = json.loads(CAD.read_text())
REF = {}
for b in cad["bodies"]:
    bb = b["bbox_mm"]
    REF[b["name"]] = {"v": b["volume_m3"] * 1e9, "bb": np.array([bb["x"][0], bb["y"][0], bb["z"][0], bb["x"][1], bb["y"][1], bb["z"][1]])}

from ansys.geometry.core import launch_modeler_with_spaceclaim
from ansys.geometry.core.designer import SurfaceType

m = None; sc_pid = None; status = "FAIL"
try:
    t = time.time()
    before = {p.pid for p in psutil.process_iter()}
    m = launch_modeler_with_spaceclaim(version=261, hidden=False, transport_mode="wnua",
                                       server_working_dir=str(STAGE), client_log_level=logging.WARNING, timeout=300)
    rep["timing"]["app_launches"]["spaceclaim_sessions"] = 1
    new = [p.pid for p in psutil.process_iter(["name"]) if p.pid not in before and (p.info["name"] or "").lower() == "spaceclaim.exe"]
    sc_pid = new[0] if new else None
    rep["session"] = {"pid": sc_pid, "backend_version": str(m.client.backend_version)}
    t = phase("launch", t)

    # ---- 1. import + scale --------------------------------------------------------------
    m.open_file(str(STEP))
    design = m.read_existing_design(); bodies = design.get_all_bodies()
    bb = lambda b: np.r_[np.asarray(b.bounding_box.min_corner, float), np.asarray(b.bounding_box.max_corner, float)] * 1000.0
    sig = [(b, b.volume.m_as("mm**3"), bb(b)) for b in bodies]
    allbb = np.array([s[2] for s in sig])
    ok = chk("imported_solid_count", 28, len(bodies), 0)
    ok &= chk("rotor_od_mm", 330.0, float((allbb[:, 3] - allbb[:, 0]).max()), 0.1)
    ok &= chk("z_min_mm", -57.0, float(allbb[:, 2].min()), 0.05)
    ok &= chk("z_max_mm", 57.0, float(allbb[:, 5].max()), 0.05)
    ok &= chk("total_volume_28_mm3", 2647566.01, sum(s[1] for s in sig), 1.0, rel=True)
    t = phase("import", t)
    if not ok:
        raise SystemExit("import gate failed - CAD defect goes back to solidworks-engineer")

    # ---- 2. identify by volume + bbox (score in units of tolerance) ---------------------
    names = {}; rows = []
    for b, v, box in sig:
        sc = sorted((max(abs(v - r["v"]) / r["v"] * 100 / 1.0, float(np.abs(box - r["bb"]).max()) / 0.05), n) for n, r in REF.items())
        names.setdefault(sc[0][1], []).append(b)
        rows.append({"name": sc[0][1], "score": round(sc[0][0], 4), "runner_up": sc[1][1], "runner_up_score": round(sc[1][0], 2),
                     "volume_mm3": round(v, 3), "bbox_mm": [round(x, 3) for x in box]})
    rep["body_map"] = rows
    perm = len(names) == 28 and all(len(v) == 1 for v in names.values())
    ok = chk("body_map_unique_matches", 28, sum(1 for v in names.values() if len(v) == 1) if perm else 0, 0)
    ok &= chk("body_map_worst_score", 0.0, max(r["score"] for r in rows), 1.0)
    if not ok:
        raise SystemExit("body map failed")

    # ---- 3. delete calliper, re-read ----------------------------------------------------
    cal = names["calliper"][0]; cal_v = cal.volume.m_as("mm**3"); tot = sum(s[1] for s in sig)
    rep["calliper_match"] = [r for r in rows if r["name"] == "calliper"][0]
    design.delete_body(cal)
    design = m.read_existing_design(); bodies = design.get_all_bodies()
    tot2 = sum(b.volume.m_as("mm**3") for b in bodies)
    ok = chk("after_delete_count", 27, len(bodies), 0)
    ok &= chk("volume_drop_vs_calliper_pct", cal_v, tot - tot2, 0.5, rel=True)
    ok &= chk("total_volume_27_mm3", 2030484.53, tot2, 1.0, rel=True)
    t = phase("identify_delete", t)
    if not ok:
        raise SystemExit("calliper delete failed")

    # ---- 4. name 27 bodies (re-identify on the re-read design) --------------------------
    R27 = {k: v for k, v in REF.items() if k != "calliper"}
    named = {}
    for b in bodies:
        box = bb(b); v = b.volume.m_as("mm**3")
        n = min(R27, key=lambda k: max(abs(v - R27[k]["v"]) / R27[k]["v"] * 100, float(np.abs(box - R27[k]["bb"]).max()) / 0.05))
        named.setdefault(n, []).append(b)
    if len(named) != 27 or any(len(v) != 1 for v in named.values()):
        raise SystemExit("re-identification after delete is not a permutation")
    for n, [b] in named.items():
        b.name = n
        design.create_named_selection(n, bodies=[b])
    t = phase("name_bodies", t)

    # ---- 5. rule-based face tagging (PRD section 4 surface groups) ----------------------
    # Full-contact faces (untagged): hat r=95 cylinder, cheek_in r=95 bore, vane faces at z=+/-6,
    # pad friction faces z=+/-16, pad backs z=+/-28. Partial-contact faces are tagged in full.
    vent, outer, pb = [], [], []
    def plane_z(f):
        b2 = f.bounding_box; z0, z1 = float(np.asarray(b2.min_corner)[2]) * 1000, float(np.asarray(b2.max_corner)[2]) * 1000
        return 0.5 * (z0 + z1) if abs(z1 - z0) < 1e-3 else None
    def radius(f):
        try: return float(f.shape.geometry.radius.m_as("mm"))
        except Exception: return None
    for n, [b] in named.items():
        for f in b.faces:
            st = f.surface_type; a = f.area.m_as("mm**2")
            z = plane_z(f) if st == SurfaceType.SURFACETYPE_PLANE else None
            r = radius(f) if st == SurfaceType.SURFACETYPE_CYLINDER else None
            if n.startswith("vane_"):
                if z is not None and abs(abs(z) - 6) < 1e-3: continue          # vane/cheek contact
                vent.append((f, a))
            elif n in ("cheek_out", "cheek_in", "hat"):
                if r is not None and abs(r - 95) < 0.02 and n in ("hat", "cheek_in"): continue   # hat/cheek_in contact
                if z is not None and n.startswith("cheek") and abs(abs(z) - 6) < 1e-3: vent.append((f, a))
                else: outer.append((f, a))
            else:                                                               # pads and backing plates
                if n.endswith("pad") and z is not None and abs(abs(z) - 16) < 1e-3: continue
                if n.endswith("pad") and z is not None and abs(abs(z) - 28) < 1e-3: continue
                pb.append((f, a))
    design.create_named_selection("wall-vent", faces=[f for f, _ in vent])
    design.create_named_selection("wall-outer", faces=[f for f, _ in outer])
    design = m.read_existing_design()
    nss = {ns.name: ns for ns in design.named_selections}
    rb_vent = sum(f.area.m_as("mm**2") for f in nss["wall-vent"].faces)
    rb_outer = sum(f.area.m_as("mm**2") for f in nss["wall-outer"].faces)
    rep["named_selections"] = {"count": len(nss), "names": sorted(nss),
                               "wall-vent": {"faces": len(vent), "area_mm2": rb_vent},
                               "wall-outer": {"faces": len(outer), "area_mm2": rb_outer},
                               "pad_backing_exposed_untagged": {"faces": len(pb), "area_mm2": sum(a for _, a in pb)},
                               "predicted_after_imprint_mm2": {"wall-vent": 142865.51, "wall-outer": 228477.17, "pad_backing": 31268.67}}
    ok = chk("named_selection_count", 29, len(nss), 0)
    ok &= chk("wall_vent_before_imprint_mm2", 167037.60, rb_vent, 2.0, rel=True)
    ok &= chk("wall_outer_before_imprint_mm2", 240205.78, rb_outer, 2.0, rel=True)
    ok &= chk("pad_backing_before_imprint_mm2", 42997.28, sum(a for _, a in pb), 2.0, rel=True)
    t = phase("tag_faces", t)
    if not ok:
        raise SystemExit("named-selection gate failed")

    # ---- 6. export PMDB ------------------------------------------------------------------
    p = Path(design.export_to_pmdb(STAGE / "brake.pmdb"))
    inner = p if p.is_file() else STAGE / "brake.pmdb" / "brake.pmdb"
    rep["pmdb"] = {"path": str(inner), "bytes": inner.stat().st_size, "sha256": sha(inner)}
    rep["pmdb_sha256"] = rep["pmdb"]["sha256"]
    chk("pmdb_inner_file_bytes_gt0", 1, 1.0 if inner.stat().st_size > 0 else 0.0, 0)
    t = phase("export_pmdb", t)
    status = "PASS" if all(c["pass"] for c in rep["checks"]) else "FAIL"
except SystemExit as e:
    rep["halt_reason"] = str(e); status = "FAIL"
except Exception as e:
    rep["error"] = repr(e); rep["traceback"] = traceback.format_exc()[-2000:]; status = "FAIL"
finally:
    if m is not None:
        try: m.close()
        except Exception as e: rep["close_error"] = repr(e)
    time.sleep(3)
    rep["spaceclaim_left_running"] = bool(sc_pid and psutil.pid_exists(sc_pid))
    write(status)
    print("STATUS", rep["status"], "seconds", rep["timing"]["seconds"], "phases", rep["phase_seconds"], flush=True)
