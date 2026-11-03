"""
Geometry module: build parametric flow-around-cylinder fluid domain,
tag boundaries as named selections, export PMDB for Fluent.
"""
import shutil
from pathlib import Path


def build_geometry(params: dict, out_dir) -> Path:
    """
    Build the flow-around-cylinder fluid domain per params.

    Args:
        params: Validated dimension table (see schema/flow_cylinder.schema.json).
        out_dir: Directory for outputs (created if missing).

    Returns:
        Path to the exported PMDB file at <out_dir>/<case_name>.pmdb.
    """
    from ansys.geometry.core import launch_modeler
    from ansys.geometry.core.sketch import Sketch
    from ansys.geometry.core.math import Point2D
    from ansys.geometry.core.misc import UNITS, Distance
    from ansys.geometry.core.designer.face import SurfaceType

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    L  = params["domain"]["length_m"]
    H  = params["domain"]["height_m"]
    D  = params["domain"]["depth_m"]
    R  = params["cylinder"]["radius_m"]
    cx = params["cylinder"]["x_m"]
    cy = params["cylinder"]["y_m"]
    case_name = params["case_name"]

    print(f"[geometry] Launching Geometry service (SpaceClaim backend)...")
    modeler = launch_modeler()

    print(f"[geometry] Sketch: {L}x{H}x{D} m channel, cyl R={R} at ({cx},{cy})")
    sketch = Sketch()
    sketch.box(
        center=Point2D([L / 2, 0], unit=UNITS.m),
        width=Distance(L, UNITS.m),
        height=Distance(H, UNITS.m),
    )
    sketch.circle(
        Point2D([cx, cy], unit=UNITS.m),
        Distance(R, UNITS.m),
    )

    design = modeler.create_design(case_name)
    fluid = design.extrude_sketch(
        "fluid_domain",
        sketch,
        Distance(D, UNITS.m),
    )

    expected_vol = L * H * D - 3.14159265 * R ** 2 * D
    actual_vol = fluid.volume.m_as(UNITS.m ** 3)
    print(f"[geometry] Volume: {actual_vol:.6f} m^3 (expected {expected_vol:.6f})")

    inlet_faces, outlet_faces = [], []
    top_bottom_walls, symmetry_faces = [], []
    cylinder_walls = []
    for face in fluid.faces:
        if face.surface_type == SurfaceType.SURFACETYPE_CYLINDER:
            cylinder_walls.append(face)
            continue
        n = face.normal()
        if abs(n.x) > 0.99 and n.x < 0:
            inlet_faces.append(face)
        elif abs(n.x) > 0.99 and n.x > 0:
            outlet_faces.append(face)
        elif abs(n.y) > 0.99:
            top_bottom_walls.append(face)
        elif abs(n.z) > 0.99:
            symmetry_faces.append(face)

    print(f"[geometry] Faces: inlet={len(inlet_faces)} outlet={len(outlet_faces)} "
          f"walls={len(top_bottom_walls)} sym={len(symmetry_faces)} cyl={len(cylinder_walls)}")

    assert len(inlet_faces)      == 1
    assert len(outlet_faces)     == 1
    assert len(top_bottom_walls) == 2
    assert len(symmetry_faces)   == 2
    assert len(cylinder_walls)   >= 1

    design.create_named_selection("inlet",    faces=inlet_faces)
    design.create_named_selection("outlet",   faces=outlet_faces)
    design.create_named_selection("walls",    faces=top_bottom_walls)
    design.create_named_selection("symmetry", faces=symmetry_faces)
    design.create_named_selection("cylinder", faces=cylinder_walls)

    pmdb_temp = Path(design.export_to_pmdb())
    target_pmdb = out_dir / f"{case_name}.pmdb"
    if pmdb_temp.resolve() != target_pmdb.resolve():
        shutil.move(str(pmdb_temp), str(target_pmdb))
    print(f"[geometry] PMDB: {target_pmdb}")

    modeler.close()
    return target_pmdb
