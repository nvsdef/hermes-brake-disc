# Mesh-stage failure catalogue

Look up the symptom first. The "Owner" column says whether you repair it (two
repairs at most) or return it to the lead with the numbers.

| Symptom | Likely cause | Owner | Action |
|---|---|---|---|
| Only a `.step` in the input folder | Tagging stage not run, or PMDB not written | upstream | Refuse. STEP drops every face name; the solve runs flat at 300 K with no error |
| PMDB hash differs from `tag_report.json` | File replaced or re-exported after Gate 2 | upstream | BLOCKED; report both hashes |
| 28 solid zones | Calliper not deleted in SpaceClaim | upstream | Report the extra zone's volume against 6.170815e-4 m^3. Do not delete it here |
| 26 or fewer solid zones | A body merged or lost at import or share topology | upstream or you | Compare zone volumes with PRD; if two bodies merged, the merged volume is their sum |
| One or more fluid zones | Region type guessed from an enclosure shape | you | Set every region to solid before the volume fill. The gate is 0 fluid |
| 27 bodies become one zone | Share topology merged bodies instead of faces | you | Share faces, not bodies. Re-import |
| `RuntimeError ... S_ExecuteTask: An error occured during task update` | Share Topology task missing or not executed | you | Read the stdout transcript. See `share-topology.md` |
| `CONFORMAL_TESSELLATION_FAILED`, `node insertion failed at (x y z)`, `SIGSEGV at Node 0` | Micron sliver at a junction | upstream | Convert the coordinates to r, theta, z; name the body pair; return as a CAD defect |
| Fewer than 45 coupled pairs | Share topology did not imprint, a gap in CAD, or a named selection over an interface | you, then upstream | Re-execute Apply Share Topology once. If still short, list the missing class and body pairs and return |
| 45 pairs but a class count is wrong (for example 41 / 0) | Pairs sit on wrong surfaces, or an unexpected hat/vane face pair | upstream | Report the class counts and areas |
| A pair's shadow is not `Coupled` | Named selection overrode shared topology | upstream | Report the pair name. A later solve would run away |
| Friction patch area about 57 177 mm^2 | Pad outline not imprinted; whole cheek face coupled | you, then upstream | Re-execute share topology once; then return |
| Meshed `wall-vent` about 167 037.6 mm^2 instead of 142 865.51 | No carving: vane footprints not imprinted | you, then upstream | Same failure as the pair count, seen from the other side |
| Only one `wall-vent` zone found | Bare name addressed, not expanded | you | Expand by prefix; expect about 22 zones; check the summed area |
| A wall list built by `wall-*` misses pad-stack walls | Leftovers are named after the cell zone (`geom-1-outerpad:1`) | you | Build by subtraction |
| Max surface skewness not found in transcript | Regex missed the format (a trailing full stop broke one parser) | you | Unparsed is FAIL. Fix the parser, keep the raw line in the report |
| Volumetric skewness reads exactly 0.0 everywhere | Not reported by Fluent 2026 R1 | - | Report `null` with the reason; it does not block (the gate is surface skewness, PRD section 6). Never use `1 - orthogonal quality` |
| Min orthogonal quality below 0.10 | Poor cells, usually at vane tips or the hat web | you | Report the zone and location. Refine locally; re-measure |
| Volume fill fails on the vanes | Min size too coarse for the vane section | you | Reduce local vane size; re-budget elsewhere |
| Cells + nodes at or over 512 000 | Vanes and hat curvature capture | you | Coarsen hat, then vanes, then global max. Never the friction face |
| Per-zone volume off by more than 2 % | Wrong import unit, a merged body, or a mis-mapped zone | you, then upstream | A 1000x or 1e9x error is a unit mistake; fix the import unit. Otherwise return |
| Mesh writes, but the solver sees 0 zones | Surface mesh written, volume mesh not generated | you | Complete the volume mesh step |
| Transcript reports `nodes = 20` | Mesher return values are unreliable | - | Measure after `switch_to_solver()` from the file read back |
| Tool returned "Request timed out" but Fluent finished | MCP transport gave up first | you | Long work goes in a `submit_ansys_job` that connects to the session; inspect the folder before retrying |
| `PermissionError: [Errno 13]` on `brake.pmdb` | The PMDB export is a folder; the file is `brake.pmdb\brake.pmdb` | you | Resolve the inner file once in step 0; hash and import that path (run 1: 13 identical failures) |
| `AttributeError: ... has no attribute ...` on a PyFluent object | A guessed name | you | Look it up in `api-verified.md`; else probe `child_names` in a short step. Never guess twice |
| `KeyError` on a key your own script wrote | Writer and reader of a dict disagree | you | Keep writer and reader in the same short step; `.get()` plus a printed list of missing keys |
| `connect_to_fluent` fails at the first probe | The UNVERIFIED part of the persistent pattern, or the host did not reach `READY` | you | Do not loop. Follow `persistent-session.md` section 5 (one written relaunch) |
| Host job prints `FLUENT GONE` | Fluent crashed or was closed | you | Inspect `30_fluent` and the transcript tail; resume from the last artifact with the one allowed relaunch |
| A 3rd Fluent launch is about to happen | Relaunch habit | you | Forbidden. Stop and return to the lead with both relaunch reasons |
| `job_status` tail is empty for minutes | Child stdout is block-buffered | you | `print(..., flush=True)` everywhere |
| Job state `lost` | Runner killed or the machine restarted | you | List the case folder first; a lost job once had written a complete mesh |
| Next launch dies with `10054` connection reset | A previous Fluent survived `session.exit()` or `job_cancel` and holds the licence | you | Count and reap your own survivors; never kill processes you did not start |
| Mesh-read banner, `/mesh/check` and aspect ratio missing from the report | One process writes one transcript; a "new files since" diff returns nothing | you | Take the newest `fluent-*.trn` on disk |
| Verification takes 30 to 40 minutes | Hundreds of report definitions created | you | Pool about 24 and mutate them |
| A figure of a zone subset is a thumbnail | Auto-scale fits the whole-case grid plane | you | Restore a named view; set camera target and field |
| Figure renders near-black | `camera/position` was set as well | you | Set target and field only |
| Capture cropped to top-left of the screen | Process not DPI-aware | you | `SetProcessDpiAwareness(2)` before capture |
