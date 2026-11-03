# Gate-review checklists - what the lead reads and compares (PRD H1.2, fast run profile)

Use this when a completion notice arrives. For each gate: open the artifact with
your own file tool, recompute hashes, and compare every row below. Print the
table to the user with `expected / measured / delta / tolerance / result`.

**Make it one step.** Write one read-only check (in `execute_code`, or a file
`00_lead\checks\gate<n>_check.py` run with
`C:/solidpilot/.venv/Scripts/python.exe` or a sandbox `python3` on the mount) that loads the JSON, hashes the files,
counts the STEP solids and prints the whole table. A check may only read, hash
and compare. It never imports `ansys`, `pyfluent`, `ansys.geometry` or a
SolidPilot client, never launches an application, and never writes into a stage
folder. Anything more is a specialist's job.

Rules that apply to every gate:

- **Common fields.** Every JSON artifact must carry `run_id` (this run),
  `prd_revision` = `"H1.2"`, `producing_role`, `started_at`, `finished_at`,
  `status`, and the SHA-256 of its upstream inputs. A missing common field is a
  FAIL of the gate (the artifact cannot be traced).
- **Timing.** Copy the report's `timing` block into `BUILD_STATE.timing.<gate>`.
  A missing block is a finding against the owner, not a gate failure.
- **Hashes.** Recompute every hash the artifact claims. A mismatch means the file
  changed after it was reported: FAIL.
- **Missing keys.** A required key that is absent or `null` without a `reason`
  is a FAIL. A `null` with a reason is still a FAIL of that check unless the
  check is explicitly "measure and report".
- **Units.** Keys carry units (`_m3`, `_mm`, `_mm2`, `_k`, `_j`). Convert once,
  explicitly, and write the conversion in your table (1 m^3 = 1e9 mm^3).
- **Delta.** `delta_pct = (measured - expected) / expected x 100`. For centroids
  and bbox, report the absolute difference in mm on each axis.

---

## Gate 0 - `00_lead\case.json` (your own)

| Check | Expected | Tolerance |
|---|---|---|
| `derived.stop_time_s` | 3.54068 | 0.1 % |
| `derived.energy_per_front_rotor_J` | 243 055.6 | 0.1 % |
| `derived.omega0_rad_s` | -84.1751 (sign negative) | 0.1 % |
| `derived.stopping_distance_m` | 49.176 | printed precision |
| `derived.mean_power_W`, `peak_power_W` | 68 646.6, 137 293.1 | printed precision |
| `derived.omega_ref_rad_s` | 56.1167 | printed precision |
| `derived.pad_contact_area_m2` | 5.864306e-3 | printed precision |
| `derived.q_layer_peak_W_m3`, `q_layer_mean_W_m3` | 5.8529e9, 2.9265e9 | printed precision |
| `numerics.full_steps`, `numerics.final_step_s` | 354, 0.000681 | exact |
| `materials` | MAT-01, MAT-02, MAT-03 values of PRD section 7 | exact |
| `deferred` | GEO-05, THM-06, DV-07 to DV-10 | all present |

---

## Gate 1 - `10_cad\cad_report.json` (solidworks-engineer)

**Check these three first.** If any fails, stop reading: the gate is FAIL and
the owner is solidworks-engineer. Run 1 let a 23-solid STEP (assembly missing 5
parts) through to SpaceClaim.

| Check | Expected | How |
|---|---|---|
| `assembly.component_count` | **9** (cheek_out, cheek_in, vanes, hat, outerpad, innerpad, bp_outer, bp_inner, calliper) | read the key and the name list |
| `step.manifold_solid_count` | **28** | read the key |
| your own STEP text count | 28 `MANIFOLD_SOLID_BREP`, 10 `PRODUCT` | text scan below |

API idiom (read-only text scan, PowerShell):

```
(Select-String -Path "<RUN>\10_cad\brake.step" -Pattern "MANIFOLD_SOLID_BREP" -AllMatches).Matches.Count   # 28
(Select-String -Path "<RUN>\10_cad\brake.step" -Pattern "= ?PRODUCT ?\(" -AllMatches).Matches.Count        # 10
```

