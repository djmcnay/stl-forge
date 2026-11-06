#!/usr/bin/env python3
"""giant-beads: one-command entry for the giant-bead family artefacts.

Modes (combinable): --letters merges a word's unique letters into ONE
row-layout STL; --parts renders heart/star/flower shapes; --preset renders
one bead preset (body+letter+assembly STLs plus the Bambu .3mf, as the old
forge.py suite did). Artefacts land in --save-to (default $HOME/Downloads);
--previews additionally writes PNG previews into <save_to>/previews/.

Exit 0 only when every requested artefact exists and is a valid binary STL
(80-byte binary header, facet count n at offset 80, size == 84 + 50*n); any
failed job prints a precise stderr message and the run exits nonzero.

Input-contract gates (exit 2 before any render): a non-blank --letters /
spec letters value with no A-Z letter cannot silently vanish (the letter
job must run or the command fails); --word-gap must be a finite number
>= 0 (0 = touching beads); width must be a positive INTEGRAL number of mm
(flag parsing already rejects non-integers; --spec fractional/boolean/
string widths are rejected, never silently truncated); --spec field types
are validated with named-field messages (bool 123-style values never
crash with an AttributeError/TypeError).

Stdlib only. Reuses the root renderer helpers: sys.path is set so
`import forge` resolves to the skill root regardless of cwd.
"""
import argparse
import json
import math
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SKILL_DIR = PROJECT_DIR.parent.parent          # skills/stl-forge
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

import forge  # noqa: E402  (root renderer/packager)

TEMPLATES_DIR = PROJECT_DIR / "templates"
PRESETS_FILE = PROJECT_DIR / "presets.json"
WORD_BASE_PRESET = "bead_default"
SPEC_KEYS = {"letters", "parts", "width", "save_to", "preset"}

DEFAULT_WIDTH = 120
DEFAULT_WORD_GAP = 10.0
STL_MIN_BYTES = forge.STL_MIN_BYTES

# --parts mapping: part name -> (template filename, -D overrides).
# heart: bead_heart.scad at default bubble, star: bead_star.scad at template
# defaults, flower: bead_star.scad driven into full flower (roundness 20).
PART_JOBS = {
    "heart": ("bead_heart.scad", {}),
    "star": ("bead_star.scad", {}),
    "flower": ("bead_star.scad", {"roundness": 20, "petal_depth": 3}),
}


# --- spec parsing and normalisation (pure, unit-tested) -------------------

def normalise_word(raw: str) -> str:
    """Uppercase ASCII letters only, in order ('C A M I L A' -> 'CAMILA')."""
    return "".join(c for c in (raw or "").upper() if "A" <= c <= "Z")


def dedupe_letters(word: str):
    """Unique letters, order preserved ('CAMILA' -> C,A,M,I,L)."""
    seen = set()
    out = []
    for c in word:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def parse_parts(raw) -> list:
    """Comma-separated part list -> validated job specs.

    Returns a list of (part_name, template_name, overrides) tuples; raises
    ValueError on unknown part names.
    """
    if raw is None:
        return []
    wanted = [s.strip() for s in str(raw).split(",") if s.strip()]
    unknown = [w for w in wanted if w not in PART_JOBS]
    if unknown:
        raise ValueError(
            f"unknown part(s) {', '.join(unknown)};"
            f" available: {', '.join(sorted(PART_JOBS))}")
    return [(name, tmpl, dict(ov)) for name, (tmpl, ov) in
            ((w, PART_JOBS[w]) for w in wanted)]


def _json_type_name(value) -> str:
    """Readable JSON-ish type name for a decoded --spec value."""
    return {type(None): "null", bool: "boolean", int: "number",
            float: "number", str: "string", list: "list",
            dict: "object"}.get(type(value), type(value).__name__)


