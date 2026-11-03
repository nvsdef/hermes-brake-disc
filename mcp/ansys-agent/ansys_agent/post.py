"""
Post-processing module: load case+data, compute reports,
save velocity contour PNG and a results.json summary.
"""
import json
from pathlib import Path
from ._launch import launch_fluent_with_retry


def extract_results(case_path, params: dict, out_dir) -> dict:
    """Load solved case, extract reports, save PNG + JSON summary."""
    case_path = Path(case_path).absolute()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assert case_path.exists(), f"Case not found: {case_path}"

    case_name = params["case_name"]

    solver = launch_fluent_with_retry(mode="solver")

    print(f"[post] Reading case+data...")
    solver.settings.file.read_case_data(file_name=str(case_path))

    rd = solver.settings.solution.report_definitions

    rd.force["drag"] = {}
    rd.force["drag"].zones = ["cylinder"]
    rd.force["drag"].force_vector = [1.0, 0.0, 0.0]

    for name, boundary in [("mflow_inlet", "inlet"), ("mflow_outlet", "outlet")]:
        rd.flux[name] = {}
        rd.flux[name].boundaries = [boundary]

    for name, surf in [("p_inlet", "inlet"), ("p_outlet", "outlet")]:
        rd.surface[name] = {}
        rd.surface[name].surface_names = [surf]
        rd.surface[name].report_type = "surface-areaavg"
        rd.surface[name].field = "pressure"

    def val(name):
        try:
            r = rd.compute(report_defs=[name])
            if isinstance(r, list) and r:
                r = r[0]
            if isinstance(r, dict) and name in r:
                v = r[name]
                if isinstance(v, list) and v and isinstance(v[0], (int, float)):
                    return float(v[0])
        except Exception as e:
            print(f"[post] compute({name}) failed: {e}")
        return None

    print(f"[post] Computing reports...")
    drag_n    = val("drag")
    mflow_in  = val("mflow_inlet")
    mflow_out = val("mflow_outlet")
    p_in      = val("p_inlet")
    p_out     = val("p_outlet")

    print(f"[post] Rendering velocity contour...")
    png_path = out_dir / f"{case_name}_velocity.png"
    png_ok = False
    try:
        g = solver.settings.results.graphics
        if g.picture.use_window_resolution.is_active():
            g.picture.use_window_resolution = False
        g.picture.x_resolution = 1600
        g.picture.y_resolution = 900
        g.contour["vel"] = {}
        g.contour["vel"].field = "velocity-magnitude"
        g.contour["vel"].surfaces_list = ["symmetry"]
        g.contour["vel"].display()
        g.views.restore_view(view_name="front")
        g.views.auto_scale()
        g.picture.save_picture(file_name=str(png_path.absolute()))
        png_ok = png_path.exists()
    except Exception as e:
        print(f"[post] PNG failed: {e}")

    solver.exit()

    R = params["cylinder"]["radius_m"]
    D = params["domain"]["depth_m"]
    H = params["domain"]["height_m"]
    inlet_v = params["flow"]["inlet_velocity_mps"]
    ref_density = 998.2 if params["flow"]["fluid_material"] == "water-liquid" else 1.225
    ref_area = 2 * R * D
    inlet_area = H * D

    cd = drag_n / (0.5 * ref_density * inlet_v**2 * ref_area) if drag_n else None
    delta_p = (p_in - p_out) if (p_in is not None and p_out is not None) else None
    mbal = abs(mflow_in + mflow_out) if (mflow_in is not None and mflow_out is not None) else None
    expected_mflow = inlet_v * ref_density * inlet_area

    results = {
        "case_name": case_name,
        "mass_flow": {
            "inlet_kg_s":    mflow_in,
            "outlet_kg_s":   mflow_out,
            "balance_kg_s":  mbal,
            "expected_kg_s": expected_mflow,
        },
        "pressure": {
            "inlet_pa":  p_in,
            "outlet_pa": p_out,
            "drop_pa":   delta_p,
        },
        "drag": {
            "force_n": drag_n,
            "cd":      cd,
        },
        "reference": {
            "velocity_mps":      inlet_v,
            "density_kg_m3":     ref_density,
            "projected_area_m2": ref_area,
        },
        "artifacts": {
            "case_file":            str(case_path),
            "velocity_contour_png": str(png_path) if png_ok else None,
        },
    }

    results_json = out_dir / f"{case_name}_results.json"
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[post] Results JSON: {results_json}")

    return results
