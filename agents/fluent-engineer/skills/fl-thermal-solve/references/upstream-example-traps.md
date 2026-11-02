# The upstream PyFluent brake example is a trap list, not a template

Open this before copying anything from the published PyFluent "Automotive Brake
Thermal Analysis" example. It downloads a prebuilt mesh and starts at the
solver. It is useful as vocabulary. It is not a fidelity reference, and its
numbers describe a different, lighter car.

## Measured defects in the example

| Upstream does | Why it is wrong for this case |
|---|---|
| `omega = -15.79` passed to `solid_omega` | Its own comment says 15.79 rev/s (100 km/h on 0.28 m). `solid_omega` takes rad/s. The example spins 2 pi times too slowly, about 15.9 km/h |
| `q_dot = 2.0e9` constant | Inverted, it is 93.8 kJ per rotor over 2.0 s, about a 973 kg car. Here q''' is derived from PRD section 5 and ramps |
| one `htc = 100` on globbed `wall-disc*` and `wall-geom*` | No distinct vent coefficient. THM-05 needs one |
| no per-zone materials | every zone stays aluminum |
| monitors on volume maxima only | not the surface or wall-layer temperature the requirements ask about |
| axis direction (0, 1, 0), origin (-0.035, -0.821, 0.045) | properties of the example's mesh; here the axis is +Z through the origin |
| 2.0 s of simulated time | the stop here is 3.540681 s |
| q, omega and h constant | here all three ramp |
| contours on `"wall*"` | in this mesh that glob misses the friction pairs, the cheek/vane interfaces and the pad-stack leftovers; the render shows a hole where the pad sits |
| friction walls named `wall-pad-disc2` and `wall_pad-disc1` | hyphen in one, underscore in the other; an artefact of their mesh. These names do not exist here |

The one idea worth keeping: it rotates two plain annular plates and keeps its
vane bodies as separate stationary zones. That is what PRD section 2 does too.

## How this case differs, point by point

1. The mesh comes from `fl-meshing`, never from `examples.download_file`.
2. 27 cell zones: 2 cheeks, hat, 20 vanes, 2 pads, 2 backing plates.
3. q''', omega and t_stop come from `case.json`, which the lead derived from
   the vehicle (PRD section 5). Recompute and compare before using them.
4. q''', omega and h are functions of time.
5. Rotation is about +Z through the origin, negative sign, on the two cheeks.
6. Three convection groups with distinct h.
7. Materials assigned per zone and read back 27 of 27.
8. Monitors and reported values include both cell maxima and wall-layer maxima,
   over time.
9. The full stop, including the final short step.
10. A stored-energy audit and the tangential-velocity check are gates.
11. All parameters come from `case.json`; results go to `results.json`.

If a line you want to copy from the example carries a number, derive the number
again from the PRD instead.