def validate_spec(spec) -> None:
    """Type/shape-check decoded --spec fields; raise ValueError on bad input.

    Named-field diagnostics only: a malformed field is rejected up front
    so nothing downstream silently coerces (120.9 -> 120, true -> 1) or
    crashes with an AttributeError/TypeError on its own.
    """
    for key in ("parts", "save_to", "preset"):
        value = spec.get(key)
        if value is not None and not isinstance(value, str):
            raise ValueError(
                f'--spec field "{key}" must be a string'
                f" (got {_json_type_name(value)} {value!r})")
    letters_val = spec.get("letters")
    if letters_val is not None and not isinstance(letters_val, str):
        if isinstance(letters_val, list):
            for entry in letters_val:
                if not isinstance(entry, str) or entry == "":
                    raise ValueError(
                        f'--spec field "letters" must be a string or a'
                        f" list of non-empty strings"
                        f" (bad entry {entry!r})")
        else:
            raise ValueError(
                f'--spec field "letters" must be a string or a list of'
                f" non-empty strings"
                f" (got {_json_type_name(letters_val)} {letters_val!r})")
    width_val = spec.get("width")
    if width_val is not None:
        if isinstance(width_val, bool):
            raise ValueError(
                f'--spec field "width" must be a number of mm, not a'
                f" boolean (got {width_val!r}); use a finite integer > 0")
        if not isinstance(width_val, (int, float)):
            raise ValueError(
                f'--spec field "width" must be a number of mm'
                f" (got {_json_type_name(width_val)} {width_val!r})")
        if not math.isfinite(width_val) or width_val <= 0:
            raise ValueError(
                f'--spec field "width" must be a finite number > 0'
                f" (got {width_val})")
        if width_val != int(width_val):
            raise ValueError(
                f'--spec field "width" must be an integral number of mm'
                f" (got {width_val}); fractional widths are rejected"
                f" instead of being silently truncated to"
                f" {int(width_val)}")


def word_gap_error(gap) -> str:
    """Error message for an invalid --word-gap, else None (0 is allowed:
    a zero gap means touching beads)."""
    if isinstance(gap, bool) or not isinstance(gap, (int, float)) \
            or not math.isfinite(gap):
        return f"--word-gap must be a finite number >= 0 (got {gap!r})"
    if gap < 0:
        return f"--word-gap must be a finite number >= 0 (got {gap})"
    return None


def resolve_save_to(value):
    """--save-to resolution: None -> $HOME/Downloads; else the given path."""
    return Path.home() / "Downloads" if value is None else Path(value)


def merged_stl_name(word: str) -> str:
    """Row-layout STL name for a word: beads_<WORD>.stl."""
    return f"beads_{word}.stl"


def explicit_letters(raw) -> tuple:
    """(explicit?, normalised unique letters) for a raw --letters value.

    explicit is True only when the caller passed a non-blank letters
    value (CLI flag or spec field): an absent/empty value is NOT an
    explicitly requested letter job and must keep its old semantics.
    """
    if raw is None:
        return False, []
    if not str(raw).strip():
        return False, []
    return True, dedupe_letters(normalise_word(raw))


def part_stl_name(part: str) -> str:
    return f"bead_{part}.stl"


# --- STL validation rule --------------------------------------------------

def validate_binary_stl(path: Path):
    """Precise error message for an invalid/missing artefact, else None.

    Rule: file exists, is binary STL (an 80-byte header, not an ASCII
    "solid <name>" / "facet normal" document), carries a facet count n at
    offset 80 (>0) and is exactly 84 + 50*n bytes.
    """
    if not path.is_file():
        return f"missing STL {path}"
    data = path.read_bytes()
    if len(data) < 84:
        return f"{path}: too small ({len(data)} bytes) for a binary STL"
    if b"facet normal" in data[:2048]:
        return f"{path}: ASCII STL, not a binary STL"
    (n,) = struct.unpack_from("<I", data, 80)
    if n <= 0:
        return f"{path}: facet count at offset 80 is {n}"
    if len(data) != 84 + 50 * n:
        return f"{path}: size {len(data)} != 84 + 50*{n} (facet count {n})"
    return None


