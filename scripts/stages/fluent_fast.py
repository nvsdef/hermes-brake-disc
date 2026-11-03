"""Gate 3 (fast mode) - Fluent mesh + setup + short transient in ONE launch.

Run it with the ansys-agent MCP:  submit_ansys_job(script_text=<launcher>, cwd=<RUN>\\30_fluent)
where the launcher sets BRAKE_RUN and runs this file. The fluent-engineer launches it, polls
job_status, and judges <RUN>\\30_fluent\\results.json. Fluent is LEFT OPEN at the end with a
temperature contour on screen (that is the visual; no PNGs are written).

Fast-mode settings (override with env vars; defaults chosen so meshing + solve take minutes):
  FAST_END_TIME_S   ts     simulated braking time; default the full stop from case.json (3.540681 s)
  FAST_DT_S         0.05   time step
  FAST_ITERS        3      iterations per step (solid conduction converges in 1-2)
  FAST_WINDOW_STEPS 4      q''' and omega updated every window (interval-average value)
  mesh: global 4 to 20 mm, growth 1.2, curvature 18 deg; local cheeks 8, vanes 8, hat 12 mm
Loads, materials, rotation and convection are the PRD H1.2 / case.json values.
"""
import hashlib, json, math, os, sys, time, traceback
from pathlib import Path

RUN = Path(os.environ.get("BRAKE_RUN") or sys.argv[1])
STAGE = RUN / "30_fluent"; STAGE.mkdir(parents=True, exist_ok=True); os.chdir(STAGE)
PMDB = RUN / "20_spaceclaim" / "brake.pmdb" / "brake.pmdb"
CASE = RUN / "00_lead" / "case.json"
MESH = STAGE / "brake.msh.h5"
os.environ.setdefault("AWP_ROOT261", r"C:\Program Files\ANSYS Inc\ANSYS Student\v261")
END_ENV = os.environ.get("FAST_END_TIME_S"); DT = float(os.environ.get("FAST_DT_S", 0.05))
ITERS = int(os.environ.get("FAST_ITERS", 3)); WIN = int(os.environ.get("FAST_WINDOW_STEPS", 4))
MESH_SIZES = {"min": float(os.environ.get("FAST_MESH_MIN_MM", 4.0)), "max": 20.0, "growth": 1.2, "curv": 18,
              "cheek": 8.0, "vane": 8.0, "hat": 12.0}

import numpy as np
import psutil
import ansys.fluent.core as pyfluent
from ansys.fluent.core import SurfaceFieldDataRequest, SurfaceDataType

T0 = time.time()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
now = lambda: time.strftime("%Y-%m-%dT%H:%M:%S")
case = json.loads(CASE.read_text()); D = case["derived"]
TS, Q0, W0, WREF = D["stop_time_s"], D["q_layer_peak_W_m3"], D["omega0_rad_s"], D["omega_ref_rad_s"]
END = float(END_ENV) if END_ENV else TS                 # default: the whole stop
E_VEH = D["energy_per_front_rotor_J"]; LAYER = case["heat_source"]["layer_thickness_m"]
HREF = {g: v["h_ref_W_m2K"] for g, v in case["convection"]["groups"].items()}
MATS = {"grey-iron": (7200.0, 447.0, 52.0), "pad-compound": (2500.0, 900.0, 1.2), "backing-steel": (8030.0, 502.0, 16.3)}
ZM = {z: "grey-iron" for z in ["cheek_out", "cheek_in", "hat"] + [f"vane_{k:02d}" for k in range(1, 21)]}
ZM.update({"outerpad": "pad-compound", "innerpad": "pad-compound", "bp_outer": "backing-steel", "bp_inner": "backing-steel"})
FRICTION = ["cheek_out-outerpad", "cheek_in-innerpad"]