`^#[0-9]*=PRODUCT` returns 0 on a real SolidWorks STEP (it writes
`#123 = PRODUCT ( ... )` with spaces) and "passes" by failing to match. Never
gate on a pattern that cannot match, and never gate scale on `SI_UNIT` text.

Tolerances (PRD section 4): volume 1 %, centroid 0.1 mm, bbox 0.05 mm.

**Bodies** (`bodies[]`, exactly 28 rows, names unique, each with `bbox_method`):

| name | volume_m3 | centroid_mm | bbox or z band (mm) |
|---|---|---|---|
| cheek_out | 5.717699e-4 | (0, 0, +11.000) | x, y -165 to 165; z +6 to +16 |
| cheek_in | 5.717699e-4 | (0, 0, -11.000) | x, y -165 to 165; z -16 to -6 |
| vane_01 | 7.251627e-6 | (123.842, 40.040, 0) | x 94.922 to 143.121; y -3.850 to 90.942; z -6 to +6 |
| vane_02 to vane_20 | 7.251627e-6 each | table below | z -6 to +6 |
| hat | 5.132043e-4 | (0, 0, +18.095) | x, y -95 to 95; z -16 to +43 |
| outerpad | 7.037168e-5 | (134.600, 0, +22.000) | z +16 to +28 |
| innerpad | 7.037168e-5 | (134.600, 0, -22.000) | z -28 to -16 |
| bp_outer | 4.398230e-5 | (135.111, 0, +31.000) | z +28 to +34 |
| bp_inner | 4.398230e-5 | (135.111, 0, -31.000) | z -34 to -28 |
| calliper | 6.170815e-4 | (146.143, 0.000, +0.369) | x 81.245 to 200.000; y -98.418 to 98.418; z -57 to +57 |

Derived from PRD section 3.5: pad x extent 103.923 to 160.000, y -80.000 to
80.000; backing x 99.593 to 165.000, y -82.500 to 82.500.

**Vane centroids** (r = 130.154 mm, angle 17.917 + (k - 1) x 18 deg, z = 0):

| k | x mm | y mm | k | x mm | y mm |
|---|---|---|---|---|---|
| 1 | 123.842 | 40.040 | 11 | -123.842 | -40.040 |
| 2 | 105.408 | 76.350 | 12 | -105.408 | -76.350 |
| 3 | 76.655 | 105.186 | 13 | -76.655 | -105.186 |
| 4 | 40.399 | 123.725 | 14 | -40.399 | -123.725 |
| 5 | 0.189 | 130.154 | 15 | -0.189 | -130.154 |
| 6 | -40.040 | 123.842 | 16 | 40.040 | -123.842 |
| 7 | -76.350 | 105.408 | 17 | 76.350 | -105.408 |
| 8 | -105.186 | 76.655 | 18 | 105.186 | -76.655 |
| 9 | -123.725 | 40.399 | 19 | 123.725 | -40.399 |
| 10 | -130.154 | 0.189 | 20 | 130.154 | -0.189 |

Vane centroids 180 deg away from this table mean the wrong circle branch was
kept; mirrored about X means the hand is reversed. Both are FAIL, owner
solidworks-engineer.

**Sums** (compute them yourself from the rows):

| Check | Expected |
|---|---|
| 20 vanes | 1.450325e-4 m^3 |
| rotor = cheeks + vanes + hat | 1.801777e-3 m^3 (1 801 776.57 mm^3) |
| MAS-01 rotor mass at 7200 kg/m^3 | 12.973 kg (limit 13.5) |
| all 28 bodies | 2.647566e-3 m^3 (2 647 566.01 mm^3) |

**Assembly and export:**