# --- argv / spec merge ----------------------------------------------------

class Config:
    __slots__ = ("letters", "parts", "width", "save_to", "preset",
                 "presets", "previews", "word_gap")

    def __init__(self):
        self.letters = None      # raw string
        self.parts = None        # raw string
        self.width = None        # int (explicit only)
        self.save_to = None      # raw string
        self.preset = None       # raw string
        self.presets = None      # raw path to presets file
        self.previews = False
        self.word_gap = DEFAULT_WORD_GAP


def apply_flags(cfg, ns_like):
    """Apply explicitly-set CLI flags onto a Config (spec fields first)."""
    if ns_like.letters is not None:
        cfg.letters = ns_like.letters
    if ns_like.parts is not None:
        cfg.parts = ns_like.parts
    if getattr(ns_like, "width", None) is not None:
        cfg.width = int(ns_like.width)
    if ns_like.save_to is not None:
        cfg.save_to = ns_like.save_to
    if getattr(ns_like, "preset", None) is not None:
        cfg.preset = ns_like.preset
    if getattr(ns_like, "presets", None) is not None:
        cfg.presets = ns_like.presets
    cfg.previews = cfg.previews or bool(getattr(ns_like, "previews", False))
    if getattr(ns_like, "word_gap", None) is not None:
        cfg.word_gap = float(ns_like.word_gap)
    return cfg


def config_from_args(ns) -> Config:
    cfg = Config()
    # 1. Spec fields first (exact key names: letters, parts, width,
    #    save_to, preset). Types are validated up front so no field is
    #    ever silently coerced.
    if ns.spec is not None:
        try:
            spec = json.loads(ns.spec)
            assert isinstance(spec, dict)
        except (ValueError, AssertionError) as e:
            raise ValueError("--spec must be a JSON object") from e
        unknown = sorted(set(spec) - SPEC_KEYS)
        if unknown:
            raise ValueError(f"--spec has unknown key(s): {', '.join(unknown)}")
        validate_spec(spec)

        # A spec letters LIST is shorthand for a space-joined word
        # (["C","A","M"] == "C A M"); after validation every entry is a
        # non-empty string.
        letters_val = spec.get("letters")
        if isinstance(letters_val, list):
            letters_val = " ".join(letters_val)

        class _SpecNS:
            pass

        spec_ns = _SpecNS()
        spec_ns.letters = letters_val
        spec_ns.parts = spec.get("parts")
        spec_ns.width = spec.get("width")
        spec_ns.save_to = spec.get("save_to")
        spec_ns.preset = spec.get("preset")
        spec_ns.presets = None
        spec_ns.previews = False
        spec_ns.word_gap = None
        apply_flags(cfg, spec_ns)
    # 2. Explicit flags override the spec.
    return apply_flags(cfg, ns)


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="giant-beads one-command entry: word rows, shapes, "
                    "and bead presets into --save-to (default $HOME/"
                    "Downloads).")
    p.add_argument("--width", type=int, default=None,
                   help="bead width in mm passed through to the templates"
                        f" (default {DEFAULT_WIDTH})")
    p.add_argument("--letters", default=None,
                   help="word of letters; unique letters render as ONE"
                        " row-layout STL beads_<WORD>.stl (e.g. 'C A M I L A')"
                        " with a clear 10 mm gap")
    p.add_argument("--parts", default=None,
                   help="comma list of heart,star,flower (harmless if empty)")
    p.add_argument("--preset", default=None,
                   help="render one bead preset from the project's"
                        " presets.json (bead_D / bead_default / bead_smooth)")
    p.add_argument("--presets", default=None,
                   help="path to a presets JSON file (default: the project's"
                        " presets.json)")
    p.add_argument("--save-to", default=None,
                   help="output directory (default $HOME/Downloads; created"
                        " if missing)")
    p.add_argument("--spec", default=None,
                   help="alternate input form: JSON dict with keys letters,"
                        " parts, width, save_to, preset (explicit flags"
                        " override)")
    p.add_argument("--previews", action="store_true",
                   help="also write PNG previews into <save-to>/previews/")
    p.add_argument("--word-gap", type=float, default=None,
                   help="clear gap in mm between neighbouring beads in"
                        f" --letters mode (default {DEFAULT_WORD_GAP})")
    return p.parse_args(argv)


