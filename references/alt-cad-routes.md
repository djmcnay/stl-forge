# Alternative CAD routes and when they automate

Verified comparison for "design a part from code and export STL", distilled
from Autodesk's own documentation and forum answers. Reach for this when the
principal asks why not Fusion/TinkerCAD, or weighs a heavier CAD package.

| Route | Automates headless? | Practical verdict |
|---|---|---|
| OpenSCAD CLI (this skill) | Yes - one binary, `openscad -o out.stl -D key=value t.scad` | Default for parameterised simple parts |
| CadQuery (Python) | Yes - `pip install cadquery`, exporters produce STL/STEP | Use when a part needs true fillets/chamfers, OCP gives B-rep; heavy install (hundreds of MB) |
| Fusion 360 desktop API | No - scripts/add-ins (Python) execute only inside a running Fusion session, on the UI thread | Excellent interactive CAD; batch parametric export is not supported locally |
| Fusion via bridge add-in (e.g. FusionHeadless) | Partial - Fusion app must be running; an HTTP add-in relays CLI commands; drives parameters and exports renders/STEP | Works, but adds a live-app dependency and per-session setup; Windows-first lineage |
| Fusion Automation API (Autodesk, APS Design Automation v3) | Yes, but cloud-only: TypeScript scripts, cloud workers, paid/APS registration | The only first-party headless Fusion route; overkill for hobbybed parts |
| TinkerCAD | No - browser-only, no downloadable package, no scripting API | Manual geometry in a browser; no parameterisation story |

## Manifold self-check without trimesh

Before trusting a render, export ASCII and read OpenSCAD's report:

```bash
openscad --export-format asciistl -o /dev/null check.scad 2>&1 | grep -A1 'Top level'
```

Passing shape: `Top level object is a 3D object (manifold):` then
`Status: NoError`. Apply it at PARAMETER EXTREMES (smallest wall, largest
corner radius, divider counts 1) - a preset set can be manifold at defaults
and float geometry at an edge. Walking the parameter space this way costs
seconds because this class of geometry renders in milliseconds.
