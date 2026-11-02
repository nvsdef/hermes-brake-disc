# Interpreting the numbers - before you recommend anything

This page holds the reasoning behind the review checklist. Read it when a number
looks surprising, or before you write the first change.

## 1. Numbers in the review exist on disk

Every measured value names its artifact and dotted key. Every derived value (a
margin, a ratio, a percentage) is computed with a tool from named keys and written
into `review.json` -> `derived` with its arithmetic. A number that exists in no
artifact is not quoted. The predecessor's review carried "1 371 J" where the
artifact said 1 353.66 J, "until t ~ 0.7 s" where the data said 0.600 s, and a
"0.16 to 0.9 %" that existed nowhere. None changed a verdict; all three were
presented as measurements.

- **Margins only on adjudicable rows.** A NOT ADJUDICABLE row has `margin: null`.
  The predecessor quoted a 152 K margin on a pad range [470.69, 630.66] K against
  623 K, off an unnamed volume monitor. There is no number, so there is no margin.
- **Never substitute a field.** If the wall-layer maximum is missing, the range
  has one end and the row is NOT ADJUDICABLE with the reason "upper end missing".
  Never fill it with a volume monitor, an area average or an end-of-stop snapshot.
- **Check that a maximum is a maximum.** Compare the reported run maximum with
  the final-time value in the history CSV. If they are identical and the history
  peaks earlier, the "maximum" is a snapshot: the key is wrong, say so.

## 2. Expected, not defects

- the pad peak is higher than the rotor peak and occurs earlier;
- the peak occurs well before ts (a ramp source peaks near mid-stop at the
  surface; exact time depends on the partition);
- the rotor field is smeared around the circumference (rotation working);
- the bulk rise is about 40 K while the surface rises hundreds of K (the energy is
  in the skin);
- the hat and mounting face stay near 300 K: conduction time x^2 / alpha to the
  mounting face is minutes, the stop is 3.54 s.

## 3. Defects that invalidate the result

A fixed hot spot under the pad (rotation not applied or wrong axis); a peak at
exactly t = ts (constant source); everything at 300 K (heat source on a wall that
touches nothing, or the mesh came from STEP); temperatures rising without bound (a
convection group resolved to zero area); energy ratio far below 90 % (a
non-axisymmetric zone was rotated). Any of these routes back to the
fluent-engineer as a Gate 3 failure; do not review temperatures from such a run.

## 4. A single stop is a thermal-mass problem

Convection removes about 1 % of the energy over one stop (the predecessor measured
0.65 % to 1.1 %; quote this run's `E_conv / E_applied`). Vanes, ducts, the vent
coefficient and cross-drilling therefore cannot move a single-stop verdict. Pad
area, heat partition and friction-face resolution can. A review that says "add
vanes" off a single-stop result misreads its own data; that advice belongs to the
repeated-stop case (DV-10, deferred).

## 5. Why one verdict source

The report consumes `review.json` and adjudicates nothing again. Two derivations
of one verdict with nothing enforcing agreement is how the predecessor shipped a
table that said "closed" beside a paragraph that said "not verified".

## 6. Why the drawing row says DESCOPED

The user descoped 2D drawings in PRD H1.2 (section 8, item 5). The drawing is
not a section 7 requirement, so it does not enter the 37-row roster and has no
disposition from the closed set. It is listed in `deliverables` with status
`DESCOPED`, so a reader sees it was dropped on purpose, not forgotten. GEO-06
evidence comes from `cad_report.json` plus the SpaceClaim section
`20_spaceclaim\cad_section_9deg.png` and the hat/cheek_in contact.

## 7. Why a timing table

Run 1 took about 2.5 h to reach Gate 2 against a 25 to 35 min target, and the
time went on lead polling and a repair loop, not on the applications. The timing
table makes that visible in every run: stage, owner, minutes, tool calls,
application launches and repairs, copied from `BUILD_STATE.timing`.