# --- rendering ------------------------------------------------------------

def _run_openscad(args, label):
    proc = subprocess.run(["openscad"] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"[FAIL] {label}: openscad exited {proc.returncode}",
              file=sys.stderr)
        print(f"  cmd: openscad {' '.join(args)}", file=sys.stderr)
        if proc.stdout:
            print(f"  --- stdout ---\n{proc.stdout}", file=sys.stderr)
        if proc.stderr:
            print(f"  --- stderr ---\n{proc.stderr}", file=sys.stderr)
    return proc


def render_letters_letters(word, letters, base_params, width, out_dir,
                           gap, preview_dir, want_previews):
    """Render one bead per unique letter and merge into a row-layout STL.

    Mirrors the historical forge.py --word pipeline exactly (same layout
    formula, same binary-concat merge), so facet counts are unchanged.
    Returns a list of failure strings (empty = ok).
    """
    labels = []
    n = len(letters)
    template_path = forge.resolve_template(
        base_params.get("template", "bead.scad"))
    if not template_path.is_file():
        return [f"letters: missing template {template_path}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    merged_path = out_dir / merged_stl_name(word)

    with tempfile.TemporaryDirectory(prefix="giant-beads-letters-") as tmp:
        tmpdir = Path(tmp)
        src_paths = []
        src_facets = []
        for letter in letters:
            src = tmpdir / f"bead_{letter}.stl"
            d = forge.d_args_for_params(base_params, {
                "part": "assembly",
                "letter_top": letter,
                "letter_bottom": letter,
                "width": width,
            })
            label = f"letters:{letter} stl"
            labels.append(label)
            proc = _run_openscad(
                ["--export-format=binstl", "-o", str(src), str(template_path)]
                + d, label)
            if proc.returncode != 0:
                return [f"letters:{letter}: STL render failed"]
            if not src.is_file():
                return [f"letters:{letter}: openscad produced no STL"]
            if src.stat().st_size <= STL_MIN_BYTES:
                return [f"letters:{letter}: STL too small "
                        f"({src.stat().st_size} bytes)"]
            try:
                facets = forge.count_facets(src)
            except Exception as e:  # noqa: BLE001
                return [f"letters:{letter}: facet count failed: {e}"]
            if facets <= 0:
                return [f"letters:{letter}: facet count is {facets}"]
            src_paths.append(src)
            src_facets.append(facets)

        # Layout: row along +X centred on x=0 (clear `gap` between bboxes).
        centres = []
        spans = []
        for src in src_paths:
            _, xmin, xmax, _, _ = forge._binary_stl_stats(src)
            centres.append((xmin + xmax) / 2.0)
            spans.append(xmax - xmin)
        bead_width = max(spans)
        pitch = bead_width + gap
        dxs = [i * pitch - (n - 1) * pitch / 2.0 - centres[i]
               for i in range(n)]

        # Merge by direct binary concatenation with x-offset only; the
        # 80-byte header stays a valid binary-STL header (facet count
        # lives at offset 80, size rule 84 + 50*n).
        header = b"solid giant-beads row-layout (bin)"
        header = header + b"\0" * (80 - len(header))
        total = int(sum(src_facets))
        with open(merged_path, "wb") as out:
            out.write(header)
            out.write(struct.pack("<I", total))
            for src, dx in zip(src_paths, dxs):
                data = src.read_bytes()
                (sn,) = struct.unpack_from("<I", data, 80)
                for j in range(sn):
                    off = 84 + j * 50
                    rec = bytearray(data[off:off + 50])
                    for b_off in (0, 12, 24, 36):
                        (xf,) = struct.unpack_from("<f", rec, b_off)
                        struct.pack_into("<f", rec, b_off, xf + dx)
                    out.write(rec)

    # Self-assertions straight off the binary at runtime.
    failures = []

    def _assert(cond, msg):
        if not cond:
            print(f"[letters] assert FAIL {msg}", file=sys.stderr)
            failures.append(f"letters: merged STL failed self-check: {msg}")
            return
        print(f"[letters] assert {msg} ok")

    try:
        (merged_n,) = struct.unpack_from("<I",
                                         merged_path.read_bytes(), 80)
        msize = merged_path.stat().st_size
        _, mxmin, mxmax, mzmin, _ = forge._binary_stl_stats(merged_path)
    except Exception as e:  # noqa: BLE001
        return [f"letters: merged STL unreadable: {e}"]
    src_sum = int(sum(src_facets))
    _assert(merged_n == src_sum,
            f"merged facets {merged_n} == sum(source facets) {src_sum}")
    _assert(msize == 84 + 50 * merged_n,
            f"file size {msize} == 84 + 50*{merged_n}")
    merged_span = mxmax - mxmin
    expected_span = (n - 1) * pitch + bead_width if n else 0.0
    _assert(abs(merged_span - expected_span) < 1e-4,
            f"merged x-span {merged_span:.4f} == (n-1)*pitch+bead_width"
            f" {expected_span:.4f}")
    _assert(abs((mxmin + mxmax) / 2.0) < 1e-4,
            f"merged x-centre {(mxmin + mxmax) / 2.0:.6f} symmetric about 0")
    _assert(abs(mzmin - 0.0) < 1e-5,
            f"merged min z {mzmin:.6f} == 0")

    if want_previews:
        import_line = 'import("%s");\n' % str(
            merged_path.resolve()).replace("\\", "/").replace('"', '\\"')
        preview_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="giant-beads-prev-") as tmp:
            scad_path = Path(tmp) / f"beads_{word}.scad"
            scad_path.write_text(import_line, encoding="utf-8")
            for view in ("iso", "front"):
                png = preview_dir / f"beads_{word}_{view}.png"
                labels.append(f"letters preview {view}")
                proc = _run_openscad(
                    ["-o", str(png), "--imgsize=640,480", "--autocenter",
                     "--viewall", "--camera", forge.CAMERAS[view],
                     str(scad_path)],
                    f"letters preview {view}")
                if proc.returncode != 0:
                    failures.append(f"letters: preview {view} render failed")
                elif not png.is_file():
                    failures.append(f"letters: missing preview {png}")
                elif png.stat().st_size <= forge.PNG_MIN_BYTES:
                    failures.append(
                        f"letters: preview {view} too small")

    print(f"LETTERS {word} unique {' '.join(letters)} -> {merged_path}"
          f" facets {merged_n}")
    return failures