rep = {"run_id": RUN.name, "prd_revision": "H1.2", "producing_role": "fluent-engineer", "mode": "fast",
       "stage_script": "scripts/stages/fluent_fast.py", "started_at": now(), "status": "RUNNING",
       "inputs_sha256": {"20_spaceclaim/brake.pmdb/brake.pmdb": sha(PMDB), "00_lead/case.json": sha(CASE)},
       "settings": {"end_time_s": END, "dt_s": DT, "iters_per_step": ITERS, "window_steps": WIN, "mesh_mm": MESH_SIZES},
       "checks": [], "phase_seconds": {}, "history": [],
       "timing": {"started_at": now(), "app_launches": {"fluent_sessions": 0}}}


def chk(name, exp, meas, tol, rel=False, kind="abs"):
    if meas is None:
        r = {"check": name, "expected": exp, "measured": None, "pass": False}
    elif kind == "max":
        r = {"check": name, "expected": "<= %s" % exp, "measured": meas, "pass": meas <= exp}
    elif kind == "min":
        r = {"check": name, "expected": ">= %s" % exp, "measured": meas, "pass": meas >= exp}
    else:
        d = (meas - exp) / exp * 100 if rel else meas - exp
        r = {"check": name, "expected": exp, "measured": round(float(meas), 4), "delta": round(float(d), 4),
             "delta_unit": "pct" if rel else "abs", "tolerance": tol, "pass": abs(d) <= tol}
    rep["checks"].append(r)
    print("CHECK %-36s expected %-12s measured %-14s %s" % (name, r["expected"], r["measured"], "PASS" if r["pass"] else "FAIL"), flush=True)
    return r["pass"]


def phase(name, t):
    rep["phase_seconds"][name] = round(time.time() - t, 1); print("PHASE", name, rep["phase_seconds"][name], "s", flush=True); return time.time()


def write(status):
    rep["status"] = status; rep["finished_at"] = now(); rep["timing"]["finished_at"] = now()
    rep["timing"]["seconds"] = round(time.time() - T0, 1)
    (STAGE / "results.json").write_text(json.dumps(rep, indent=1, default=float))


def num(res, key):
    """compute() returns a list with one {name: [value, ...]} dict per report definition."""
    for r in (res if isinstance(res, list) else [res]):
        if key in r:
            v = r[key]
            return float(v[0] if isinstance(v, (list, tuple)) else v)
    raise KeyError(key)


busy = [(p.pid, p.name()) for p in psutil.process_iter(["name"])
        if (p.info["name"] or "").lower() in ("spaceclaim.exe", "discovery.exe", "fluent.exe", "cx2610.exe", "fl2610.exe")]
if busy:
    rep["blocked_by"] = busy; write("BLOCKED"); print("BLOCKED", busy); sys.exit(3)