| Key | Expected |
|---|---|
| `interference_mm3` | 0, with `interference_method` named |
| `clearances_mm` pad stack to slot, outboard / inboard | 4.6 / 5.0 |
| `clearances_mm` slot height minus stack | +9.6 (PAD-05 needs >= +4) |
| `clearances_mm` rotor OD to bridge / hat wall to calliper end wall | 13.0 / 11.8 |
| `step.sha256` | equals your recomputed hash |
| `step.product_count` | 10 |
| `native_hashes` | 10 entries (9 SLDPRT + SLDASM), each equal to your recomputed hash |
| `vane_hand` | angle increases with r; rotation clockwise from +Z; consistent with `case.json` |

**Requirements block**: PKG-01 330.0 mm, PKG-02 32.0 mm, PKG-03 5 x dia 14 on
PCD 115, PKG-04 dia 70.0, PKG-05 z = +43.0, MAS-01 12.973 kg, GEO-01 yes, GEO-02
10.0 mm each, GEO-03 12.0 mm, GEO-04 20 vanes, GEO-06 hat on inboard cheek with
inlet gap about 7 mm, PAD-01 60 deg, PAD-02 120 to 160 mm, PAD-03 12 mm, PAD-04
6 mm at r 115 to 165, PAD-05 +9.6 mm and 0 mm^3.

There are no drawings or views to check at Gate 1 in H1.2.

**Result**: PASS only if component count is 9, the STEP has 28 solids (key and
your own count), all 28 rows pass, interference is 0 and all hashes match. Then
freeze the 11 hashes (9 SLDPRT, SLDASM, STEP).

---

## Gate 2 - `20_spaceclaim\tag_report.json` (spaceclaim-engineer, stage script)

| Check | Expected |
|---|---|
| `status` | `PASS` |
| `inputs_sha256["10_cad/brake.step"]`, `["10_cad/cad_report.json"]` | your frozen Gate 1 hashes |
| every `checks[]` row | `pass: true` (import count, OD, z extents, 28-body volume, unique body map, after-delete count, volume drop, 27-body volume, 29 named selections, three before-imprint areas, PMDB written) |
| `body_map` | 28 rows, 28 distinct names, worst score <= 1.0 |
| `named_selections.count` | 29 |
| wall-vent / wall-outer / pad-backing before imprint | 167 037.60 / 240 205.78 / 42 997.28 mm^2, 2 % |
| your SHA-256 of `brake.pmdb\brake.pmdb` | equals `pmdb.sha256`; freeze it |
| `spaceclaim_left_running` | `false` |
| `timing.seconds`, `phase_seconds` | copied into `BUILD_STATE.timing.G2` |

The 45 contacts are not measured here; Fluent's 45 coupled pairs prove them at
Gate 3.

---

## Gate 3 - `30_fluent\results.json` (fluent-engineer, stage script)

| Check | Expected |
|---|---|
| `status` | `PASS` |
| `inputs_sha256` | your frozen PMDB inner-file and `case.json` hashes |
| every `checks[]` row | `pass: true` |
| `mesh.solid_zones` / fluid | 27 PRD names / 0 |
| `mesh.coupled_pairs` | 45 |
| friction areas | 5 864.31 mm^2 each, 2 % |
| meshed volume | 2 030 484.53 mm^3, 2 % |
| `layer_material_readback` | `grey-iron` on both friction walls |
| applied energy vs closed form | 2 % |
| stored / applied | 90 to 110 % |
| stored energy, rotor max T, pad max T | rise in every `history` window |
| `history[-1].t_s` | 3.540681 s (the full stop, default) |
| `live_contour.displayed` | `true` (Fluent is left open on purpose) |
| `timing.seconds`, `phase_seconds` | copied into `BUILD_STATE.timing.G3` |

Quote the `summary` block: peak and final friction-face temperatures (rotor and
pad), applied and stored energy, and the fraction of the stop energy applied.
It is a heating demonstration, not a THM verdict.

---

## Gate 4 - your gate summary

`00_lead\gate_log.md` (the printed gate tables verbatim) and the final
`BUILD_STATE.json`: gates, timing table, Gate 3 summary, and a disposition for
every PRD section 7 ID and DV item per `specs/handoffs.md` Gate 4. No PDF, no
images.