def render_part_job(part, template_name, overrides, width, out_dir,
                    preview_dir, want_previews):
    """Render one heart/star/flower STL (+ previews when asked)."""
    template_path = forge.resolve_template(template_name)
    if not template_path.is_file():
        return [f"parts:{part}: missing template {template_path}"]
    stl_path = out_dir / part_stl_name(part)
    d = forge.d_args_for_params({"width": width}, overrides)
    proc = _run_openscad(
        ["--export-format=binstl", "-o", str(stl_path), str(template_path)]
        + d, f"parts:{part} stl")
    if proc.returncode != 0:
        return [f"parts:{part}: STL render failed"]
    err = validate_binary_stl(stl_path)
    if err:
        return [f"parts:{part}: {err}"]
    if want_previews:
        preview_dir.mkdir(parents=True, exist_ok=True)
        for view, cam in forge.CAMERAS.items():
            png = preview_dir / f"bead_{part}_{view}.png"
            proc = _run_openscad(
                ["-o", str(png), "--imgsize=640,480", "--autocenter",
                 "--viewall", "--camera", cam, str(template_path)] + d,
                f"parts:{part} preview {view}")
            if proc.returncode != 0:
                return [f"parts:{part}: preview {view} render failed"]
            if not png.is_file():
                return [f"parts:{part}: missing preview {png}"]
            if png.stat().st_size <= forge.PNG_MIN_BYTES:
                return [f"parts:{part}: preview {view} too small"]
    print(f"PART {part} (template {template_name}) -> {stl_path}"
          f" facets {forge.count_facets(stl_path)}")
    return []


