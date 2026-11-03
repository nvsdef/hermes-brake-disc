"""
Mesh + solve module: import PMDB, watertight meshing workflow,
apply physics + BCs per params, solve to convergence, save case+data.
"""
from pathlib import Path
from ._launch import launch_fluent_with_retry


def mesh_and_solve(pmdb_path, params: dict, out_dir) -> Path:
    """Mesh + set up + solve. Returns path to saved .cas.h5."""
    pmdb_path = Path(pmdb_path).absolute()
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    assert pmdb_path.exists(), f"PMDB not found: {pmdb_path}"

    case_name      = params["case_name"]
    fluid_material = params["flow"]["fluid_material"]
    inlet_v        = params["flow"]["inlet_velocity_mps"]
    n_iter         = params.get("solver", {}).get("iterations", 150)
    turb_model     = params.get("solver", {}).get("turbulence_model", "k-omega-sst")
    min_size       = params.get("mesh", {}).get("min_size_m", 0.002)
    max_size       = params.get("mesh", {}).get("max_size_m", 0.02)
    growth_rate    = params.get("mesh", {}).get("growth_rate", 1.2)

    R = params["cylinder"]["radius_m"]
    D = params["domain"]["depth_m"]

    meshing = launch_fluent_with_retry(mode="meshing")

    wt = meshing.watertight()

    print(f"[mesh_solve] Importing: {pmdb_path.name}")
    wt.import_geometry.file_name = str(pmdb_path)
    wt.import_geometry.length_unit = "m"
    wt.import_geometry()

    wt.add_local_sizing_wtm.add_child_to_task()
    wt.add_local_sizing_wtm()

    print(f"[mesh_solve] Surface mesh (min={min_size}m, max={max_size}m)...")
    wt.create_surface_mesh.cfd_surface_mesh_controls.min_size = min_size
    wt.create_surface_mesh.cfd_surface_mesh_controls.max_size = max_size
    wt.create_surface_mesh.cfd_surface_mesh_controls.growth_rate = growth_rate
    wt.create_surface_mesh()

    wt.describe_geometry.update_child_tasks(setup_type_changed=False)
    wt.describe_geometry.setup_type = "fluid"
    wt.describe_geometry.update_child_tasks(setup_type_changed=True)
    wt.describe_geometry()

    wt.update_boundaries()
    wt.update_regions()

    print(f"[mesh_solve] Volume mesh...")
    wt.create_volume_mesh_wtm()

    print(f"[mesh_solve] Switching to solver...")
    solver = meshing.switch_to_solver()

    print(f"[mesh_solve] Physics: turbulence={turb_model}, fluid={fluid_material}")
    if turb_model == "k-omega-sst":
        solver.settings.setup.models.viscous.model = "k-omega"
        solver.settings.setup.models.viscous.k_omega_model = "sst"
    elif turb_model == "laminar":
        solver.settings.setup.models.viscous.model = "laminar"
    else:
        raise ValueError(f"Unknown turbulence_model: {turb_model}")

    solver.settings.setup.materials.database.copy_by_name(
        type="fluid", name=fluid_material
    )

    fluid_zones = list(solver.settings.setup.cell_zone_conditions.fluid.get_object_names())
    print(f"[mesh_solve] Fluid zones: {fluid_zones}")
    for z in fluid_zones:
        solver.settings.setup.cell_zone_conditions.fluid[z].general.material = fluid_material

    print(f"[mesh_solve] Inlet velocity: {inlet_v} m/s")
    inlet_bc = solver.settings.setup.boundary_conditions.velocity_inlet["inlet"]
    inlet_bc.momentum.velocity_magnitude.value = inlet_v

    ref_density = 998.2 if fluid_material == "water-liquid" else 1.225
    solver.settings.setup.reference_values.area     = 2 * R * D
    solver.settings.setup.reference_values.length   = 2 * R
    solver.settings.setup.reference_values.velocity = inlet_v
    solver.settings.setup.reference_values.density  = ref_density

    print(f"[mesh_solve] Init + {n_iter} iterations...")
    solver.settings.solution.initialization.hybrid_initialize()
    solver.settings.solution.run_calculation.iterate(iter_count=n_iter)

    case_file = out_dir / f"{case_name}.cas.h5"
    print(f"[mesh_solve] Saving: {case_file}")
    solver.settings.file.write_case_data(file_name=str(case_file.absolute()))

    solver.exit()
    return case_file
