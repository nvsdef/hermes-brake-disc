# Report structure - sections, content and captions (PRD H1.2)

Target length 10 to 15 pages. Figures at a modest height (about 70 to 75 mm) so
two fit on a page. There is no drawing page: 2D drawings are descoped in H1.2.

## Section order

| # | Section | Content | Source |
|---|---|---|---|
| 1 | **Verdict** (page 1) | title "FR-330V vented front brake - single-stop thermal design verification (fictional, educational)", run id, PRD H1.2, date, workflow status word, engineering verdict sentence, governing requirement and its disposition, energy audit line, first change with quantified effect | `review.json` -> `headline`, `workflow_status`, `engineering_verdict`, `first_change` |
| 2 | **Requirement table** | 27 rows: ID, class, requirement, measured (ranges as `[a, b] K`), unit, disposition, evidence (file -> key) | `review.json` -> `rows` |
| 3 | **DV summary** | DV-01 to DV-10: composed disposition, constituents, owner, phase | `review.json` rows DV-* |
| 4 | **Duty cycle** | the PRD section 5 table as computed (formula, value, unit), the P(t), omega(t) and h(t) laws, a small plot of P(t) and the three h(t) curves over 0 to 3.540681 s | `00_lead\case.json` (a plot of the declared laws is a picture of the input, not a result) |
| 5 | **Geometry** | parts table (9 parts, 28 bodies), assembly component count, STEP solid count, per-body volume expected vs measured with delta, interference, clearances; rotation note "rotates clockwise viewed from +Z (outboard), omega0 = -84.1751 rad/s"; SpaceClaim `cad_iso.png` and `cad_section_9deg.png` | `cad_report.json`, `20_spaceclaim\cad_*.png` |
| 6 | **Geometry preparation** | calliper removal arithmetic, 27 bodies, named selections, before-imprint areas predicted vs measured (wall-vent 167 037.60, wall-outer 240 205.78, pad/backing 42 997.28 mm^2), 45 contacts; `named_selections.png` | `tag_report.json`, `named_selections.png` |
| 7 | **Mesh** | zone and pair counts, quality (max surface skewness; volumetric skewness null with reason), cells + nodes vs cap, per-zone volume deltas, after-imprint areas (142 865.51 / 228 477.17 / 31 268.67 mm^2), friction-face cell sizes vs penetration depths; full mesh and vent close-up images | `mesh_report.json`, `30_fluent\` mesh images |
| 8 | **Setup readback** | materials per zone group, rotating zones, h schedules, layer model, dt and steps, pre-solve energy integral, tangential-velocity check | `setup_report.json` |
| 9 | **Results** | peak table (cell max and layer max, time of each) for rotor friction surface, pad friction surface, all rotor surfaces; bulk rise; peak-history plot with limits drawn; contours with units, time and range | `results.json`, `histories\*.csv`, contour images |
| 10 | **Energy audit** | E_vehicle, E_applied (and % vs vehicle), E_stored, E_conv, ratio, residual with sign, convected fraction | `results.json` -> `energy_audit`, `review.json` -> `energy_audit` |
| 11 | **Thermal credibility** | resolution table, what the two ends of each range are, why each THM disposition is what it is | `review.json` -> `resolution`, THM rows |
| 12 | **Limitations** | the conditional list from the review | `review.json` -> `limitations` |
| 13 | **Recommendations** | first change, then ranked levers with magnitude, cost and requirement touched | `review.json` -> `first_change`, `recommendations` |
| 14 | **Run record** | deliverables table (2D drawing: DESCOPED, PRD H1.2 section 8 item 5; CAD screenshots: DELIVERED); per-stage timing table (stage, owner, minutes, tool calls, app launches, repairs; total and minutes to Gate 2 pass vs the 25 to 35 min target) | `review.json` -> `deliverables`, `timing` |
| 15 | **Findings and manifest** | spec contradictions, package defects, repairs made (with both numbers); artifact manifest (stage, file, first 16 hex of SHA-256, producing role) | `BUILD_STATE.json` -> `findings`, `manifest.json` |

A plot drawn by the composition script from a history CSV is allowed: it is a
picture of stored data, not a new computation. Label axes with units, draw the
limit as a horizontal line, and put the CSV file name in the caption.

## Visuals from every stage (PRD section 8, item 5)

| Stage | Figure | Must show | Caption must say |
|---|---|---|---|
| CAD (captured in SpaceClaim) | `cad_iso.png` | the full assembly including the calliper | "Assembly as exported from SolidWorks and imported to SpaceClaim, 28 bodies; the calliper is removed only from the simulation copy" |
| CAD (captured in SpaceClaim) | `cad_section_9deg.png` | hat web on the inboard cheek, open inlet of about 7 mm | "GEO-06: section at 9 deg through the vent inlet; hat lands on cheek_in at r = 95, inlet open" |
| Geometry prep | `named_selections.png` | wall-vent and wall-outer in distinct colours | the measured wall-vent area before imprint against 167 037.60 mm^2 |
| Mesh | full mesh image | the whole mesh | cells + nodes |
| Mesh | vent close-up image | vane passages meshed | "vent faces are distinct walls (THM-05 modelled, not validated)" |
| Solve | contour, pad friction face at peak time | legend in K, time stamp, range | the time, and which quantity the colour map shows (cell values, not the layer maximum) |
| Solve | contour, rotor friction face | smeared annulus | "the warm band covers the swept annulus: rotation applied", or the defect if not |
| Solve | peak-history plot | cell max and layer max against time, limits drawn | where the peak occurs relative to ts |

If a contour shows the end-of-stop field, the caption says "end-of-stop field
(t = 3.540681 s), not the peak". The predecessor's contour band topped out about
250 K below the reported peak; a "peak temperature" caption on it was wrong by
that much.

## Page 1 template

```
FR-330V vented front brake - single-stop thermal design verification
Fictional, educational design. Not a certified brake.
Run FR330V-20261001-0930    PRD H1.2    2026-10-01

WORKFLOW STATUS: complete_with_findings
VERDICT: <engineering_verdict>
GOVERNING: THM-02 pad friction surface <= 623 K -> <disposition>, range [<a>, <b>] K
ENERGY AUDIT: applied <+x.xx %> vs vehicle, ratio <yy.y %>, convected <z.zz %>
FIRST CHANGE: <text> - expected effect <number unit>
RUN TIME: <total> min (Gate 2 passed at <m> min; target 25 to 35). 2D drawing descoped (H1.2).

[requirement table]
```

If the run halted, page 1 says `WORKFLOW STATUS: halted`, names the gate, and
prints the expected and measured numbers from `BUILD_STATE.json` -> `halt`
before anything else.
