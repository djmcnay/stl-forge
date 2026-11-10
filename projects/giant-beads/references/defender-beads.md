# Defender bead pair — references and decisions

## Local reference files

- `references/defender/side.png` — authoritative side-view reference supplied by the principal (carsized, Defender 90 2007 side view).
- `references/defender/rear.png` — authoritative rear-view reference supplied by the principal (carsized, Defender 90 2007 rear view).
- `references/defender/side-trace-overlay.png` — corrected trace overlay: green body outline including the side step, orange door seams/handle/hinges, cyan windows, yellow road wheels and spare. Mirror, mudflaps and exhaust are deliberately omitted.

## References

- Principal-supplied profile drawing.
- Carsized side view: `https://www.carsized.com/resources/land-rover/defender/90/2007/sl_329105122_land-rover-defender-2007-side-view_4x.png`
- Carsized rear view: `https://www.carsized.com/resources/land-rover/defender/90/2007/ra_376000000_land-rover-defender-2007-rear-view_4x.png`
- Principal-supplied side photo: `https://monarchdefender.com/_next/image?url=https%3A%2F%2Fimg.monarchdefender.com%2Fmedia%2F1772728604357-peutzg-dark-knight-side.webp.webp&w=828&q=75`
- Blueprint side view: `https://www.the-blueprints.com/blueprints-depot-restricted/cars/landrover/land_rover_defender_90_1990-83624.jpg`
- Four-view floorplan: `https://freecadfloorplans.com/wp-content/uploads/2023/05/land-rover-defender.jpg.webp`

## Status

The first-pass Defender 3D pair is superseded: its silhouette was not close enough to the supplied side view. The authoritative basis is now the stored side and rear images, starting with the side trace at `references/defender/side-trace-overlay.png`.

Do not rebuild the 3D beads from the earlier 120 x 58 / 120 x 128 guesses. Rebuild only after the side trace is approved, using the traced side outline, window/door/wheel positions, and the rear reference as the next drawing stage.

## Trace conventions

- Green: outer body silhouette (wheels included, so the wheel outlines sit inside it).
- Orange: visible side door seam, handle and hinges. The 90 has one side door; the rear quarter is fixed bodywork.
- Cyan: front door window, rear side window, alpine roof window and window divisions.
- Yellow: road-wheel tyres, rims, hubs and wheel nuts.
- Amber: spare wheel behind the rear body.
- Included: side step.
- Omitted on purpose: wing mirror, mudflaps, exhaust.
