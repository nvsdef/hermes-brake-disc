# Fluent Graphics — Contours, Vectors, Streamlines, PNG Export

**Source:** PyFluent examples + hands-on.

**Scope:** creating contour, vector, and streamline visualizations; saving PNGs for reports/videos; headless rendering caveats.

---

## Access

```python
graphics = solver.settings.results.graphics
```

Contains named-object dicts for each visualization type:
- `graphics.contour["name"]` — scalar field colored on a surface
- `graphics.vector["name"]` — velocity vectors on a surface
- `graphics.streamline["name"]` — 3D flow lines
- `graphics.pathline["name"]` — transient particle paths
- `graphics.mesh["name"]` — mesh display
- `graphics.picture` — PNG export config
- `graphics.views` — camera control

## Contour plot

```python
graphics.contour["vel_contour"] = {}
c = graphics.contour["vel_contour"]
c.field = "velocity-magnitude"
c.surfaces_list = ["symmetry"]  # can be multiple
c.display()  # render
```

**Common `field` values:**
- `"velocity-magnitude"`, `"x-velocity"`, `"y-velocity"`, `"z-velocity"`
- `"pressure"`, `"dynamic-pressure"`, `"total-pressure"`, `"absolute-pressure"`
- `"temperature"`, `"total-temperature"`
- `"turb-kinetic-energy"`, `"turb-diss-rate"`
- `"cell-volume"`, `"wall-shear"` (near-wall only)

Full list depends on physics enabled. Query at runtime:
```python
c.field.allowed_values()
```

**Common `surfaces_list` values:** any named boundary from your case (`"inlet"`, `"outlet"`, `"symmetry"`, `"cylinder"`, `"walls"`), plus any custom surfaces you create.

## Vector plot

```python
graphics.vector["vel_vector"] = {}
v = graphics.vector["vel_vector"]
v.field = "velocity-magnitude"     # coloring field
v.surfaces_list = ["symmetry"]
v.options.scale = 4                # vector length scaling
v.style = "arrow"                  # "arrow" or "3d-arrow" or "line"
v.display()
```

## Streamline / pathline

```python
graphics.streamline["sl"] = {}
sl = graphics.streamline["sl"]
sl.field = "velocity-magnitude"
sl.surfaces_list = ["inlet"]  # source surface
sl.options.step_size = 0.001
sl.display()
```

Pathlines (transient) — similar but for time-integrated particles.

## Custom surfaces (planes, isosurfaces)

Sometimes you want a plane through the domain that isn't a boundary. Create it first:

```python
# Iso-surface at Y=0 midplane
solver.settings.results.surfaces.iso_surface["midplane"] = {}
mp = solver.settings.results.surfaces.iso_surface["midplane"]
mp.field = "y-coordinate"
mp.iso_value = 0.0
mp.surfaces_list = ["symmetry", "walls", "cylinder"]  # scope
```

Then use `"midplane"` as a surface in contours/vectors.

## View control

Camera view for the render:

```python
graphics.views.restore_view(view_name="front")   # front, back, top, bottom, left, right, iso
graphics.views.auto_scale()                        # zoom to fit
```

Save a custom view:
```python
graphics.views.save_view(view_name="my_view")
graphics.views.restore_view(view_name="my_view")
```

## PNG picture export

```python
# Set resolution
graphics.picture.x_resolution = 1600
graphics.picture.y_resolution = 900

# For containerized/headless: disable window-based resolution
if graphics.picture.use_window_resolution.is_active():
    graphics.picture.use_window_resolution = False

# Save
graphics.picture.save_picture(file_name="results/velocity.png")
```

**Common resolutions:**
- `1920 x 1080` — Full HD (video)
- `1600 x 900` — smaller, faster
- `3840 x 2160` — 4K (print quality)

**Format:** determined by file extension. PNG (default), JPEG, TIFF, EPS all supported.

## Full workflow: contour PNG in one shot

```python
# Setup
g = solver.settings.results.graphics
if g.picture.use_window_resolution.is_active():
    g.picture.use_window_resolution = False
g.picture.x_resolution = 1600
g.picture.y_resolution = 900

# Create contour
g.contour["vel"] = {}
g.contour["vel"].field = "velocity-magnitude"
g.contour["vel"].surfaces_list = ["symmetry"]
g.contour["vel"].display()

# Adjust view
g.views.restore_view(view_name="front")
g.views.auto_scale()

# Save
g.picture.save_picture(file_name="velocity.png")
```

## Headless / no-gui rendering

When running with `ui_mode="no_gui"`, Fluent still renders in memory to file. Confirmed working — see `../examples/post_processing.py`.

If offscreen rendering fails (rare), try:
```python
solver = pyfluent.launch_fluent(ui_mode="hidden_gui")   # offscreen window
```

## Coloring / colormap

```python
c.color_map.field = "velocity-magnitude"
c.color_map.color = "rainbow"  # or "field-velocity", "reverse-rainbow", "custom"
c.color_map.log_scale = False
c.color_map.log_scale_min = 0.01
c.color_map.range_option.option = "auto-range-on"    # or "auto-range-off"
# c.color_map.range_option.min_value = 0
# c.color_map.range_option.max_value = 1
```

## Line integral convolution (LIC)

Advanced visualization showing detailed flow structure:
```python
graphics.LIC["lic1"] = {}
# See docs for full options
```

## Saving to alternative formats

```python
# EPS for print
g.picture.save_picture(file_name="fig.eps")

# TIFF for high-quality
g.picture.save_picture(file_name="fig.tiff")
```

## Common gotchas

- **No output file** — verify `use_window_resolution = False` for headless
- **Blurry image** — bump resolution to 1920x1080 or higher
- **Blank contour** — surface has no cells (wrong surface name?), or field is all zero
- **View is inside geometry** — call `auto_scale()` after `restore_view()`

## For paper reproduction

Papers commonly show:
- Velocity magnitude contour on symmetry plane
- Streamlines showing recirculation
- Pressure coefficient on wall
- Vorticity contour for shedding cases

Match:
- Field variable (velocity vs. pressure vs. vorticity)
- Colormap (matching color range makes visual comparison possible)
- Camera view (usually front/side)
- Same surface for the contour
