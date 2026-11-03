# case.json - every field, unit and meaning

`00_lead\case.json` is the single declaration of the load case. The
fluent-engineer applies it and reads it back into `results.json`; the lead
compares the two. Write it by hand from your own computed values (there is no
template file to copy in this package), then validate it against the checklist at
the end of this page.

Rules:

- **Units in key names.** `stop_time_s`, `omega0_rad_s`, `h_ref_vent_W_m2K`. A
  number without a unit in its key is a defect.
- **Every derived number carries its formula** in a sibling `_formula` string or
  in the `derivation` list, so a reader can recompute it.
- **Spell keys exactly as below.** The predecessor lost a run because the case
  file said `rho` where the reader expected `density` and `backing_plate` where it
  expected `backplate`: 0 of 27 zones got a material and the warning list was
  empty. A near-miss key is read as absent. If the fluent-engineer reports a key
  it cannot find, fix `case.json` (Gate 0 is yours), re-hash it, and tell the
  child the new hash.
- **Numbers are numbers**, not strings. Booleans are `true` / `false`.

## Full example (values are the PRD H1.2 values)

```json
{
  "run_id": "FR330V-20261001-0930",
  "prd_revision": "H1.2",
  "producing_role": "lead",
  "started_at": "2026-10-01T09:31:02+02:00",
  "finished_at": "2026-10-01T09:36:40+02:00",
  "status": "PASS",
  "inputs_sha256": {"specs/PRD.md": "<sha256>"},

  "vehicle": {
    "mass_kg": 1800,
    "entry_speed_kmh": 100,
    "deceleration_g": 0.8,
    "g_m_s2": 9.80665,
    "front_axle_bias": 0.70,
    "front_rotors": 2,
    "rolling_radius_m": 0.33
  },

  "derived": {
    "v0_m_s": 27.777778,
    "decel_m_s2": 7.84532,
    "stop_time_s": 3.540681,
    "stopping_distance_m": 49.1761,
    "vehicle_ke_J": 694444.44,
    "energy_per_front_rotor_J": 243055.56,
    "mean_power_W": 68646.55,
    "peak_power_W": 137293.10,
    "omega0_rad_s": -84.175084,
    "omega0_rpm_abs": 803.81,
    "omega_ref_rad_s": 56.116723,
    "pad_contact_area_m2": 0.005864306,
    "layer_thickness_m": 0.002,
    "source_volume_m3": 2.345723e-5,
    "q_layer_peak_W_m3": 5.852913e9,
    "q_layer_mean_W_m3": 2.926457e9,
    "q_face_peak_W_m2": 1.170583e7,
    "bulk_rise_upper_estimate_K": 41.91,
    "rotor_mass_kg": 12.9728
  },

  "derivation": [
    "v0_m_s = 100 / 3.6",
    "decel_m_s2 = 0.8 * 9.80665",
    "stop_time_s = v0_m_s / decel_m_s2",
    "stopping_distance_m = v0_m_s^2 / (2 * decel_m_s2)",
    "energy_per_front_rotor_J = 0.5 * 1800 * v0_m_s^2 * 0.70 / 2",
    "mean_power_W = energy_per_front_rotor_J / stop_time_s",
    "peak_power_W = 2 * mean_power_W",
    "omega0_rad_s = -(v0_m_s / 0.33); sign = -sign(dtheta_dr) of the vane mean line",
    "omega_ref_rad_s = (2/3) * abs(omega0_rad_s)",
    "pad_contact_area_m2 = (pi/6) * (0.160^2 - 0.120^2)",
    "q_layer_peak_W_m3 = peak_power_W / (2 * pad_contact_area_m2 * layer_thickness_m)",
    "bulk_rise_upper_estimate_K = energy_per_front_rotor_J / (rotor_mass_kg * 447)"
  ],

  "laws": {
    "power_W": "peak_power_W * (1 - t/stop_time_s) for 0 <= t <= stop_time_s, else 0",
    "q_layer_W_m3": "q_layer_peak_W_m3 * (1 - t/stop_time_s) for 0 <= t <= stop_time_s, else 0",
    "omega_rad_s": "omega0_rad_s * max(0, 1 - t/stop_time_s)",
    "h_W_m2K": "max(h_floor_W_m2K, h_ref * (abs(omega(t)) / omega_ref_rad_s)^h_exponent)"
  },

  "rotation": {
    "axis": [0.0, 0.0, 1.0],
    "origin_m": [0.0, 0.0, 0.0],
    "rotating_zones": ["cheek_out", "cheek_in"],
    "never_rotate": ["vane_01..vane_20", "hat", "outerpad", "innerpad", "bp_outer", "bp_inner"],
    "sense": "clockwise viewed from +Z (outboard)",
    "vane_sweep_dtheta_dr_sign": 1,
    "vane_sweep_evidence": "PRD 3.2: about -2.3 to +2.3 deg at r = 95, +29.8 to +33.4 deg at r = 165; confirm against cad_report.json vane_sweep at Gate 1",
    "sign_rule": "sign(omega) = -sign(dtheta/dr)",
    "cts_intent_met": false,
    "cts_intent_note": "CTS intent 'pumps under +theta' is not met by the PRD geometry (PRD section 10)"
  },

  "heat_source": {
    "model": "virtual wall layer heat generation, one side only per contact",
    "contacts": ["outerpad/cheek_out", "innerpad/cheek_in"],
    "layer_thickness_m": 0.002,
    "layer_material": {"name": "grey iron (MAT-01 values)", "density_kg_m3": 7200,
                       "cp_J_kgK": 447, "k_W_mK": 52,
                       "rule": "never Fluent's default aluminium; read back (PRD section 6)"},
    "q_scaling_area_m2": 5.864306e-3,
    "applied_energy_area_basis": "measured mesh contact areas (PRD section 6)",
    "applied_energy_target_J": 243055.56,
    "applied_energy_tolerance_pct": 2.0,
    "note": "the layer is a modelling assumption, not a physical interface"
  },

  "convection": {
    "t_inf_K": 300.0,
    "h_exponent": 0.8,
    "h_floor_W_m2K": 7.0,
    "omega_ref_rad_s": 56.116723,
    "groups": {
      "wall-vent":   {"h_ref_W_m2K": 130.0, "h_at_t0_W_m2K": 179.81},
      "wall-outer":  {"h_ref_W_m2K": 85.0,  "h_at_t0_W_m2K": 117.57},
      "pad-backing-exposed": {"h_ref_W_m2K": 40.0, "h_at_t0_W_m2K": 55.33}
    },
    "basis": "prescribed inputs, not solved airflow (PRD section 6)"
  },

  "materials": {
    "MAT-01": {"name": "grey iron", "density_kg_m3": 7200, "cp_J_kgK": 447, "k_W_mK": 52,
               "zones": ["cheek_out", "cheek_in", "vane_01..vane_20", "hat"]},
    "MAT-02": {"name": "pad compound", "density_kg_m3": 2500, "cp_J_kgK": 900, "k_W_mK": 1.2,
               "zones": ["outerpad", "innerpad"]},
    "MAT-03": {"name": "backing steel", "density_kg_m3": 8030, "cp_J_kgK": 502, "k_W_mK": 16.3,
               "zones": ["bp_outer", "bp_inner"]}
  },

  "initial_conditions": {"T_initial_K": 300.0, "T_ambient_K": 300.0},

  "numerics": {
    "precision": "double",
    "transient": true,
    "energy_equation": true,
    "flow_equations": false,
    "dt_s": 0.01,
    "full_steps": 354,
    "final_step_s": 0.000681,
    "total_steps": 355,
    "end_time_s": 3.540681,
    "load_update_every_steps_max": 10,
    "h_update_every_steps_max": 25,
    "window_value_rule": "exact interval average of the ramp (mid-time value for a linear ramp)",
    "iterations_per_step_start": 5,
    "energy_residual_target": 1e-8,
    "tangential_velocity_limit_m3_s_per_rad_s": 1.592987e-4
  },

  "mesh_start": {
    "global_min_mm": 2.2, "global_max_mm": 20, "growth": 1.2, "curvature_angle_deg": 18,
    "local_mm": {"cheeks": 4, "vanes": 5, "hat": 8},
    "method": "poly-hexcore, no inflation, shared topology, all regions solid"
  },

  "acceptance": {
    "energy_ratio_band_pct": [90, 110],
    "applied_vs_vehicle_pct": 2.0,
    "limits_K": {"THM-01": 923, "THM-02": 623, "THM-04": 1143},
    "limit_bulk_rise_K": {"THM-03": 60}
  },

  "deferred": [
    {"id": "GEO-05", "reason": "cross-drilling breaks the axisymmetry the solid-motion model needs", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"},
    {"id": "THM-06", "reason": "calliper not in the thermal model (DV-09)", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"},
    {"id": "DV-07", "reason": "fade / dyno", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"},
    {"id": "DV-08", "reason": "cracking", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"},
    {"id": "DV-09", "reason": "calliper / fluid temperature", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"},
    {"id": "DV-10", "reason": "repeated stops", "owner": "Chassis / Foundation Brake", "phase": "Phase 3"}
  ],
  "open": [
    {"id": "PKG-06", "reason": "no wheel geometry in scope"}
  ],
  "findings": []
}
```

`tangential_velocity_limit_m3_s_per_rad_s`, `iterations_per_step_start`,
`energy_residual_target` and the two update cadences all come from PRD
section 6.

## Validation checklist (run it before recording the hash)

1. Parse the file with a JSON parser (a trailing comma is a Gate 0 failure).
2. Every top-level key above is present.
3. Recompute `stop_time_s`, `energy_per_front_rotor_J` and `omega0_rad_s` from the
   `vehicle` block with a fresh calculation and compare within 0.1 %.
4. `omega0_rad_s < 0` and `rotation.vane_sweep_dtheta_dr_sign == 1`.
5. `numerics.full_steps * dt_s + final_step_s == end_time_s` within 1e-6 s.
6. The windowed integral of `laws.power_W` equals `energy_per_front_rotor_J`
   within 0.01 %.
7. Material values equal PRD section 7 MAT-01 to MAT-03 exactly.
8. Hash the file and store the hash in `BUILD_STATE.json` -> `artifacts.case_json`.