status = "FAIL"; s = None
FLUENT_PROCS = ("fluent.exe", "fl2610.exe", "cx2610.exe", "fl_mpi2610.exe")
before = {p.pid for p in psutil.process_iter()}
try:
    t = time.time()
    s = pyfluent.launch_fluent(mode="meshing", precision="double", dimension=3, processor_count=4, ui_mode="gui",
                               cwd=str(STAGE), product_version="26.1.0", cleanup_on_exit=False,
                               start_transcript=False, start_timeout=300)
    rep["timing"]["app_launches"]["fluent_sessions"] = 1
    t = phase("launch", t)

    # ---- MESH (watertight workflow, task-object style; verified on run 2, 2026-11-02) ----
    wf = s.workflow
    wf.InitializeWorkflow(WorkflowType="Watertight Geometry")
    imp = wf.TaskObject["Import Geometry"]; imp.Arguments.set_state({"FileName": str(PMDB), "LengthUnit": "mm"}); imp.Execute()
    ls = wf.TaskObject["Add Local Sizing"]
    for name, sz, labels in [("cheek", MESH_SIZES["cheek"], ["cheek_out", "cheek_in"]),
                             ("vane", MESH_SIZES["vane"], [f"vane_{k:02d}" for k in range(1, 21)]),
                             ("hat", MESH_SIZES["hat"], ["hat"])]:
        ls.Arguments.set_state({"AddChild": "yes", "BOIControlName": name, "BOIExecution": "Body Size", "BOISize": sz,
                                "BOIZoneorLabel": "label", "BOIFaceLabelList": labels})
        ls.AddChildAndUpdate()
    surf = wf.TaskObject["Generate the Surface Mesh"]
    surf.Arguments.set_state({"CFDSurfaceMeshControls": {"MinSize": MESH_SIZES["min"], "MaxSize": MESH_SIZES["max"],
                                                         "GrowthRate": MESH_SIZES["growth"], "CurvatureNormalAngle": MESH_SIZES["curv"]}})
    surf.Execute()
    desc = wf.TaskObject["Describe Geometry"]
    desc.Arguments.set_state({"SetupType": "The geometry consists of only solid regions", "InvokeShareTopology": "Yes"})
    desc.UpdateChildTasks(SetupTypeChanged=True); desc.Execute()
    names = list(wf.TaskObject.get_object_names())
    for tn in ("Apply Share Topology", "Share Topology", "Update Boundaries", "Create Regions", "Update Regions"):
        if tn in names: wf.TaskObject[tn].Execute()
    bl = wf.TaskObject["Add Boundary Layers"]; bl.Arguments.set_state({"AddChild": "no"}); bl.Execute()
    vol = wf.TaskObject["Generate the Volume Mesh"]; vol.Arguments.set_state({"VolumeFill": "poly-hexcore"}); vol.Execute()
    if MESH.exists(): MESH.unlink()
    s.meshing.File.WriteMesh(FileName=str(MESH))
    rep["mesh"] = {"path": str(MESH), "bytes": MESH.stat().st_size, "sha256": sha(MESH)}
    t = phase("mesh", t)

    # ---- SOLVER: read mesh, mesh gate -------------------------------------------------------
    s = s.switch_to_solver()
    st = s.settings
    czs = st.setup.cell_zone_conditions.solid
    try: loaded = len(czs.get_object_names())
    except Exception: loaded = 0
    if loaded != 27:                                    # switch_to_solver normally transfers the mesh
        st.file.read_case(file_name=str(MESH))
    rep["mesh"]["transferred_by_switch"] = loaded == 27
    solids = sorted(czs.get_object_names())
    try: fluids = sorted(st.setup.cell_zone_conditions.fluid.get_object_names())
    except Exception: fluids = []
    bc = st.setup.boundary_conditions.wall
    walls = sorted(bc.get_object_names())
    shadows = [w for w in walls if w.endswith("-shadow")]
    rv = st.solution.report_definitions.volume
    rv["n-cells"] = {}; rv["n-cells"].report_type = "volume-sum"; rv["n-cells"] = {"field": "cell-volume", "cell_zones": solids}
    rep["mesh"].update({"solid_zones": solids, "n_walls": len(walls), "coupled_pairs": len(shadows)})
    ok = chk("solid_zones", 27, len(solids), 0) & chk("fluid_zones", 0, len(fluids), 0)
    ok &= chk("coupled_pairs", 45, len(shadows), 0)
    ok &= chk("zone_names_match_prd", 27, len(set(solids) & set(ZM)), 0)
    if not ok:
        raise SystemExit("mesh gate failed - not solving")

    # friction contact areas from the mesh (verified field-data idiom)
    fd = s.fields.field_data.get_field_data(SurfaceFieldDataRequest(surfaces=FRICTION,
             data_types=[SurfaceDataType.Vertices, SurfaceDataType.FacesConnectivity], flatten_connectivity=True))
    A_mesh = {}
    for w in FRICTION:
        V = np.asarray(fd[w].vertices, float).reshape(-1, 3); C = np.asarray(fd[w].connectivity).astype(int)
        A = 0.0; i = 0
        while i < len(C):
            n = C[i]; P = V[C[i + 1:i + 1 + n]]; i += 1 + n
            cr = sum(np.cross(P[k] - P[0], P[k + 1] - P[0]) for k in range(1, n - 1)); A += 0.5 * float(np.linalg.norm(cr))
        A_mesh[w] = A
        chk("friction_area_%s_mm2" % w, 5864.31, A * 1e6, 2.0, rel=True)
    rep["mesh"]["friction_area_m2"] = A_mesh
    t = phase("mesh_gate", t)

    # ---- SETUP -------------------------------------------------------------------------------
    st.setup.general.solver.time = "unsteady-1st-order"
    st.setup.models.energy = {"enabled": True}
    s.tui.solve.set.equations("flow", "no")
    mats = st.setup.materials.solid
    for n, (rho, cp, k) in MATS.items():
        if n not in mats.get_object_names(): mats.create(n)
        mats[n] = {"density": {"option": "constant", "value": rho}, "specific_heat": {"option": "constant", "value": cp},
                   "thermal_conductivity": {"option": "constant", "value": k}}
    for z, n in ZM.items(): czs[z].material = n
    zone_rb = {z: czs[z].material() for z in solids}
    chk("zone_materials_readback", 27, sum(1 for z in ZM if zone_rb.get(z) == ZM[z]), 0)
    for z in solids:
        czs[z] = {"solid_motion": {"enable": False}}
    for w in FRICTION:
        bc[w] = {"thermal": {"q_dot": {"value": Q0}, "wall_thickness": {"value": LAYER}}}
        try: bc[w].thermal.material = "grey-iron"
        except Exception as e: rep.setdefault("notes", []).append("layer material set failed on %s: %r" % (w, e))
    layer_rb = {w: bc[w].thermal.get_state().get("material") for w in FRICTION}
    rep["layer_material_readback"] = layer_rb
    chk("friction_layer_material_grey_iron", 2, sum(1 for v in layer_rb.values() if v == "grey-iron"), 0)
    groups = {"wall-vent": [w for w in walls if w.startswith("wall-vent")],
              "wall-outer": [w for w in walls if w.startswith("wall-outer")],
              "pad-backing-exposed": [w for w in walls if w.endswith(":1") and w.split(":")[0] in ("outerpad", "innerpad", "bp_outer", "bp_inner")]}
    rep["convection_walls"] = {g: len(v) for g, v in groups.items()}
    chk("convection_groups_nonempty", 3, sum(1 for v in groups.values() if v), 0)

    def omega(tm): return W0 * max(0.0, 1 - tm / TS)
    def q(tm): return Q0 * max(0.0, 1 - tm / TS)
    def h(g, tm): return max(7.0, HREF[g] * (abs(omega(tm)) / WREF) ** 0.8)
    def set_h(tm):
        for g, ws in groups.items():
            for w in ws: bc[w] = {"thermal": {"thermal_bc": "Convection", "heat_transfer_coeff": {"value": h(g, tm)}, "free_stream_temp": {"value": 300.0}}}

    init = st.solution.initialization; init.initialization_type = "standard"; init.defaults["temperature"] = 300.0
    init.standard_initialize()
    vol_total_mm3 = num(st.solution.report_definitions.compute(report_defs=["n-cells"]), "n-cells") * 1e9
    if not chk("meshed_volume_27_mm3", 2030484.53, vol_total_mm3, 2.0, rel=True):
        raise SystemExit("meshed volume gate failed - not solving")
    st.solution.run_calculation.parameters.time_step_size = DT
    # reports: peaks + stored energy (volume integral of T per material group)
    rs = st.solution.report_definitions.surface
    def vdef(n, typ, field, zones):
        rv[n] = {}; rv[n].report_type = typ; rv[n] = {"field": field, "cell_zones": zones}
    def sdef(n, typ, field, surfs):
        rs[n] = {}; rs[n].report_type = typ; rs[n] = {"field": field, "surface_names": surfs}
    grp = {m: [z for z in solids if ZM[z] == m] for m in MATS}
    for m, zs in grp.items():
        vdef("T-int-" + m, "volume-integral", "temperature", zs); vdef("V-" + m, "volume-sum", "cell-volume", zs)
    vdef("T-max-rotor", "volume-max", "temperature", grp["grey-iron"])
    vdef("T-max-pad", "volume-max", "temperature", grp["pad-compound"])
    sdef("T-face-rotor", "surface-facetmax", "temperature", FRICTION)
    sdef("T-face-pad", "surface-facetmax", "temperature", [w + "-shadow" for w in FRICTION])
    REPS = ["T-max-rotor", "T-max-pad", "T-face-rotor", "T-face-pad"] + ["T-int-" + m for m in MATS] + ["V-" + m for m in MATS]
    t = phase("setup", t)

    # ---- SOLVE in windows (interval-average loads) -----------------------------------------
    n_full = int(END / DT + 1e-9); tail = END - n_full * DT        # full steps plus one short final step
    n_steps = n_full + (1 if tail > 1e-9 else 0); done = 0; tm = 0.0; E_applied = 0.0
    A_tot = sum(A_mesh.values())
    set_h(0.0)
    while done < n_steps:
        k = min(WIN, n_full - done) if done < n_full else 1
        dt_w = DT if done < n_full else tail
        if dt_w != DT: st.solution.run_calculation.parameters.time_step_size = dt_w
        t_mid = tm + 0.5 * k * dt_w
        qw, ww = q(t_mid), omega(t_mid)
        for w in FRICTION: bc[w] = {"thermal": {"q_dot": {"value": qw}}}
        for z in ("cheek_out", "cheek_in"):
            czs[z] = {"solid_motion": {"enable": True, "solid_omega": ww, "solid_motion_axis_direction": [0, 0, 1],
                      "solid_motion_axis_origin": [0, 0, 0], "solid_motion_velocity": [0, 0, 0],
                      "solid_relative_to_thread": "absolute", "solid_motion_zone_motion_function": "none"}}
        if done and done % 24 < WIN: set_h(t_mid)             # h refresh about every 24 steps (PRD: <= 25)
        st.solution.run_calculation.dual_time_iterate(time_step_count=k, max_iter_per_step=ITERS)
        done += k; tm += k * dt_w; E_applied += qw * LAYER * A_tot * k * dt_w
        r = st.solution.report_definitions.compute(report_defs=REPS)
        vals = {n: num(r, n) for n in REPS}
        E_st = sum(rho * cp * (vals["T-int-" + m] - 300.0 * vals["V-" + m]) for m, (rho, cp, _) in MATS.items())
        row = {"t_s": round(tm, 6), "q_W_m3": qw, "omega_rad_s": ww, "T_face_rotor_K": vals["T-face-rotor"], "T_face_pad_K": vals["T-face-pad"],
               "T_max_rotor_K": vals["T-max-rotor"], "T_max_pad_K": vals["T-max-pad"], "E_applied_J": E_applied, "E_stored_J": E_st}
        rep["history"].append(row)
        print("t=%.3f s  rotor face %.1f K  pad face %.1f K  stored/applied %.1f %%" % (tm, row["T_face_rotor_K"], row["T_face_pad_K"], 100 * E_st / E_applied), flush=True)
    t = phase("solve", t)

    # ---- GATES --------------------------------------------------------------------------------
    H = rep["history"]
    Te = min(END, TS); E_exact = Q0 * LAYER * A_tot * (Te - Te ** 2 / (2 * TS))
    chk("applied_energy_vs_closed_form_pct", E_exact, H[-1]["E_applied_J"], 2.0, rel=True)
    chk("stored_over_applied_pct", 100.0, 100 * H[-1]["E_stored_J"] / H[-1]["E_applied_J"], 10.0)
    chk("rotor_face_heats_up_K", 300.0, H[-1]["T_face_rotor_K"], 0, kind="min")
    chk("pad_face_heats_up_K", 300.0, H[-1]["T_face_pad_K"], 0, kind="min")
    # the friction-face temperature peaks early and eases as the power ramps down (real physics);
    # what must rise every window is the stored heat and the bulk temperatures.
    chk("stored_energy_rises_every_window", len(H) - 1, sum(1 for a, b in zip(H, H[1:]) if b["E_stored_J"] > a["E_stored_J"]), 0)
    if END >= TS - 1e-6:
        chk("full_stop_covered_s", round(TS, 6), round(H[-1]["t_s"], 6), 1e-5)
        chk("applied_vs_vehicle_energy_pct", E_VEH, H[-1]["E_applied_J"], 2.0, rel=True)
    chk("no_unphysical_temperature_K", 1500.0, max(max(r["T_face_rotor_K"], r["T_face_pad_K"]) for r in H), 0, kind="max")
    rep["summary"] = {"simulated_s": H[-1]["t_s"], "rotor_face_K": H[-1]["T_face_rotor_K"], "pad_face_K": H[-1]["T_face_pad_K"],
                      "peak_rotor_face_K": max(r["T_face_rotor_K"] for r in H), "peak_pad_face_K": max(r["T_face_pad_K"] for r in H),
                      "E_applied_J": H[-1]["E_applied_J"], "E_stored_J": H[-1]["E_stored_J"],
                      "fraction_of_stop_energy_pct": 100 * H[-1]["E_applied_J"] / E_VEH,
                      "note": "fast profile: %.4f s of the %.4f s stop, coarse mesh, dt %.2f s; temperatures are coarse-mesh observations, not a THM verdict" % (END, TS, DT)}
    status = "PASS" if all(c["pass"] for c in rep["checks"]) else "FAIL"

    # ---- VISUAL: live temperature contour in the Fluent window (Fluent stays open) -----------
    try:
        g = st.results.graphics
        show = [w for w in walls if not w.endswith("-shadow") and "vane" not in w and not w.startswith("cheek_in-hat")]
        g.contour["temperature"] = {"field": "temperature", "surfaces_list": show, "boundary_values": True,
                                    "node_values": True, "filled": True}
        g.contour["temperature"].display()
        try: g.views.restore_view(view_name="isometric")
        except Exception: pass
        rep["live_contour"] = {"surfaces": len(show), "displayed": True}
    except Exception as e:
        rep["live_contour"] = {"displayed": False, "error": repr(e)[:300]}
    st.file.write(file_type="case-data", file_name=str(STAGE / "brake-fast.cas.h5"))
    t = phase("contour_and_write", t)
except SystemExit as e:
    rep["halt_reason"] = str(e)
except Exception as e:
    rep["error"] = repr(e)[:1000]; rep["traceback"] = traceback.format_exc()[-2500:]
finally:
    if status != "PASS" and s is not None:          # only a PASS leaves Fluent open on screen
        try: s.exit()
        except Exception as e: rep["exit_error"] = repr(e)[:200]
        time.sleep(5)
        mine = [p for p in psutil.process_iter(["name"]) if p.pid not in before and (p.info["name"] or "").lower() in FLUENT_PROCS]
        for p in mine:                                  # only processes this script started
            try: p.terminate()
            except psutil.NoSuchProcess: pass
        psutil.wait_procs(mine, timeout=15)
        rep["fluent_closed_on_fail"] = not any(psutil.pid_exists(p.pid) for p in mine)
    write(status)
    print("STATUS", rep["status"], "seconds", rep["timing"]["seconds"], "phases", rep["phase_seconds"], flush=True)
# Fluent is intentionally left running (cleanup_on_exit=False) so the contour stays on screen.