def render_preset(name, params, presets_file, out_dir, preview_dir,
                  want_previews, width_override=None):
    """Render one bead preset exactly as the old forge.py suite did:
    assembly + body + letter STLs, then the Bambu-native .3mf."""
    template_path = forge.resolve_template(
        params.get("template", "bead.scad"))
    if not template_path.is_file():
        return [f"preset:{name}: missing template {template_path}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = params.get("parts")
    merged = dict(params)
    if width_override is not None:
        merged["width"] = int(width_override)
    base_d_args = forge.d_args_for_params(merged)
    stl_targets = []
    if parts:
        stl_targets.append((None, out_dir / f"{name}.stl",
                            base_d_args + ["-D", 'part="assembly"']))
        for part_label in parts:
            stl_targets.append((part_label, out_dir / f"{name}_{part_label}.stl",
                                base_d_args + ["-D", f'part="{part_label}"']))
    else:
        stl_targets.append((None, out_dir / f"{name}.stl", base_d_args))

    for part_label, stl_path, d in stl_targets:
        label = f"preset:{name}:{part_label}" if part_label else \
            f"preset:{name}"
        proc = _run_openscad(
            ["--export-format=binstl", "-o", str(stl_path),
             str(template_path)] + d, f"{label} stl")
        if proc.returncode != 0:
            return [f"{label}: STL render failed"]
        err = validate_binary_stl(stl_path)
        if err:
            return [f"{label}: {err}"]

    mf_path = out_dir / f"{name}.3mf"
    if parts and len(parts) == 2:
        body_stl = out_dir / f"{name}_{parts[0]}.stl"
        letter_stl = out_dir / f"{name}_{parts[1]}.stl"
        try:
            n_body, n_letter = forge.build_bead_3mf(
                name, body_stl, letter_stl, mf_path)
        except Exception as e:  # noqa: BLE001
            return [f"preset:{name}:3mf: build failed: {e}"]
        problems = forge.validate_bead_3mf(mf_path, n_body, n_letter)
        if problems:
            return [f"preset:{name}:3mf: {note}" for note in problems]
    elif parts:
        return [f"preset:{name}:3mf: expected 2 parts, found {len(parts)}"]

    if want_previews:
        preview_part = params.get("preview")
        preview_dir.mkdir(parents=True, exist_ok=True)
        for view, cam in forge.CAMERAS.items():
            png = preview_dir / f"{name}_{view}.png"
            d = base_d_args + (["-D", f'part="{preview_part}"']
                               if preview_part else [])
            proc = _run_openscad(
                ["-o", str(png), "--imgsize=640,480", "--autocenter",
                 "--viewall", "--camera", cam, str(template_path)] + d,
                f"preset:{name} preview {view}")
            if proc.returncode != 0:
                return [f"preset:{name}: preview {view} render failed"]
            if not png.is_file():
                return [f"preset:{name}: missing preview {png}"]
            if png.stat().st_size <= forge.PNG_MIN_BYTES:
                return [f"preset:{name}: preview {view} too small"]

    print(f"PRESET {name} from {presets_file.name} -> {out_dir / name}.stl"
          + (" (+.3mf)" if parts else ""))
    return []


def main(argv=None) -> int:
    ns = parse_args(argv)
    try:
        cfg = config_from_args(ns)
    except ValueError as e:
        print(f"giant-beads: {e}", file=sys.stderr)
        return 2
    gap_err = word_gap_error(cfg.word_gap)
    if gap_err is not None:
        print(f"giant-beads: {gap_err}", file=sys.stderr)
        return 2

    explicit, letters = explicit_letters(cfg.letters)
    try:
        part_jobs = parse_parts(cfg.parts)
    except ValueError as e:
        print(f"giant-beads: {e}", file=sys.stderr)
        return 2
    # BLOCK: a non-blank --letters / spec letters value that carries no
    # A-Z letter must NOT silently vanish (the letters normalisation
    # emptied it, so no letter job would run while the command returned
    # 0). An explicitly requested letter job either runs or makes the
    # command fail; a merely absent/empty letters value stays valid.
    if explicit and not letters:
        print(f'giant-beads: --letters "{cfg.letters}": no renderable A-Z '
              "letters in the request; the explicitly requested letter "
              "job could not run (other requested parts would render, "
              "but failing the run is required)", file=sys.stderr)
        return 2
    if not letters and not part_jobs and cfg.preset is None:
        print("giant-beads: nothing requested: give --letters, --parts"
              " and/or --preset (or --spec)", file=sys.stderr)
        return 2

    presets_path = Path(cfg.presets) if cfg.presets else PRESETS_FILE
    if not presets_path.is_file():
        print(f"giant-beads: missing presets file: {presets_path}",
              file=sys.stderr)
        return 1
    with open(presets_path, "r", encoding="utf-8") as f:
        presets = json.load(f).get("presets", {})

    base_params = presets.get(WORD_BASE_PRESET)
    if letters and base_params is None:
        print(f"giant-beads: word list needs the '{WORD_BASE_PRESET}' preset;"
              f" not in {presets_path}", file=sys.stderr)
        return 1

    width = cfg.width if cfg.width is not None else DEFAULT_WIDTH
    if width <= 0:
        print(f"giant-beads: --width must be a positive number of mm"
              f" (got {width})", file=sys.stderr)
        return 2
    save_to = resolve_save_to(cfg.save_to)
    save_to.mkdir(parents=True, exist_ok=True)
    preview_dir = save_to / "previews"

    failures = []
    word = None
    if letters:
        word = normalise_word(cfg.letters)
        failures += render_letters_letters(
            word, letters, base_params, width, save_to, cfg.word_gap,
            preview_dir, cfg.previews)
    if part_jobs:
        for part, template_name, overrides in part_jobs:
            failures += render_part_job(
                part, template_name, overrides, width, save_to,
                preview_dir, cfg.previews)
    if cfg.preset:
        name = cfg.preset
        params = presets.get(name)
        if params is None:
            failures.append(f"preset:{name}: not in {presets_path};"
                            f" available: {', '.join(sorted(presets))}")
        else:
            failures += render_preset(
                name, params, presets_path, save_to, preview_dir,
                cfg.previews,
                width_override=cfg.width)

    # Final gate: every requested artefact must exist and be a valid
    # binary STL.
    expected = []
    if letters:
        expected.append(save_to / merged_stl_name(word))
    expected += [save_to / part_stl_name(part)
                 for part, _, _ in part_jobs]
    if cfg.preset and cfg.preset in presets:
        expected.append(save_to / f"{cfg.preset}.stl")
        for part_label in (presets[cfg.preset].get("parts") or []):
            expected.append(
                save_to / f"{cfg.preset}_{part_label}.stl")
    for path in expected:
        err = validate_binary_stl(path)
        if err:
            failures.append(f"artefact: {err}")

    if failures:
        print("FAILURES:", file=sys.stderr)
        for msg in failures:
            print(f"  - {msg}", file=sys.stderr)
        return 1
    print(f"OK: {len(expected)} artefact(s) (plus "
          f"{'a' if cfg.preset and presets.get(cfg.preset, {}).get('parts') else 'no'}"
          f" Bambu .3mf) in {save_to}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
