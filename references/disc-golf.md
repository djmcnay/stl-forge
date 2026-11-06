# Disc golf discs (printing, flight numbers, free files)

Domain notes for the principal's local course and for printing discs.
Everything here is sourced from the pages named; re-check prices and
availability before quoting.

## Flight numbers

Written speed / glide / turn / fade.

- **Speed (1-14)**: the airspeed you must supply for the disc to fly as
  designed. Not how fast it goes. A wide-rim speed-12 driver thrown by a
  beginner dumps left like a brick.
- **Glide (1-7)**: lift. Higher stays up longer, drifts more in wind.
- **Turn (-5 to +1)**: rightward curl during the fast phase for a right
  hand backhand. Negative = understable = flatters a weak arm.
- **Fade (0-5)**: leftward drop as it slows. Fade 3+ is the thing that
  makes a beginner's first round miserable.

Numbers are manufacturer marketing, not measurements; the ordering is
reliable even when the values are inflated (glide most of all).

## What to recommend for a beginner

- Putter: 2-3 speed, 3-4 glide, turn 0, fade 1-2. Aviar 2/3/0/1, Judge
  2/4/0/1, Wizard 2/3/0/2, Luna 3/3/0/2.
- Midrange: 4-5 / 4-5 / -1 to 0 / 1. Buzzz 5/4/-1/1, Mako3 5/5/0/0,
  Hex 5/5/-1/1, Shark 4/4/0/2.
- Fairway, only if asked for distance: 6-7 / 5-7 / -2 to -1 / 1. Leopard
  6/5/-2/1, River 7/7/-1/1, FD 7/6/-1/1.
- Ignore anything 9 speed or faster, and anything fade 3 or more, as a
  first disc.
- One putter plus one midrange covers most of a beginner round. The
  Innova DX starter set (Aviar, Shark, Leopard) is the correct cheap
  answer; unknown-brand Amazon "disc golf sets" usually ship a speed-13
  driver and make the game feel harder.

## Alice Holt Forest course (Farnham, GU10 4LS)

9 holes, dual tees (advanced and beginner), heavily wooded, moderately
hilly, holes 40m to 200m, par 30, designed by Richard Hatton (Disc Golf
UK), opened 2025. Free to play, no booking, about an hour and 1.3km per
round. First tee just off the path opposite the visitor centre info
point; parking charges apply. Not pushchair friendly on course. Score on
the UDisc app.

Disc hire at the visitor centre: GBP 3.50 per disc or GBP 12 for four;
Forestry England members GBP 3.00 and GBP 10.00.
https://www.forestryengland.uk/alice-holt-forest/disc-golf-alice-holt
https://www.dgcoursereview.com/courses/alice-holt-dgc.16449

Wooded and hilly means accuracy beats distance: recommend straight,
controlled discs, not drivers. Canopy means light wind, so glide helps.

## Free files worth recommending

- **RyanMarr/parametric-disc-golf** (MIT): parametric OpenSCAD solving
  the cross-section from official PDGA measurements of 28 real molds,
  plus `disc.json` Customizer presets and a browser designer with live
  profile, weight estimate (Pappus theorem, `print_factor` 0.94 default)
  and legality checks. `flat_top` forces a planar top and exports
  already flipped, so it prints top down with no supports. Text engraving
  only (`label_text`, underside, mirrored, 0.4mm default); no SVG or
  image import. Repo is young and the author had not flown one when he
  posted: correct numbers, unproven flight.
  https://github.com/RyanMarr/parametric-disc-golf
  https://ryanmarr.github.io/parametric-disc-golf/designer.html
- **Printables 1775001** (astrophage): the same generator as an Onshape
  FeatureScript feature that auto-splits the disc into four support-free
  parts. Drops underside engraving, automatic weight and flight-number
  reporting relative to the .scad.
- **MakerWorld 2097041** (Kitty Hawk): four-part, glued, no supports,
  TPU 95A, tuned to about 173g, author reports 5/4/0/1.5 and a near-RPM
  Kotuku flight; floats at low infill. Onshape source linked. The best
  flight-verified free starting point.
- **Printables 1272645** (bengineer700, Cricket, Hummingbird Flight Tech):
  the only free file that is also a PDGA approved production disc. Cert
  22-170, approved Oct 2022, 175.1g max, 21.1cm, rim depth 8.1%. Geometry
  and scale must not change; only that .3mf counts. 85A-90A TPU for
  putting, 95A for a driving putter, roughly 3/3/0/2 at 150g.
- Do not recommend: Printables 100847 (author admits the fairway
  proportions are wrong, specifies 100% PLA infill), Thingiverse 4057615
  UMF3D mold set (2019 rim profiles, no flight report), Cults discgolf
  results without a flight report.

## PDGA approval mechanics

Approval attaches to a manufacturer and a disc, not a shape. The brand
submits three samples, pays USD 500, the model name must be moulded in
raised lettering, the disc must carry "PDGA Approved", and it must be
"essentially as produced". Homemade prints are not tournament legal even
when they match an approved file exactly. Numbers that matter if
matching a real mold: diameter 21.0-30.0cm, weight at most 8.3g per cm
of diameter (200g absolute), rim depth 5-12% of diameter, rim width at
most 2.6cm, inside rim diameter at least 15.8cm, flight plate at most
0.5cm.
https://www.pdga.com/technical-standards/guidelines

## Printing discs in TPU

- 95A is the sweet spot; 85A-90A for putting putters; 64D reportedly
  feels closest to premium injection moulded plastic. Rigid filament
  cracks on the first tree.
- Discs print upside down with the top on the plate. A domed top printed
  that way touches at a point and needs supports, which is why the
  flat_top / four-part split routes exist. Top-down also gives the top
  face build-plate smoothness, which is where a logo belongs.
- A logo on the top face is a first-layer feature: keep engraving 0.4 to
  0.6mm, and get contrast from a filament change at layer two or three
  rather than multi-material TPU.
- TPU is hygroscopic: dry it or it strings. Slow speeds, direct drive,
  0.15-0.2mm layers, minimal part cooling, print one at a time.
- Stability is set by how much mass sits in the rim versus the flight
  plate, so walls and infill placement change behaviour more than the
  shape sliders at a fixed total weight.

## Commercial reference point

Forge Discs (forgediscs.com) sell 3D printed TPU discs (Nail, Ash,
Temper, Tanto, Fuller) at about USD 20, PDGA approved, and publish no
STL or STEP files. The Amolen blog post about them is filament marketing,
not a file release; do not go looking for a download behind it.
