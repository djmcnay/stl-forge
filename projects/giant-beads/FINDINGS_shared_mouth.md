# FINDINGS: shared v2 string-hole countersink — one common SCAD module

Branch: `refactor/shared-hole-mouth` (cut from current `main` checkout;
never merged, never pushed). Working directory:
`/Users/djmcnay/GitHub/araminta-skills/skills/stl-forge/projects/giant-beads`.

## Files touched (commit order)

| Commit | File |
|---|---|
| 39747e4 | `templates/bead_common.scad` (NEW) |
| 94966f8 | `templates/bead_star.scad` |
| 7c91b4b | `templates/bead_heart.scad` |
| aec3e28 | `templates/bead.scad` |
| 9a1e261 | `README.md` (one sentence) |

Only the fence-listed paths were staged/committed; the dirty files from
other sessions (minty-sync, pi-media-server) were left unstaged and
untouched; `BRIEF_shared_mouth.md` was not edited and is left untracked
for the orchestrator to clean. No `.3mf` strings added.

## Per-file summary

- **`templates/bead_common.scad` (new)** — one reusable SUBTRACTIVE module
  `module bead_string_hole(hole_entry_x, n_out, R_throat, R_open, k,
  hole_len)` yielding exactly the union of: straight throat bore along X
  (radius `R_throat`, `cylinder(h=2*hole_len, r=R_throat, center=true)`
  rotated to X) + spherical countersink at the +x mouth (sphere
  `R_ball = sqrt(R_open^2 + k^2)` sunk `k` along the LOCAL wall normal
  `n_out` from the crossing `hole_entry_x`) + the mirrored -x countersink.
  Caller frame: hole axis X, bore centred on x=0; the caller supplies the
  z lift (each template's own `height/2` translate) and all local values.
  Full provenance comment block cites bead_star.scad lines 459–530 and
  bead.scad lines 134–165 (and names bead_heart.scad's copy).

- **`templates/bead_star.scad`** — `use <bead_common.scad>` added after
  the header block; private `module string_hole()` body replaced by a
  `bead_string_hole(...)` call forwarding the star's OWN local values
  exactly as derived today (`hole_entry_x` from the scale-invariant
  interpolated crossing, `n_out` from the flank recompute, `R_throat`,
  `R_open`, `k = k_scoop`, `hole_len`). No local value's derivation
  changed; the flank recompute per dial setting stays per-template; all
  asserts and the echo stay.

- **`templates/bead_heart.scad`** — same treatment: header `use`,
  `string_hole()` body replaced by the shared call forwarding the heart's
  local `hole_entry_x`, `n_out`, `R_throat`, `R_open`, `k`, `hole_len`;
  per-template derivation untouched.

- **`templates/bead.scad`** — header `use` added after the orientation
  notes; `string_hole()` body replaced by the shared call with
  `hole_entry_x = half` (= `width/2`) and `n_out = [1, 0]` (the straight
  cylinder wall's exact outward normal, as documented in the old
  construction comment), `R_throat`, `R_open`, `k = k_scoop`,
  `hole_len`. The letter-well/funnel code was NOT touched; no template
  defaults changed.

- **`README.md`** — the sentence in "The v2 spherical-countersink mouth"
  that described the family-wide standing procedure now also names the
  place where the ONE construction lives in code:
  `templates/bead_common.scad`'s `bead_string_hole(...)` (each template
  forwards its own local values). Minimal edit, 5 diff lines.

## Geometry-identity gate (hard)

Baseline pre-edit binary renders at template defaults (no `-D`), from the
pre-edit tree on `main`, were compared `cmp` against the read-only
reference baselines in
`/Users/djmcnay/.hermes/profiles/araminta/cache/scratch/mouth-baseline/`,
then the post-edit renders on `refactor/shared-hole-mouth` were compared
the same way.

```
pre-edit vs reference baselines:
cmp regr-baseline-check/bead_bin.stl        .../mouth-baseline/bead_base.stl        → BEAD_IDENTICAL
cmp regr-baseline-check/bead_heart_bin.stl  .../mouth-baseline/bead_heart_base.stl  → HEART_IDENTICAL
cmp regr-baseline-check/bead_star_bin.stl   .../mouth-baseline/bead_star_base.stl   → STAR_IDENTICAL
post-edit vs reference baselines:
cmp regr-baseline-check/bead_post.stl       .../mouth-baseline/bead_base.stl        → bead: BYTE-IDENTICAL
cmp regr-baseline-check/bead_heart_post.stl .../mouth-baseline/bead_heart_base.stl  → bead_heart: BYTE-IDENTICAL
cmp regr-baseline-check/bead_star_post.stl  .../mouth-baseline/bead_star_base.stl   → bead_star: BYTE-IDENTICAL
```

All three: **BYTE-IDENTICAL** via `openscad --export-format=binstl`
(deterministic writer here — even the header bytes match; the ASCII
fallback was not needed). Facet counts unchanged: bead 26009284 bytes /
520184 facets, heart 14645284 / 292904, star 1237284 / 24744.

## Verification transcript

```
$ openscad -o regr-baseline-check/<t>_bin.stl templates/<t>.scad   (defaults, no -D)
bead exit=0 (520184 facets, Genus 1)   bead_heart exit=0 (292904 facets)   bead_star exit=0 (24744 facets)
$ python3 main.py --parts heart,star,flower --save-to regr-suite
PART heart (template bead_heart.scad) -> regr-suite/bead_heart.stl facets 292904
PART star (template bead_star.scad) -> regr-suite/bead_star.stl facets 24744
PART flower (template bead_star.scad) -> regr-suite/bead_flower.stl facets 23232
OK: 3 artefact(s) (plus no Bambu .3mf) in regr-suite
SUIT_EXIT=0
$ python3 -m pytest tests/ -q
34 passed in 9.78s   (PYTEST_EXIT=0)
$ grep -rn "3mf" <touched files>
only pre-existing README prose lines (21, 48, 77, 144); no .3mf strings added
$ openscad -o /tmp/x.stl templates/<t>.scad   (standalone, no flags)
exit 0 for bead, bead_heart, bead_star
```

Extra identity checks: the suite's own defaults outputs
`regr-suite/bead_heart.stl` and `regr-suite/bead_star.stl` are also
`cmp`-identical to the reference baselines
(`SUITE_HEART_IDENTICAL`, `SUITE_STAR_IDENTICAL`; the flower render has
no baseline but renders clean at 23232 facets).

## Deviations

- The brief says run `python3 main.py --parts heart,star,flower` "with
  `--out` pointed at a scratch dir YOU create inside the repo root
  (prefix `regr-`)"; `main.py` has no `--out` flag — its output flag is
  `--save-to`, which was used instead (`--save-to regr-suite`,
  `SUIT_EXIT=0`). Intent honoured: scratch dir `regr-suite` inside the
  repo root.
- None other. Geometry zero-change gate passed outright (no ASCII
  fallback, no facet-count relaxation needed).
- Scratch dirs `regr-baseline-check/` and `regr-suite/` left untracked
  for the orchestrator; they were never staged or committed.
