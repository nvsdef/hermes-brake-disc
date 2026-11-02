# Figure verification - prove every figure renders and shows what it claims

A report generator places whatever PNG is in the folder under whatever caption it
was given. It cannot tell an empty viewport from a model, or a picture of the
wrong model from the right one. The predecessor shipped a SpaceClaim screenshot of
an empty, unframed viewport, and captions describing cooling holes on renders of a
model that had none. Checking is your job.

## 1. Before layout: each image file

For every figure in `50_report\assets\`:

| Check | Pass when | How |
|---|---|---|
| exists | file present at the path you will cite | file tool |
| size | > 20 kB for a PNG screenshot or render (a blank or failed capture is usually a few kB) | `Get-Item <path> | Select Length` |
| dimensions | at least 800 x 600 px | PIL `Image.open(p).size` |
| not blank | grey-level standard deviation > 8 on a 0 to 255 scale, and fewer than 97 % of pixels equal to the most common colour | API idiom below |
| content | the vision tool confirms the claimed content | `vision_analyze` with a specific question |

API idiom (blank check, inside the composition script or `execute_code`; never
bare `python` in the terminal, use `C:/solidpilot/.venv/Scripts/python.exe`):

```python
from PIL import Image, ImageStat
im = Image.open(path).convert("L")
std = ImageStat.Stat(im).stddev[0]
top = max(im.getcolors(im.size[0] * im.size[1]))[0] / (im.size[0] * im.size[1])
ok = std > 8 and top < 0.97
```

Ask the vision tool specific, falsifiable questions, not "does this look good":

- `cad_iso.png`: "How many separate parts can you distinguish? Is there a
  C-shaped calliper around a disc? Is the model centred and filling most of the
  frame?"
- `cad_section_9deg.png`: "Is there a gap between the hat wall and the vanes at
  the inboard side? Is the hat attached to the lower (inboard) cheek?"
- named selections: "Are two different colours applied to the rotor faces? Is the
  model visible and framed, or is the viewport empty?"
- mesh close-up: "Are mesh cells visible between the vanes?"
- contour: "Is there a colour legend with units in K? Is a time value shown? Is
  the hot band a full ring or a single spot?"

Record each answer in `manifest.json` under the figure (`vision_check`). A figure
that fails is replaced by a placeholder and becomes a finding; it is never
captioned as if it were correct.

## 2. After building: the PDF

1. Open the PDF with pypdf and count pages; a zero-page or unreadable PDF is a
   failure.
2. Rasterise every page (API idiom, PyMuPDF):

   ```python
   import fitz
   doc = fitz.open(pdf_path)
   for i, page in enumerate(doc):
       page.get_pixmap(dpi=110).save(f"{out_dir}\\page_{i+1:02d}.png")
   ```

3. Look at every page image with the vision tool: legible text, figures present,
   tables not cut at the right margin, no overlapping text, placeholders visible
   and named.
4. Text-extract the PDF (`page.get_text()`) and check that each of the 37 row IDs
   appears once in the requirement and DV tables with the same disposition as
   `review.json`.
5. Keep the page images in `50_report\pages\` and list them in the manifest:
   they are the evidence that the report rendered.

## 3. Hash the result

After the final build, hash `report.pdf` and every file in `assets\`, and write
them to `manifest.json`. If you rebuild, re-hash and append to `builds[]` with
the time and the reason.
