# H1 decisions and source reconciliation

H1 is a new demo specification derived from the predecessor, not a claim that its historical output met these rules.

1. Exactly one lead and three specialist roles. Use native Hermes delegation, not Claude agent-registration syntax. Dependent stages are sequential; no stage2.5 concurrent drawing.
2. One analysis geometry. Cross-drilling GEO-05 is deferred; do not build a separate unsolved display model. A frozen-model drawing comes after the solve/review.
3. Solid-only transient conduction with prescribed convection is retained. This is not airflow CFD or production brake verification.
4. Teach construction/physics and independent verification. Do not ship old tag.py, mesh.py, solve.py, case scripts or their default result constants. Short API limitations belong in references.
5. Retain the source's corrected calliper windows matching slot z−39..38.6. That correction was not demonstrated in source evidence; H1 must build and measure it. Do not retain the stale caliper signature. Its fresh signature is a handoff artifact.
6. Hat radius is 95 mm, web ends at z = -6. Source references to 97 mm and 1 mm calliper clearance belong to a retired geometry. Hat-to-calliper clearance is 11.8 mm (PRD section 4).
7. Build negative-offset counterparts independently rather than prescribing the source's contradicted copy-and-edit shortcut. Verify frames and effective coordinates.
8. Use g=9.80665 consistently. Cover the complete computed stop, including the final fractional step; do not label354×0.01 s as the exact full stop.
9. Derive vane handedness geometrically. Do not inherit conflicting rotation signs. The prescribed h basis remains an assumption.
10. Preserve energy fault screening but report both loss AND excess;90–110% is an explicit H1 diagnostic band, not a relaxation of DV-05's±2% applied-load requirement or proof of numerical adequacy.
11. Historical cell-max/wall-layer-max ranges are diagnostic, not automatically rigorous bounds on true interface temperature. Thermal requirement signoff needs demonstrated resolution and layer-model credibility. Otherwise NOT ADJUDICABLE.
12. Nominal product dimensions have no invented manufacturing tolerances. Record measurement precision and unmet/missing evidence.

These changes are visible and versioned here so no result appears to pass through an undisclosed requirement change. Original CTS is retained under docs/source for provenance; H1 scope/implementation decisions govern this new demo.

## H1.1 (2026-09-29) - rebuilt after the Nemotron run built a single drilled disc

