# What this model cannot tell you

State these in the limitations section, **conditional on this run's data**. A
caveat that is false on a clean run teaches the reader to skip the section, so
include each item only when it is true, and give its number where there is one.

| Blind spot | Include when | What to write |
|---|---|---|
| **Friction-face resolution** | always; name it first | wall-normal cell vs penetration depth for pad (1.374 mm) and iron (7.564 mm), cells across, and which rows it makes NOT ADJUDICABLE or resolution-limited. Every unresolved effect (cell averaging, uniform 300 K start) moves the pad **towards** the limit, none away |
| **Virtual heat-generation layer** | always | the 0.002 m layer is a modelling assumption, not a physical interface; the wall-layer maximum is the outer face of that layer and exceeds the true interface temperature while heat flows inward. The range [cell max, layer max] is diagnostic, not a certified bound |
| **Prescribed convection** | always | h is an input (130 / 85 / 40 W/(m^2 K) at omega_ref, scaled by omega^0.8, floor 7), not a solved airflow. There is no air domain. THM-05 proves the vent is modelled, not that its coefficient is right |
| **Vane hand and the vent coefficient** | always | the vent coefficient's basis presumes vanes pumping in the direction of rotation (clockwise from +Z here); the CTS intent "pumps under +theta" is not met by the geometry |
| **Solid-motion approximation** | always | only the two axisymmetric cheeks rotate; vanes and hat are stationary in the model. Circumferential smearing in the vanes is not represented. Quote the tangential-velocity check value if the child measured it |
| **Energy audit residual** | always | quote ratio and residual with sign; a closed audit is a fault screen (90 to 110 %), not proof of numerical accuracy; time-step and mesh sensitivity were (or were not) run |
| **Calliper and brake fluid** | always | the calliper is built and gated in CAD but deleted before meshing; THM-06 and DV-09 are deferred; soak-back after the stop is the governing case for fluid and is absent |
| **Single stop only** | always | production rotors are sized by repeated-stop and descent cases (DV-10) where convection matters; this case says nothing about them |
| **Uniform 300 K start** | always | real duty cycles start hot; a limit judged from ambient must be re-derived for a hot start |
| **No stress, wear, fade or judder** | always | conduction only: no thermal stress or coning (DV-08 cracking deferred), no wear or transfer film, no fade chemistry (DV-07 deferred), no DTV |
| **Contact resistance** | always | pad/cheek, pad/backing, vane/cheek and hat/cheek contacts are perfect conductors (shared topology); real contacts have resistance that raises the pad face temperature |
| **Constant source** | only if the run used one | a constant source is about 5.7 % low on the peak and puts it at t = ts; the ramp is the model |
| **Truncated solve** | only if final time < 3.540681 s | state the missing time and energy |
| **Clipped cells** | only if any value hit a solver limit | name the quantity excluded; do not claim locality from a warning coordinate |
| **Student cell cap** | only if the licence is Student | cells + nodes vs 512 000, and whether it limited the friction-face resolution |
| **No wheel geometry** | always | PKG-06 is OPEN |

Keep each item to two or three sentences with its number. This section comes
**before** the recommendations in the report.
