"""
Orchestrator: runs the full pipeline (geometry -> mesh+solve -> post).
"""
import json
import time
from datetime import datetime
from pathlib import Path

# Delay between Fluent sessions to let ports release cleanly
INTERSTAGE_DELAY_S = 10


def load_params(params_path) -> dict:
    """Load a JSON params file, tolerant of UTF-8 BOM."""
    with open(Path(params_path), encoding="utf-8-sig") as f:
        return json.load(f)


def validate_params(params: dict, schema_path=None) -> None:
    try:
        import jsonschema
    except ImportError:
        print("[run] jsonschema not installed; skipping validation")
        return
    if schema_path is None:
        schema_path = Path(__file__).parent.parent / "schema" / "flow_cylinder.schema.json"
    with open(Path(schema_path), encoding="utf-8-sig") as f:
        schema = json.load(f)
    jsonschema.validate(instance=params, schema=schema)
    print("[run] Params validated against schema")


def run_case(params_path, output_root="results") -> dict:
    """Full geometry -> mesh+solve -> post pipeline."""
    from .geometry import build_geometry
    from .mesh_solve import mesh_and_solve
    from .post import extract_results

    params = load_params(params_path)
    validate_params(params)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    case_name = params["case_name"]
    out_dir = Path(output_root) / f"{case_name}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[run] Case: {case_name}")
    print(f"[run] Output dir: {out_dir}\n")

    print("[run] === Stage 1/3: Geometry ===")
    pmdb = build_geometry(params, out_dir=out_dir)
    print()

    print(f"[run] Waiting {INTERSTAGE_DELAY_S}s for ports to release...")
    time.sleep(INTERSTAGE_DELAY_S)

    print("[run] === Stage 2/3: Mesh + Solve ===")
    case_file = mesh_and_solve(pmdb, params, out_dir=out_dir)
    print()

    print(f"[run] Waiting {INTERSTAGE_DELAY_S}s for ports to release...")
    time.sleep(INTERSTAGE_DELAY_S)

    print("[run] === Stage 3/3: Post-processing ===")
    results = extract_results(case_file, params, out_dir=out_dir)
    print()

    input_copy = out_dir / f"{case_name}_input.json"
    with open(input_copy, "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)

    print(f"[run] Complete. All artifacts in: {out_dir}")
    return results
