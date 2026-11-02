# Handoff failure modes - symptom, cause, owner

Every row here was seen in the predecessor workflow or follows directly from this
PRD's geometry. Most of them **reported success while being wrong**.

| Symptom | Likely cause | Owner | Fix |
|---|---|---|---|
| body volume right, centroid off by a few mm | body built on the wrong plane or offset; volume is invariant under translation | solidworks-engineer | rebuild at true global position; gate on centroid and bbox too |
| vane_01 centroid near (-124, -40) | wrong circle branch (the 153 to 158 deg branch at r = 95) | solidworks-engineer | keep the branch whose angle increases with r |
| vane_01 centroid at negative y | vanes mirrored (hand reversed) | solidworks-engineer | rebuild; the PRD fixes the hand |
| 20 vanes reported, 1 body exists | circular-pattern feature | solidworks-engineer | one closed profile per vane from rotated coordinates |
| hat z range wrong (for example -43 to +16) | revolve direction or reverse flag trusted | solidworks-engineer | measure the bbox; rebuild |
| calliper volume about 1 % off, band section area wrong at z = +40 | windows or bores on the wrong z band | solidworks-engineer | use the band section areas in PRD section 4 to localise |
| STEP has fewer than 28 solids | assembly missing parts (run 1: 23 solids, 5 parts never inserted), a part exported as surfaces, or a body merged | solidworks-engineer | check `assembly.component_count` = 9 before export; re-export; count `MANIFOLD_SOLID_BREP` |
| `PermissionError: [Errno 13]` opening `brake.pmdb` | the export wrote a folder `brake.pmdb\` holding the file `brake.pmdb` | whoever opened it | open and hash `brake.pmdb\brake.pmdb` |
| import volume off by 16 387 or 1e9 | unit context misread, or a scale applied | whoever scaled; else solidworks-engineer | never scale; measure |
| every geometric query returns zero faces | wrong scale (the `SI_UNIT` text check passed on an inch file) | spaceclaim-engineer to report | measure scale first |
| bodies imported with names like `CirPattern1` | normal: STEP body names are feature-derived | - | identify by signature, then rename |
| calliper match ambiguous or zero | stale signature, or the calliper is wrong | spaceclaim-engineer (report) / solidworks-engineer (if the CAD is wrong) | use this run's measured signature; unique match only |
| 28 zones in Fluent, one near 6.17e-4 m^3 | calliper suppressed instead of deleted | spaceclaim-engineer | delete the body; prove by re-read volume arithmetic |
| Geometry service dies after a delete | handles invalidated by the deletion | spaceclaim-engineer | delete last, then re-read |
| a pad/cheek contact covers the whole cheek face (about 57 177 mm^2) | pad outline not imprinted | spaceclaim-engineer / fluent-engineer | imprint; re-measure 5 864.31 mm^2 |
| wall-vent in Fluent equals the before-imprint area (about 167 038 mm^2) | shared topology carved nothing; interfaces uncoupled | fluent-engineer (mesh) | apply shared topology; count 45 coupled pairs |
| fewer than 45 coupled pairs | a contact face was tagged, or bodies do not abut in CAD | spaceclaim-engineer or solidworks-engineer | read which contact is missing and measure its gap |
| temperatures flat at 300 K | STEP meshed instead of PMDB, or heat source on a wall that touches nothing | fluent-engineer | mesh from PMDB; confirm both pad/cheek coupled pairs exist |
| temperatures rise without bound, or a cell pinned at a clip limit | convection resolved to zero area, or a friction patch was tagged and the pad isolated | fluent-engineer / spaceclaim-engineer | resolve split selections and assert areas; never tag contacts |
| only part of the vent gets convection | the bare `wall-vent` string addressed one of up to 22 pieces | fluent-engineer | resolve by prefix; assert 142 865.51 mm^2 |
| energy ratio far below 90 % | a non-axisymmetric zone (vanes or hat) was rotated; the predecessor lost 92 % of the energy this way | fluent-engineer | rotate only `cheek_out` and `cheek_in`; read the list back |
| pad and rotor temperatures look swapped | interface side inferred from a name | fluent-engineer | identify side by cp and k of the adjacent cell zone |
| a solver boundary named `...inlet...` behaves as a flow inlet | reserved substring in a name | spaceclaim-engineer | rename without `inlet`, `outlet`, `symmetry` |
| a CAD screenshot shows holes or a shape that is not in `brake.step` | a second model was built or the wrong file was imported | solidworks-engineer / spaceclaim-engineer | Gate 2 failure; every visual is of the frozen STEP |
| frozen CAD hash changed after Gate 1 | a part or the assembly was saved during a later stage | whoever saved it | Gate failure; restore or halt |
