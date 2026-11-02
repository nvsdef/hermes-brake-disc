---
name: brake-design-review
description: "Gate 4: disposition every requirement, write review.json."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, lead, review, verdict]
---

# brake-design-review - the verdict (PRD H1.2)

You turn the stage artifacts into one engineering answer: can this brake
withstand the frictional heat of one stop, and what would you change first? You
write it once into `50_report\review.json` and render `review.md` from it.
`brake-report` consumes `review.json` and adjudicates nothing again.

| Reference | Open it when |
|---|---|
| `references/disposition-rules.md` | for every row: which artifact and key answer it, and the rule |
| `references/review-json-schema.md` | when writing `review.json` and `review.md` |
| `references/recommendation-levers.md` | when writing the first change and the ranked recommendations |
| `references/resolution-remediation.md` | a thermal row is NOT ADJUDICABLE for resolution |
| `references/model-blind-spots.md` | when writing the limitations |
| `references/interpretation.md` | a number looks surprising, or before you recommend anything |

## 1. Checklist

**Preconditions**
- [ ] Gates 1, 2 and 3 passed, or the failing gate is recorded. Rows downstream
      of a halt are OPEN, reason "stage not reached".
- [ ] Energy audit closed (`results.json` -> `energy_audit`): ratio 90 to 110 %,
      `E_applied_j` within +/-2 % of 243 055.6 J, `coverage.covers_full_stop`
      true. If not, THM-01 to THM-04 are NOT ADJUDICABLE with the audit numbers
      as the rationale.
- [ ] No temperature equals a solver clip limit (the predecessor saw 5000 K).
- [ ] Read this run's wall-normal and in-plane cell sizes at both friction faces
      from `mesh_report.json`. Never carry a size from another run.

**Rows (37 = 27 requirement IDs + DV-01 to DV-10)**
- [ ] CAD rows PKG, MAS, GEO, PAD from `10_cad\cad_report.json` ->
      `requirements`, `clearances_mm`. GEO-06 also cites
      `20_spaceclaim\cad_section_9deg.png` and the hat/cheek_in contact.
- [ ] MAT-01 to MAT-03 from the `setup_report.json` readback (exact match PASS,
      difference FAIL, missing OPEN).
- [ ] THM-01 to THM-05 from `results.json` with the range rule (section 3).
- [ ] Deferred rows GEO-05, THM-06, DV-07 to DV-10: DEFERRED, owner Chassis /
      Foundation Brake, phase Phase 3. PKG-06: OPEN (no wheel geometry).
- [ ] DV rows composed from their requirement rows (worst of FAIL, NOT
      ADJUDICABLE, OPEN, PASS). DV-05 is `E_applied_j` / 243 055.6 J within +/-2 %.
- [ ] Every row has the nine fields: `required`, `measured`, `unit`,
      `evidence_file`, `json_key`, `disposition`, `rationale`, `owner`,
      `next_step`.

**Beyond the rows**
- [ ] `deliverables`: the 2D drawing listed with status `DESCOPED` (PRD H1.2
      section 8, item 5, descoped by the user). It is not a requirement row and
      never lowers the workflow status.
- [ ] `timing`: one row per stage from `BUILD_STATE.timing` (section 4).
- [ ] `first_change`: parameter, from, to, expected effect with a unit, the
      arithmetic, and the requirement it touches.
- [ ] `limitations`, conditional on this run's data.
- [ ] Write `review.json`, render `review.md`, print the requirement table.

## 2. State the answer first

At the top of `review.md` and in chat:

```
Pad friction surface (THM-02, limit 623 K):  range [<cell max>, <layer max>] K, peak at t = <s>
   keys: results.json -> <cell key>, <layer key>
   pad wall-normal cell <x> mm vs penetration depth <sqrt(alpha x t_peak)> mm; <n> cells across
   disposition: <PASS | FAIL | NOT ADJUDICABLE>
Rotor friction surface (THM-01, limit 923 K): range [<a>, <b>] K ... disposition
All rotor surfaces (THM-04, limit 1143 K):    range [<a>, <b>] K ... disposition
Rotor bulk rise (THM-03, limit 60 K):         <x> K (upper estimate 41.9 K) ... disposition
Energy audit: applied <J> (<+/-%> vs 243 055.6 J), ratio <%>, convected <%>
Verdict: <one sentence>. Governing requirement: THM-02 (expected) / <actual>.
First change: <parameter from -> to>, expected effect <number with unit>.
2D drawing: DESCOPED (PRD H1.2). Run time to Gate 2: <min> (target 25 to 35).
```

The pad governs: about 40 times lower conductivity than the iron and a lower
limit. A review without the pad row answers the wrong question.

## 3. Dispositions (closed set) and the thermal range rule

| Disposition | Allowed when |
|---|---|
| **PASS** | evidence key exists, measurement credible (thermal: audit closed, face resolved), target met |
| **FAIL** | as PASS but target missed; also a thermal row whose cell maximum alone exceeds the limit |
| **NOT ADJUDICABLE** | range straddles the limit, wall-normal cell coarser than sqrt(alpha x t) at the peak, audit not closed, or a readback contradicts the declaration |
| **OPEN** | no in-scope model produces the measurement, or the stage was not reached |
| **DEFERRED** | the PRD defers it: GEO-05, THM-06, DV-07 to DV-10 |

No other words in a disposition field. Qualifiers go into `rationale`. Report
cell max and wall-layer max as a range (THM-04: cell max and wall-facet max over
all rotor walls). Record cells across the penetration depth; fewer than 5 is a
finding. A missing mesh-sensitivity study is a finding, not NOT ADJUDICABLE.

## 4. The timing table

```
stage   owner                 minutes  tool_calls  app_launches            repairs
G0      lead                  1.4      -           -                       0
G1      solidworks-engineer   14.8     212         solidworks_documents 10 0
G2      spaceclaim-engineer   9.6      41          spaceclaim_sessions 1   0
G3      fluent-engineer       ...      ...         fluent_sessions 1       0
G4      lead                  ...      -           -                       -
total / to Gate 2 pass        ... / ...
```

Values come from `BUILD_STATE.json` -> `timing`; a missing value is `null` with
the reason. Exceeding the 25 to 35 min target to Gate 2 is a finding, not a
disposition.

## Verification

- `review.json` has 37 rows, each with the nine fields, and every disposition is
  one of the five closed-set words.
- Every non-null `measured` value can be found at `evidence_file` -> `json_key`
  (open three at random and check).
- Every THM-01, THM-02 and THM-04 row carries both range keys, the friction-face
  wall-normal cell size and the penetration depth it was compared with. No NOT
  ADJUDICABLE row quotes a margin.
- `deliverables` lists the 2D drawing as `DESCOPED`, and `timing` has a row per
  stage.
- `first_change` has a parameter, a from and to value, a quantified effect with
  unit, and the requirement it touches.
- `review.md` was rendered from `review.json` (same dispositions, same numbers)
  and `completed_gates` contains `"G4"` only after `brake-report` also passes.
