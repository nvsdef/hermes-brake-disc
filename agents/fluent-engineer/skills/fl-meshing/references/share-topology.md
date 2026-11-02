# Shared topology - the task, what it creates, and how it fails

Open this before step 5 of the meshing procedure, when surface meshing fails, or
when coupled pairs come back short.

## Why it matters

27 bodies touch at **45 interfaces** (PRD section 4 contacts table). The rotor
alone owns 41 of them, because it is four kinds of body, not one:

```
bp_outer | outerpad | CHEEK_OUT | 20 VANES | CHEEK_IN | innerpad | bp_inner
                                               |
                                              HAT  (cylinder r = 95, z = -16 to -6)
```

Each interface must become **one shared face with matched nodes on both
sides**, which the solver sees as a coupled wall and its `-shadow` twin. If it
does not, Fluent creates two coincident, uncoupled walls, and conduction across
the interface is zero. There is no error message. The typical symptom is one
body heating and its neighbour staying at 300 K.

**If the cheeks are not coupled to the vanes and the hat, the heat cannot leave
the friction plates and the answer is worthless.** Forty of the 45 pairs are
cheek/vane pairs, and their absence is silent.

## It is a task, and the workflow will not add it for you

Describe Geometry needs `InvokeShareTopology = "Yes"`. That makes an
`Apply Share Topology` task appear. **You must execute it.** Without it, the
predecessor measured this in the transcript:

```
---------------- After surface meshing, 27 objects/parts have been detected.
                 Either the Share Topology task should be added, or the
                 Non-Conformal option should be invoked.
Error: An error occured during task update
```

PyFluent surfaces only `RuntimeError: Exception encountered in S_ExecuteTask:
An error occured during task update`, and the process sometimes printed
`SIGSEGV at Node 0` on the way down, so it looked like a Fluent crash. **Read the
stdout transcript, not the traceback.** Everything useful Fluent Meshing has to
say goes to stdout.

## Two routes, in order of preference

1. **Conformal shared topology** (this workflow). It works when the CAD faces
   are exactly coincident, which they are by construction: every part is built at
   its true global position and assembled with identity transforms (PRD section
   2), so contacts abut with zero overlap.
2. **Non-conformal interfaces** with coupled thermal conditions. Use only if the
   lead approves after route 1 fails for a reason that is not a CAD defect. It
   adds interpolation error and one more thing to verify, and the pair and area
   checks still apply.

If shared topology fails, the cause is almost always a small gap, overlap or
sliver in the assembly. That is an upstream defect. Report it; do not paper over
it in the mesher.

## Micron slivers kill the surface mesher

A predecessor vane whose end arcs were fitted to r = 164.998 mm against a cheek
at exactly 165.000 mm left a 2 micron sliver face. Surface meshing then reported
`CONFORMAL_TESSELLATION_FAILED`, `node insertion failed at (108.661 124.16 -6)`
and `SIGSEGV at Node 0`. Those coordinates are r = sqrt(108.661^2 + 124.16^2) =
165.00 mm, z = -6 mm: they point straight at a vane/cheek junction on the
inboard side. **Read the coordinates, convert to r, theta, z, and name the body
pair.** Return it to the lead as a CAD defect with those numbers. The fix is in
the CAD (trim the vanes with exact r = 95 and r = 165 cylinders, PRD section
3.2), not in the mesher.

## What shared topology must and must not create here

| Contact | Expected result |
|---|---|
| outerpad / cheek_out at z = +16 | coupled pair, 5 864.31 mm^2 (the pad footprint, not the whole cheek face) |
| innerpad / cheek_in at z = -16 | coupled pair, 5 864.31 mm^2 |
| outerpad / bp_outer at z = +28 | coupled pair, 5 864.31 mm^2 (the pad face; the backing plate is larger) |
| innerpad / bp_inner at z = -28 | coupled pair, 5 864.31 mm^2 |
| each vane / cheek_out at z = +6 | coupled pair, 604.30 mm^2, 20 of them |
| each vane / cheek_in at z = -6 | coupled pair, 604.30 mm^2, 20 of them |
| hat / cheek_in, cylinder r = 95, z = -16 to -6 | coupled pair, 5 969.03 mm^2 |
| hat / vanes at r = 95, z = -6 | **edge only, no face pair**; a pair here means the hat geometry is wrong |
| pad stack / calliper | nothing; the calliper is not in the PMDB |

A friction patch with an area near 57 177 mm^2 (a whole cheek face, pi x
(165^2 - 95^2)) means the pad outline was not imprinted into the cheek. That is
a FAIL; the pad would be coupled over the whole cheek.

## Not confirmable upstream

Shared topology **cannot be confirmed at the tagging stage**. Imprinting reads
`false` in the PMDB because Fluent creates it during meshing. The confirmation is
here, by three independent witnesses:

1. The coupled-pair count and classes (45: 2 / 2 / 40 / 1).
2. The meshed `wall-vent` area falling from about 167 037.6 mm^2 (pre-imprint)
   to 142 865.51 mm^2 (post-imprint).
3. The leftover exposed pad-stack walls: if the pad faces were never carved into
   interfaces, their exposed area is larger by about 2 x 5 864.31 mm^2 or
   4 x 5 864.31 mm^2.

All three must agree. If one disagrees with the other two, report all three
numbers.
