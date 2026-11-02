# The naming chain - what survives each hop

No name written in SolidWorks reaches Fluent. Every name the solver uses is
created in SpaceClaim and carried by the PMDB.

```
SolidWorks     part files named cheek_out, cheek_in, vanes, hat, outerpad, innerpad,
   |           bp_outer, bp_inner, calliper; assembly brake.SLDASM
   |           faces: no names exported at all
   v  export_document (STEP)
STEP           PRODUCT('cheek_out') ... present in the text, but NOT used by the importer
   |           ADVANCED_FACE entities: none named
   v  SpaceClaim import
SpaceClaim     bodies arrive named after a SolidWorks FEATURE (the predecessor's body
   |           came in as 'CirPattern1'); the vanes arrive as 20 bodies with
   |           feature-derived names in no reliable order
   |           -> identify each body by measured volume + centroid + bbox
   |           -> rename to the PRD name (Body.name is settable)
   |           -> create 27 body named selections + wall-vent + wall-outer
   v  export PMDB
PMDB           bodies and named selections carried
   v  Fluent Meshing import
Fluent         cell zones from the bodies; face zones from the named selections,
               SPLIT PER BODY; leftover walls named after their cell zone
```

## 1. Rules

1. **Name the SolidWorks parts exactly as the PRD** (`cheek_out`, not `Cheek_Out`
   or `cheekOut`). It does not help the solver, but it makes `cad_report.json`,
   the STEP and every human reading them agree.
2. **SpaceClaim identifies by geometry.** The measured signatures in
   `cad_report.json` are the lookup table. Vanes are told apart by centroid angle:
   vane_k at 17.917 + (k - 1) x 18 deg, r = 130.154 mm. Keep `vane_01` to
   `vane_20` in the same angular order as `cad_report.json`.
3. **Named selections, exactly:** `cheek_out`, `cheek_in`, `hat`, `vane_01` to
   `vane_20`, `outerpad`, `innerpad`, `bp_outer`, `bp_inner`, `wall-vent`,
   `wall-outer`. Twenty-nine in all. No selection on any contact face.
4. **Fluent's zone names are read, not assumed.** The mesh report's zone map
   (actual Fluent name -> PRD name) is the only source of zone names for setup.
   The predecessor's pads arrived as `geom-1-outerpad`; the leftover pad wall came
   out as `geom-1-outerpad:1`. Do not "clean up" inherited prefixes; map them.
5. **Named selections arrive split per body.** `wall-vent` touches 22 bodies (2
   cheeks and 20 vanes), so it can arrive as up to 22 face zones (for example
   `wall-vent`, `wall-vent.1`, ... or with a body suffix). `wall-outer` touches 3
   bodies (the two cheeks and the hat). Addressing the bare string reaches one
   piece and leaves the rest with **no convection at all**, silently. Resolve every
   piece by prefix and **assert the summed area** (142 865.51 mm^2 for wall-vent).
6. **The opposite trap:** a glob for a name Fluent never created (for example
   `wall-rotor*` or `wall-pad*`) matches nothing, silently. Build the exposed pad
   and backing wall list at runtime by subtracting the named set and the
   interface walls from all walls of the pad and backing zones, then assert the
   area is non-zero.
7. **Reserved substrings.** Fluent assigns boundary types by substring. Never name
   anything with `inlet`, `outlet` or `symmetry` in it: a selection called
   `vent-inlet` would become a velocity inlet and the case would stop being a
   conduction problem.
8. **Side identification is measured.** To know which side of a pad/cheek
   interface is the pad, read the adjacent cell zone's material properties:
   pad cp 900 and k 1.2; iron cp 447 and k 52. Do not read `density` for this with
   flow equations off: the predecessor got 0.0 on a solid and the identification
   failed silently. Do not infer the side from a name: the convention inverted
   between builds.

## 2. What each role must write down

| Role | Records |
|---|---|
| solidworks-engineer | part names, per-body measured signature, vane angular order |
| spaceclaim-engineer | imported name -> PRD name for all 28 bodies with the signature that matched; named selection -> faces -> area |
| fluent-engineer | Fluent cell zone -> PRD name; each named selection -> list of face zones -> summed area; coupled pair -> both zones -> area |
| lead | checks that the three maps compose without a gap: every PRD name reaches exactly one Fluent zone |
