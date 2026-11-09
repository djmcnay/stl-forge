# cards

Playing-card accessories. The first part is a parametric deck box for
**UNO Junior** cards.

## Card sizes (validated 2026-11-09)

`card-sizes.json` is the source of truth. Sizes are millimetres; `width` is
the short side, `height` the long side, and `corner_radius` is the card's
corner curvature.

| format | width | height | corner radius | notes |
|---|---:|---:|---:|---|
| Poker / standard | 63.5 | 88.9 | 3.5 | 2.5 x 3.5 in. Publishers often round it to 63 x 88 mm (TCG nominal); the exact imperial size is 63.5 x 88.9. |
| Bridge (reference) | 57 | 89 | 3.5 | 2.25 x 3.5 in. Narrower than poker. Included to show it is *not* the UNO size. |
| **UNO Junior** | **56** | **87** | **3.5** | 56 x 87 mm, the "Standard USA" sleeve size. **Not bridge** (bridge is 57 x 89). |

Corner radius: the print-industry standard is 1/8 in = 3.175 mm; metric
printers quote 3.5 mm. Both are in the same 3.0-3.5 mm band. UNO print
guides (third-party) use 3.5 mm; Mattel does not publish a die line.
Sources and URLs are recorded per card in `card-sizes.json`.

Two size corrections against the initial guesses:

- Poker is 63.5 x 88.9 mm exactly. "63 x 88" is the rounded publisher/TCG
  nominal, not the exact card.
- UNO Junior is 56 x 87 mm. It is narrower and shorter than bridge
  (57 x 89), so it is its own size, not a bridge card.

## UNO Junior deck box

A simple vertical deck holder: the deck stands on its long edge, the open
side is the top, and the large front face carries the Artemis logo.

**What it holds:** one UNO Junior deck, 56 x 87 mm cards, 15 mm thick.

**Dimensions (mm):**

| | width (X) | depth (Y) | height (Z) |
|---|---:|---:|---:|
| card / deck | 56 | 15 | 87 |
| internal cavity | 56.6 | 15.6 | 87.6 |
| external | 60.6 | 19.6 | 89.6 |

- 2 mm walls and floor (`wall`).
- 0.6 mm total card clearance (`fit`, 0.3 mm per side). Tune this first if
  the print is too tight or too loose.
- Open top = card short side x deck thickness (56 x 15 nominal).
- The inner rim of the open top has a 1 mm chamfer. It flares the entry
  from 56.6 x 15.6 to 58.6 x 17.6 at the top surface, so the deck drops in
  without catching.
- A **17.5 mm-diameter semicircular thumb arch** runs through the front
  face, the back face and the bottom, centred on the width. It leaves two
  floor rails for the deck to sit on and a 17.5 mm-wide channel underneath;
  push the deck up through the channel with your thumb. The arch is
  8.75 mm tall at its crown.
- The front face carries `assets/artemis-logo.svg` centred, engraved
  0.8 mm deep. The SVG file is 45 mm square, but its artwork occupies
  about 37.75 mm x 35.11 mm of that box, so the visible mark is about
  37.8 mm wide. The black areas of the SVG are cut; the white figure
  stays flush.
- Print orientation: floor on the bed, open top up. No supports. The
  engraving is on a vertical wall.

### Design choices worth knowing

- "Open side = short end x deck thickness" and "front face has the logo in
  the centre" are read as a **vertical holder**: open top of 56 x 15, front
  face of 56 x 87. A flat tray would put the logo on a 15 mm-tall edge,
  which is too small for the 45 mm badge.
- The thumb arch is a half-cylinder **along the deck thickness**, not a
  shallow floor notch: it opens the front and back faces and removes a
  17.5 mm-wide strip of the floor, so a thumb can come up from underneath.
  It is a parameter (`thumb_arch_d`).
- Engraving (cut) rather than embossing keeps the outside snag-free and
  needs no supports.

## Files

| path | what |
|---|---|
| `card-sizes.json` | validated card sizes and corner radii |
| `param-defaults.json` | canonical box parameter snapshot + derived dimensions |
| `presets.json` | named preset for the UNO Junior box |
| `assets/artemis-logo.svg` | 45 mm Artemis SVG (37.8 mm visible artwork; same file as the play-coins logo) |
| `solidcraft/uno-junior-box.sc` | SolidCraft source model |
| `solidcraft/uno-junior-box.step` | STEP export for CAD interchange |
| `stl/uno-junior-box.stl` | print STL (gitignored) |
| `tests/test_card_sizes.py` | checks the card data and box defaults agree |
| `templates/`, `tools/`, `.tmp/` | reserved for the OpenSCAD replication / scratch |

The printable copy is delivered to `~/Downloads/stl-forge/`.

## Changing it

In SolidCraft the model is fully parametric. User parameters:

`card_w`, `card_h`, `deck_t`, `wall`, `fit`, `entry_chamfer`,
`thumb_arch_d`, `logo_w`, `logo_depth`.

Change one, rebuild, and the shell, chamfer, thumb arch and logo follow. The
one exception is the face/edge picks: they are resolved once and then
follow their edge/face, which is what keeps the model editable.

An OpenSCAD replication is not written yet; this project is a SolidCraft
design first.