13. **One authority.** `specs/PRD.md` replaces `specs/product.md` and `specs/analysis.md`. The CTS stays in `docs/source/` as background; the PRD wins on every conflict (PRD section 10).
14. **Checksums for every body.** Volume, centroid and bbox for all 28 bodies were computed by two independent integrations, which agree within 0.01 %. That includes the calliper (6.170815e-4 m^3), which H1 had left "unknown", so its gate had no stop number.
15. **Skills restored at full depth**, per agent, under `agents/<role>/skills/`. They carry the predecessor's measured traps and are adapted to H1.1 numbers. Guidance only: there is still no stage build, tag, mesh or solve script. See `docs/SKILL_STYLE.md`.
16. **Native MCP.** The run path is Hermes `mcp_servers` in a dedicated `brake` profile. `mcp_client.py` is diagnostic only. The SolidPilot tools that were measured broken (`submit_feature_graph`, `rebuild_from_ir`, `auto_dimension_drawing`) are excluded in the profile.
17. **Role loading.** Hermes children get AGENTS.md but not SOUL.md or skills. AGENTS.md carries the role table, and each commission starts with `ROLE: <role>`.
18. **Area basis.** SpaceClaim (Gate 2) checks the areas before imprint: wall-vent 167 037.60 mm^2. Fluent (Gate 3a) checks the areas after imprint: wall-vent 142 865.51 mm^2. The hat step face at z = -6 belongs to wall-outer.
19. **Wall layer** material is grey iron (MAT-01). q''' is scaled by the closed-form contact area, and applied energy is integrated over the measured mesh areas.
20. **Surface skewness** is the mesh gate. Volumetric skewness is recorded as null, because Fluent 2026 R1 does not report it.
21. **Final time step** is 0.000681 s, so the solve ends exactly at ts = 3.540681 s.
22. **Gate 1 inlet section** is cut at 9 deg, mid-passage between vanes. The views live on an undimensioned evidence sheet.
23. **Thermal disposition.** A cell maximum over the limit is FAIL. A range that straddles the limit, or a friction-face cell coarser than the penetration depth, is NOT ADJUDICABLE. A missing mesh-sensitivity study is a finding, not a disposition.

## H1.2 (2026-09-30) - after run 1 (FR330V-20260930-1012)

Run 1: Gate 0 exact; Gate 1 all 28 bodies passed to 0.00 % but took ~90 min
(including a 15 min view sheet and a repair because the assembly held 4 of 9
parts); Gate 2 failed after ~35 SpaceClaim launches (hallucinated API names,
PMDB-folder PermissionError x 13, partial-contact faces excluded); the lead
drifted into doing SpaceClaim itself after context compaction.

24. **2D drawings descoped.** CAD visuals (isometric, 9 deg vent-inlet section,
    named selections) come from SpaceClaim at Gate 2.
25. **One Ansys launch per stage, kept alive.** A holder job starts SpaceClaim or
    Fluent once; short step scripts connect to it. Launch budget 1, 2 with a
    reason, never 3.
26. **Verified API sheets** (`api-verified.md`) built from the installed
    ansys-geometry-core 0.15.5 and ansys-fluent-core 0.41.0 source.
27. **PMDB is a folder** (`brake.pmdb\brake.pmdb`); hash and import the inner file.
28. **Partial-contact rule** stated with a worked table: only faces wholly in
    contact are left untagged.
29. **Fluent is one commission** (mesh, internal mesh gate, setup, solve, post).
30. **Lead rules live in the profile SOUL.md** (system prompt, survives
    compaction, not given to children) and in AGENTS.md section 2.
31. **Speed:** checklist-first SKILL.md files with detail in references; sketch
    data cards for every SolidWorks sketch; per-part measurement; SolidPilot tool
    list cut to 17 (`tools.include`); no polling by the lead; `execute_code`
    for arithmetic; children no longer load `brake-handoff`.
32. **Gate 1** requires `assembly.component_count` 9 read back before STEP export;
    the lead checks it and the STEP solid count itself.

## H1.2 packaging (2026-11-02) - portable, repeatable setup

No engineering content changed: PRD, checksums, skills' procedures and gates are
as in H1.2.

33. **Profile is source, rendered per machine.** `profile/config.template.yaml`
    (full config, three placeholders) and `profile/SOUL.md` are tracked;
    `scripts/install_profile.ps1` renders them. `.local/` keeps only machine
    output. The superseded `examples/hermes-profile.yaml` (H1.1 `tools.exclude`)
    and `examples/servers.template.json` were removed so there is one source.
34. **Fixed conventions, not placeholders:** SolidPilot at `C:\solidpilot` and run
    output in `C:\brake-runs`, because the skills name both paths. Only the
    package root, the ansys-agent root and the Ansys v261 root vary.
35. **Pinned environment.** `profile/environment.json` records the versions the
    skills were verified against; pyansys pins are exact because
    `api-verified.md` was built from that source. `preflight.ps1` fails on a
    mismatch.
36. **Tool inventories are tracked** in `mcp/`. A unit test proves every
    SolidPilot tool outside the 17-tool include filter is mentioned only as a
    tool not to call, and every Ansys tool named in a skill exists.


## H1.2 fast run profile (2026-11-02) - "build once, prep, mesh, heat up"

Run 2 (FR330V-20261102-0936) passed Gates 0 to 2 with agents composing every
call (Gate 1 13 min, Gate 2 18 min) and was cut off in Gate 3 setup after 30 min.
Fluent alone needed about 25 min at the section 6 numerics. The user asked for
an end-to-end run of about 10 minutes, no report, no images.

37. **Fast run profile is the default** (PRD section 6A): coarse mesh (4 to 20 mm;
    cheeks 8, vanes 8, hat 12 mm), first 1.0 s of the stop, dt 0.05 s, 3
    iterations per step. THM-01 to THM-04 are `NOT RUN (fast profile)`. Section 6
    stays the full analysis definition.
38. **Vetted stage scripts for Gates 2 and 3** (`scripts/stages/`), built from
    the code that passed run 2. The specialist launches one, judges its JSON,
    and routes failures; it never rewrites the script mid-run. This reverses
    rule 1 of `docs/SKILL_STYLE.md` ("guidance, not automation") for these two
    stages only; Gate 1 stays agentic through SolidPilot. Measured: Gate 2 62 s
    (was 18 min), Gate 3 126 s.
39. **SpaceClaim face tagging by geometric rule** (surface type, plane z, radius)
    replaces the sampled contact graph. It reproduced the run-2 areas to 0.00 %.
    The 45 contacts are now proven once, by Fluent's coupled-pair count.
40. **Images, the PDF report and the design-review stage are descoped.** Skills
    `brake-report`, `brake-design-review`, `sc-geometry-tagging`, `fl-meshing`,
    `fl-thermal-solve` and `fl-postprocess-energy` were removed (they remain in
    commit f4d8f2f). Their API sheets and failure tables moved to the new skills'
    `references/`. The only visual is the live Fluent contour left on screen.
41. **No STEP re-import in SolidWorks** (old step A8): about 22 calls in run 2
    for evidence that the per-part reads and SpaceClaim's import already give.
42. **Vane trim is two cuts** (cards R6a, R6b): the three-circle parity cut
    returned `EXTRUSION_FAILED` through SolidPilot in run 2.
43. **Heating gate, not monotonic face temperature.** The friction-face peak
    comes at about 0.2 s and eases as the power ramps down; the gate requires
    stored energy and the bulk rotor and pad maxima to rise in every window,
    and stored / applied within 90 to 110 % (measured 99.6 %).
