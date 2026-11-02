# When a thermal row is NOT ADJUDICABLE - what closing it costs

Open this when THM-01, THM-02 or THM-04 is NOT ADJUDICABLE because of resolution
or a straddling range, and someone asks whether the number "should be quoted
anyway", or what it would take to decide it.

## 1. Say it plainly

A quantity that the model under-reports by an amount it cannot size, sitting near
its limit, is not verified. Write: "THM-02 is not adjudicable on this mesh: the
pad-side wall-normal cell is <c> mm against a 1.374 mm penetration depth, and the
range [<a>, <b>] K contains the 623 K limit." Do not average the discomfort away,
do not quote the lower end as the answer, and do not quote a margin.

## 2. The direction of the error is known

Every unresolved effect in this model moves the pad **towards** the limit: a cell
reports its average, and the average of a steep near-surface gradient sits below
the surface value; the uniform 300 K start is the most favourable start possible;
perfect contact conductance lets heat leave the pad face as fast as the iron will
take it. None of these moves the pad away from the limit. That asymmetry is
reportable on its own, and needs no hand calculation. It **cannot** be supported
by a disc/pad split closed form (see the brake-duty-cycle skill's traps
reference): one assumed coefficient swings that answer across 600 K.

## 3. The resolution targets, derived

```
(values at ts; PRD section 7 compares at the time of the peak, which is earlier
and gives a smaller depth, so recompute with this run's t_peak)
penetration depth (pad) = sqrt(5.3333e-7 x 3.540681) = 1.374 mm
PRD minimum (1 cell)    : wall-normal cell <= 1.374 mm
5-cell target           : 1.374 / 5 = 0.275 mm
penetration depth (iron) = sqrt(1.6157e-5 x 3.540681) = 7.564 mm
PRD minimum (1 cell)    : wall-normal cell <= 7.564 mm
5-cell target           : 7.564 / 5 = 1.513 mm
```

The predecessor once wrote "about 0.14 mm" for the pad target while stating a
5-cell criterion on the same line; 1.374 / 0.14 is 9.8 cells. Derive the target
from the criterion each time and print the division.

## 4. What it costs

1. **Local refinement on the two pad contact faces.** Set a wall-normal size of
   0.275 mm (or at least below 1.374 mm) on the pad side of the pad/cheek contacts
   and let it grow into the pad (pad thickness 12 mm). One mesh and one solve,
   commissioned to the fluent-engineer as a Gate 3 repair (one commission: mesh,
   internal mesh gate, setup, solve, post).
2. **Check the Student cap first.** cells + nodes must stay below 512 000. The
   predecessor's full-assembly mesh already used 93 % of the cap with a 1.9 mm pad
   cell. If local refinement does not fit, the two routes are a licence beyond
   Student, or a **60 deg pad-and-cheek sector submodel** (one pad, the cheek
   sector under it, the backing plate), which buys roughly two orders of
   magnitude of local resolution inside the same cap. The submodel is a new
   analysis definition and needs the PRD owner's agreement; record it as a
   next step, not something you commission silently.
3. **Layer-thickness sweep** (lever B in `recommendation-levers.md`) to show
   whether the upper end of the range is the layer's own resistance. If the upper
   end scales with d, the true interface value is closer to the cell value than
   the layer value, but only resolution can say by how much.

## 5. What does not close it

- More iterations per time step. The gap between the cell maximum and the layer
  maximum tracks the applied flux (the predecessor fitted it against q(t) with
  R^2 = 0.999), not the iteration count.
- Phasing the source in over the first steps. A linear ramp already peaks at
  t = 0; phasing only moves the same peak later.
- A hand calculation with an assumed heat partition.
- Quoting the cell maximum as "near-surface". It is the lower end of the range,
  and a lower end cannot show a requirement is met.
