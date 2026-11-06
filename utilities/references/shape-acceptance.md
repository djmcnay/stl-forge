# Shape acceptance against a reference silhouette

When a template's outline must LOOK like an image the principal
supplied (printable silhouettes, letterforms, character shapes),
acceptance is a stack of measurements plus his eye - in that order of
contact: show the comparison early, let the numbers support the
verdict, never let them replace it.

## Acceptance order

1. FIRST working draft: deliver a target-vs-actual stitch (reference
   mask beside the current render, same width normalisation, captioned
   with measured numbers) into the project folder - and to Telegram
   when he is away - before building any gate harness. Likeness
   rejections cost minutes at this stage and hours after a fitter has
   been tuned against proxies.
2. Build the gate suite only for defects he has actually named, with
   thresholds measured from the references themselves.
3. Every gate is fail-the-build with a sanctioned outcome: halt and
   report the failing number against threshold. A brief that only says
   'make gates pass' invites threshold relaxation.

## Metric vs defect class

| Detector | Catches | Blind to | 
|---|---|---|
| Width-normalised area IoU | gross scale, position, sway | interior straights, proportion drift (a flat notch floor moves ~0 area; a triangle can still score 0.95) |
| Max turn angle / curvature audit | creases, kinks, tangent breaks | straights (a straight has ZERO turn) |
| Straight-run scan (radius of curvature > ~40 mm sustained over >= ~5 mm of arc) | dead-flat spans - the only reliable straight detector | creases |
| Landmark ratios (depth % of a feature, width/height) | proportion-class errors | local texture |
| BBox / facet / manifold probe | scale errors, degenerate or empty renders | everything about shape |

No single metric is an acceptance criterion; area metrics in
particular must never be the optimisation objective for a likeness
task - fitters game them (folding a cusp into a wide point raises the
score while wrecking the shape). Keep structural rules (continuity,
minimum curvature, landmark bands) as hard constraints and let the
soft metric only rank candidates inside the feasible set.

## Reference preparation and calibration

- Width-normalise both masks to one convention (e.g. 600 px = the
  part's nominal width) before any comparison; measure everything in
  that space.
- Region-aware: a photographic or screen-captured reference carries
  its own top-row / side-column rasterisation fringe - strip it before
  calibrating, and exclude it from gates, or the reference fails its
  own threshold.
- Every gate threshold is calibrated by running the detector on BOTH
  reference images first: references must pass untouched. A threshold
  the reference fails is a broken threshold.
- Derive landmark targets (depth %, aspect) by measuring the
  references with the SAME code that will measure your render.

## Vector vs raster measurement

- Curvature, turn angles and straightness run on VECTOR contours: STL
  z-slice (float32 slab endpoints rarely match exactly - chain
  segments with a ~3e-3 tolerance and keep the largest ring, skipping
  the bore), or a traced outline sampled at fixed arc steps.
- Raster traces convert pixel staircases into ~90-degree phantom
  turns; use raster only for quick masks, bboxes and landmarks.
- Exclude a tip/point neighbourhood explicitly when its legitimate
  turning exceeds the crease threshold, and say so in the report.

## Known-answer self-tests (run before trusting any gate)

1. Identical silhouette against itself scores ~1.0.
2. A planted 6 mm straight on a circle FAILS the straightness gate;
   the pure circle passes.
3. Phase stability: the detector returns the same run counts from any
   contour start point (a phase-dependent result is measuring the
   tracer, not the shape).

## Blend sweeps (parametric families)

Render the full dial (every integer, plus fine steps near endpoints),
measure the landmark table per value, and require: no adjacent-value
cliff (max step well under the tolerance band), monotone landmark
progression, and every gate green at anchors AND interior samples.
Endpoint fits prove nothing about the interior - the blend rule is
where families break.

## Verdict handling

A reviewer consumes evidence you produced: run the full independent
verification first, stage one fenced review file (measurements with
thresholds, render paths, numbered questions, verdict file name,
SHIP/FIX first line), read the verdict END TO END - release
qualifications live in the body, not the sentinel - and implement a
FIX prescription verbatim, including any control measurement it
demands, before resubmitting.
