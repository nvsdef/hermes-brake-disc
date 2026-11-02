# SolidPilot tools used by the CAD stage (PRD H1.2)

The live server exposes 46 tools (`mcp/solidpilot-tools.json`, re-checked live 2026-11-02). The Gate 1
procedures use 17 of them. A smaller tool list means fewer tokens every turn
and fewer wrong turns, so the Hermes profile for `solidworks-engineer` should
filter SolidPilot to this list.

## Include (17)

| Tool | Used for |
|---|---|
| `ensure_ready` | session start, once |
| `verify_state` | pre-existing documents; inspection after a timeout |
| `open_new_part` | each of the 9 parts |
| `add_reference_geometry` | offset planes (`type='plane'`) |
| `create_sketch` | every sketch; returns the frame |
| `add_sketch_entities` | every profile, from a data card (`segments` is a JSON string) |
| `extrude_feature` | boss, cut, revolve; returns `result_geometry.volume` |
| `analyze_model` | `mass_properties` once per part, `bodies` for the vanes and the STEP re-import, `faces` at the re-import, `features` or `sketch` after a timeout or a miss |
| `edit_feature` | `action='delete'` for a HALT repair |
| `save_document` | each part and `brake.SLDASM` |
| `open_new_assembly` | `brake.SLDASM` |
| `insert_component` | 9 parts, identity `transform_json`, `fixed=true` |
| `analyze_assembly` | `components` (count 9 and names); `faces` for the placement spot check |
| `export_document` | `brake.step` |
| `open_document` | STEP re-import (it flattens to one multibody part) |
| `activate_document` | re-activate `brake` if another document took focus |
| `close_document` | close the re-imported STEP with `save=false` |

Hermes profile idiom (the key name depends on the Hermes version; the list is
the part that matters):

```yaml
mcp_servers:
  solidpilot:
    tools:
      include: [ensure_ready, verify_state, open_new_part, add_reference_geometry,
                create_sketch, add_sketch_entities, extrude_feature, analyze_model,
                edit_feature, save_document, open_new_assembly, insert_component,
                analyze_assembly, export_document, open_document, activate_document,
                close_document]
```

## Must stay excluded

| Tool | Why |
|---|---|
| `submit_feature_graph` | The schema calls it the "primary build path". It ignored every placement key, and all bodies landed on one plane extruding +Y. A `cheek_out` built this way had a perfect volume at the wrong position |
| `rebuild_from_ir` | Same compiler path as `submit_feature_graph` |
| `auto_dimension_drawing` | Stacked every dimension in one view. There is no tool to delete or move a dimension. Drawings are descoped in H1.2 anyway |

## Not needed in H1.2 (leave out of the include list)

- Drawing tools: `create_drawing`, `add_drawing_view`, `add_section_view`,
  `add_drawing_dimension`, `add_hole_callout`, `auto_center_marks`,
  `analyze_slddrw_test`, `analyze_drawing`, `add_flat_pattern_view`.
  Drawings are descoped. SpaceClaim takes the CAD screenshots at Gate 2.
- `create_pattern`: it reported 20 instances and made 1 body.
- `modify_dimension`: it dropped the sign of a negative plane offset
  (`requested -0.016, effective 0.006`).
- `save_body_as_part`: bodies keep their source coordinates, and it timed out.
- `add_mate`: nothing is mated. Identity transforms only.
- `set_part_material`: material is cosmetic. Mass = volume x PRD density.
- `add_sketch_entity`, `add_sketch_constraint`, `add_dimension`, `edit_sketch`:
  the data cards go in with `add_sketch_entities`, and constraints can roll a
  sketch back.
- `compare_parts`, `compare_assemblies`, `save_analysis`, `batch_export`,
  `sheet_metal_feature`, `create_rib`, `add_edge_feature`, `get_selection`:
  no use in this build. PRD 3.4 forbids fillets and chamfers.

If a procedure step ever needs a tool that is not on the include list, the list
is wrong. Tell the lead. Do not route around the list with
`scripts/mcp_client.py`.
