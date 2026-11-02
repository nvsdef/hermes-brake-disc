---
name: brake-report
description: "Gate 4: compose report.pdf, verdict first, with manifest."
version: 1.2.0
author: "sdefibaugh"
license: Apache-2.0
platforms: [windows]
metadata:
  hermes:
    tags: [brake, lead, report, pdf]
---

# brake-report - the design-verification package (PRD H1.2)

The last step of Gate 4. It turns the run folder into one PDF an engineer can put
in a design review: `C:\brake-runs\<run-id>\50_report\report.pdf`, plus
`manifest.json`. **The report assembles; it does not compute or adjudicate.**
Every disposition comes from `review.json`; every number comes from a named key
in an artifact; every figure already exists on disk. There is no 2D drawing in
H1.2: the report says so in one line.

| Reference | Open it when |
|---|---|
| `references/report-structure.md` | before you start: section order, figures, captions, page 1 |
| `references/figure-verification.md` | after collecting figures and after building the PDF |

## 1. Checklist

**Tools**
- [ ] Find a Python that has the libraries, in one terminal call. Never bare
      `python` or `python3` (it opens a Windows Store installer):

      ```
      C:/solidpilot/.venv/Scripts/python.exe -c "import reportlab, pypdf, fitz, PIL; print('ok')"
      ```

      Or use `execute_code`. Preferred: reportlab for layout, pypdf for merging,
      PyMuPDF (`fitz`) for rasterising. If only matplotlib is available, its
      `PdfPages` backend will do. Do not install packages without the user's
      approval; if nothing works, write `report.md` with linked figures and set
      `complete_with_findings`.
- [ ] One composition script only: `50_report\compose_report.py`. It lays out
      text, tables and existing images. It contains no disposition logic, and it
      never builds geometry, tags, meshes, solves or recomputes a temperature.

**Collect** (copy, never move, into `50_report\assets\`)
- [ ] SpaceClaim CAD visuals: `20_spaceclaim\cad_iso.png`,
      `cad_section_9deg.png`, `named_selections.png`.
- [ ] Mesh images from `30_fluent\` (full view and vent close-up).
- [ ] Temperature contours from `30_fluent\` (rotor and pad friction faces, at
      peak and end of stop) and the history CSVs for the peak plot.
- [ ] `review.json`, `case.json`, `cad_report.json`, `tag_report.json`,
      `mesh_report.json`, `setup_report.json`, `results.json`.
- [ ] Record each source path and SHA-256 in `manifest.json`. Recompute the 11
      frozen CAD hashes and the PMDB inner-file hash one last time.

**Verify figures** (`references/figure-verification.md`)
- [ ] Each exists, is larger than 20 kB, is not blank, and passes its vision
      question. A failure becomes a named placeholder and a finding.

**Compose** (order in `references/report-structure.md`)
- [ ] Page 1: run id, PRD H1.2, workflow status, verdict sentence, governing
      requirement, energy audit line, first change, then the requirement table,
      all verbatim from `review.json`.
- [ ] Geometry section: parts table, `cad_iso.png`, `cad_section_9deg.png`
      (GEO-06), rotation note "rotates clockwise viewed from +Z (outboard)".
- [ ] Geometry preparation: areas, contacts, `named_selections.png`.
- [ ] Mesh: numbers and both mesh images. Results: peak table, peak-history
      plot, contours. Energy audit.
- [ ] Deliverables line: "2D drawing: DESCOPED (PRD H1.2 section 8, item 5)".
- [ ] Per-stage timing table from `review.json` -> `timing`.
- [ ] Limitations, recommendations, findings, manifest.

**Render, inspect, close**
- [ ] Rasterise every page at about 110 dpi; look at each with the vision tool.
- [ ] Text-extract and compare the 37 dispositions with `review.json`.
- [ ] Write `manifest.json` (every run artifact: stage, path, SHA-256, size,
      producing role; plus the report and page images).
- [ ] Update `BUILD_STATE.json`: `completed_gates` + `"G4"`, `timing.G4`,
      `timing.total_minutes`, final status. Tell the user the status word, the
      governing requirement and its disposition, and the report path.

## 2. Rules that make it a report, not a slideshow

- **Verdict first.** Method comes later.
- **Dispositions verbatim.** The five words from `review.json`, unchanged. Never
  "OK", never "N/A", never a softened synonym.
- **Ranges stay ranges.** A THM row prints `[lower, upper] K`, both keys named.
- **Every figure is of the solved model.** A figure showing geometry that is not
  in `brake.step` (cross-drilled holes, a "design model") is a Gate 4 failure, not
  a caption to fix.
- **Captions say what to notice** and describe the image actually in the file.
  An end-of-stop contour says so: it is not the peak.
- **Limitations come before recommendations.**
- **Degrade on pictures, never on numbers.** A missing figure becomes a visible
  boxed placeholder naming the file and the stage that owed it, and the status
  becomes `complete_with_findings`. A missing headline number stops the report:
  go back to `brake-design-review`. The descoped drawing is not a missing
  figure and gets no placeholder.
- **One canonical output.** Rebuilding overwrites `report.pdf`; keep a `builds`
  list in `manifest.json` rather than `report_v2.pdf` siblings.
- **Nothing in OneDrive.** The report and its assets live in the run folder.

## Verification

- `report.pdf` opens, every page rasterises, and you looked at every page image.
- Page 1 carries the workflow status, the engineering verdict, the governing
  requirement and the requirement table (continued on page 2 if needed).
- Every disposition in the PDF matches `review.json` (text-extract and compare).
- The three SpaceClaim CAD visuals, both mesh images and the contours are present
  or have named placeholders listed as findings.
- The report states the 2D drawing is descoped and contains the per-stage timing
  table.
- `manifest.json` hashes recomputed now match the files; the 11 frozen CAD
  hashes still equal Gate 1 and the PMDB inner-file hash still equals Gate 2.
