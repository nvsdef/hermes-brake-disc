# Monitors, report files and contours

Open this when defining monitors, reading the `.out` report file, or rendering
temperature contours.

## Monitors go into one per-step report file

A report file is written by Fluent itself at every time step. It costs no
PyFluent round trips, and it is the only way to get a true per-step history of
the maxima. Put the 12 monitors from step 1 of the skill, plus flow time, into
one report file.

API idiom:
```python
rv = solver.settings.solution.report_definitions.volume
rv["t-cell-max-pad-fric"] = {}
rv["t-cell-max-pad-fric"].report_type = "volume-max"
rv["t-cell-max-pad-fric"] = {"field": "temperature", "cell_zones": pad_zones}
rs = solver.settings.solution.report_definitions.surface
rs["t-wall-max-pad-fric"] = {}
rs["t-wall-max-pad-fric"].report_type = "surface-facetmax"
rs["t-wall-max-pad-fric"] = {"field": "temperature", "surface_names": pad_side_walls}
rf = solver.settings.solution.monitor.report_files
rf.create(name="brake-monitors")
rf["brake-monitors"] = {"report_defs": names + ["flow-time"],
                       "file_name": "brake-monitors.out"}
```

Check the report file is set to write every time step (not every iteration),
and read its state back.

## Reading the .out file

**Fluent never overwrites a monitor file.** A second run writes
`brake-monitors_1_1.out` and leaves the old one. Reading the fixed name reports
the first run's numbers forever; the predecessor saw three consecutive fixes
"produce" the same 2527 K from a run made an hour earlier. Delete stale files
before the run, and after the run take the file whose mtime is inside this job's
start and end times.

The header has several lines, and only the last one lists every column:

```
"brake-monitors"
"Time Step" "t-cell-max-rotor-fric t-cell..."                     <- truncated
("Time Step" "t-cell-max-rotor-fric" "t-cell-max-pad-fric" ... "flow-time")
```

Two traps, both of which swap columns silently:

- A naive scan latches onto the truncated line and falls back to guessing
  positions.
- Splitting the header on whitespace turns `"Time Step"` into two tokens while
  the data rows have one column for it, so every index is off by one.

Extract the **quoted** names with `re.findall(r'"([^"]*)"', line)`, use the last
header line that resolves every monitor, and **map columns by name**. Store the
mapping in `results.json.column_mapping`. If any column was mapped by position,
say so; the numbers cannot then be trusted as to which curve is which.

## Contours

### Surfaces: every wall, shadows included

The upstream example uses `surfaces_list: "wall*"`. In this mesh that glob
misses the friction pairs, the 40 cheek/vane interfaces and the auto-named
pad-stack walls; the picture shows a hole where the pad sits. Excluding
`-shadow` zones removes one whole side of each coupled pair and makes the same
hole from the other direction. Enumerate every wall:

```python
walls = list(solver.settings.setup.boundary_conditions.wall.get_object_names())
```

Then choose subsets per view from that list.

### Range: manual, banded, labelled

- Set the range **manually**, from the values you have already measured. Auto
  range stretches to any clipped cell and turns the model blue.
- Use a banded (non-smooth) palette. With a smooth palette the circumferential
  distribution on the rotor flattens to one colour.
- One palette cannot show both the friction faces and the vent faces well. Use a
  separate band per view and print the band on the figure.
- Every figure states: field and unit (temperature, K), flow time in s, band
  minimum and maximum in K, and the caption for its instant.

API idiom:
```python
c = solver.settings.results.graphics.contour
c["t-rotor-face"] = {"field": "temperature", "surfaces_list": rotor_face_walls,
                     "filled": True, "node_values": True, "boundary_values": True,
                     "coloring": {"smooth": False}}
c["t-rotor-face"].range_option.option = "auto-range-off"
c["t-rotor-face"].range_option.auto_range_off = {"minimum": tmin, "maximum": tmax}
c["t-rotor-face"].display()
```
The range path varies by version; read `get_state()` and set what you find.

### The instant is part of the evidence

Only the instants for which data exists can be contoured after the run. By
default that is the end-of-stop field. Its caption must say
**"end-of-stop field, t = 3.540681 s, NOT the peak"**. A predecessor contour band
of 370.0 to 390.5 K was published beside a 642.3 K peak with nothing but a
hand-written note between them.

To show the field near the peaks, write data during the run at a few planned
instants, for example t = 0.1 s (wall-layer peaks), about 1.8 s (expected
cell-max peak on the pad) and ts, or render and save contours in-loop at those
windows. Record for each contour entry: `field_instant_s`, `contour_band_k`,
`caption`, `headline_peak_k` and `headline_peak_time_s` of the related monitor,
and `band_top_below_headline_peak_k`.

### Views to produce

| File | Surfaces | Camera |
|---|---|---|
| `contour_rotor_face_end.png` | rotor-side friction walls, `wall-outer*` on `cheek_out` | looking along -Z at the outboard face |
| `contour_pad_face_end.png` | pad-side friction walls and pad/backing leftovers | looking at the pad friction face |
| `contour_vent_end.png` | `wall-vent*` zones | vent close-up, target (0, 0, 0) |
| `contour_<view>_t<time>.png` | same, at a planned peak instant | same |

Framing traps from the meshing stage apply here: restore a named view, set
camera target and field, do not set camera position, do not call
`views.camera.orbit`.

### Saving pictures

`save_picture` does not overwrite an existing PNG and raises nothing. Delete the
target first. It ignores `x_resolution` and `y_resolution`; the PNG takes the
graphics window size. Record each file's size and mtime. Render in the session
that solved: the predecessor once rendered contours in a separate Fluent and
spent 13 min 37 s; in the solving session they took about 4 s each.

## Ring evidence that rotation works

Optional but cheap: create iso-surface rings (constant radius) on the rotor
outboard face at r = 128, 140 and 155 mm, and report coldest-facet rise /
hottest-facet rise on each at the end of the stop. A ratio near zero means a
stationary hot spot under the pad, which means the solid motion did not take.
