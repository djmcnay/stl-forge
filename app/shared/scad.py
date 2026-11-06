"""OpenSCAD CLI helpers for the stl-forge generation app.

Everything the two tabs share: template discovery, top-parameter-block
parsing (literal-valued params only -> UI controls), -D argument
formatting, binary-STL probing (facet count from the 4-byte LE field at
offset 80, mirroring core/stl_probe.py read-only) and the
--imgsize/--camera PNG render pipeline documented in the skill root
SKILL.md (USAGE.md is not present in this checkout).

Renders land ONLY in app/.render-scratch/ - the app is a control panel,
never a delivery mechanism, so nothing here writes to a project output
folder. Stdlib only (the app runs on its own venv, not the Hermes one).
"""
from __future__ import annotations

import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

# --- paths (derived from this file, independent of cwd) --------------------
APP_DIR = Path(__file__).resolve().parents[1]        # .../skills/stl-forge/app
SKILL_ROOT = Path(__file__).resolve().parents[2]     # .../skills/stl-forge
TEMPLATES_DIR = SKILL_ROOT / "projects" / "giant-beads" / "templates"
SCRATCH_DIR = APP_DIR / ".render-scratch"

OPENSECAD = "openscad"

# Gimbal camera "tx,ty,tz,rx,ry,rz,dist" strings (forge.py CAMERAS):
# rx=ry=rz=0 looks straight down the z axis = face-on for the bead family,
# whose flat letter/star faces point up.
CAMERA_FACEON = "0,0,0,0,0,0,350"


class RenderError(RuntimeError):
    """OpenSCAD exited nonzero; .stderr carries the console tail."""


@dataclass(frozen=True)
class ScadParam:
    """One template parameter promoted to a UI control.

    Only LITERAL-valued params are surfaced: derived params (e.g.
    `height = width / 2`, `fillet_radius = width / 12`) must recompute,
    and bead_star asserts height == width/2, so overriding them would
    break every render. Literal defaults round-trip cleanly as -D args.
    """
    name: str
    value: object          # int | float | bool | str
    info: str = ""         # inline / preceding / header comment from the file


# --- template discovery -----------------------------------------------------

def list_templates() -> list[str]:
    """Filename stems of projects/giant-beads/templates/*.scad, sorted."""
    return sorted(p.stem for p in TEMPLATES_DIR.glob("*.scad"))


def template_path(stem: str) -> Path:
    return TEMPLATES_DIR / f"{stem}.scad"


# --- top parameter block parsing --------------------------------------------

_ASSIGN_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?P<value>.+?);\s*"
    r"(?://\s?(?P<inline>.*))?$")
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\.\d+|\d+(?=[eE]))(?:[eE][+-]?\d+)?$")
_STRUCTURAL_RE = re.compile(r"^\s*(?:(?:module|function)\b|use\s*<|include\s*<)")


def _literal(raw: str):
    """Literal value of an assignment RHS, or None when derived/complex."""
    s = raw.strip()
    if _INT_RE.match(s):
        return int(s)
    if _FLOAT_RE.match(s):
        return float(s)
    low = s.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return None  # expression -> derived, stays out of the UI


def _header_docs(text: str) -> dict[str, str]:
    """name -> description lines from the file's leading block comment.

    Covers bead_star's aligned header form:
        width        enclosing-circle diameter of the star face (mm)...
    Continuation lines (deeper indent) are appended to the entry.
    Spurious entries are harmless: lookups are by real param name only.
    """
    m = re.match(r"\A\s*/\*(.*?)\*/", text, re.S)
    if not m:
        return {}
    docs: dict[str, str] = {}
    entry_re = re.compile(r"^ {4}(?P<name>[A-Za-z_]\w*) {2,}(?P<desc>\S.*)$")
    cont_re = re.compile(r"^ {6,}(?P<cont>\S.*)$")
    current: str | None = None
    for line in m.group(1).splitlines():
        em, cm = entry_re.match(line), cont_re.match(line)
        if em:
            current = em.group("name")
            docs[current] = em.group("desc").strip()
        elif cm and current:
            docs[current] += " " + cm.group("cont").strip()
        else:
            current = None
    return docs


def parse_template_params(stem: str) -> list[ScadParam]:
    """Literal-valued params from the template's TOP parameter block.

    Walks from the top: skips the leading block comment, blanks and
    use/include lines; collects `name = value;` assignments (inline
    comments attach directly, immediately-preceding // comment lines are
    the fallback info, then the header block); stops at the first
    structural line (module/function/anything non-assignment) so nothing
    below the block is ever captured. $-variables ($fn...) are skipped.
    """
    path = template_path(stem)
    if not path.is_file():
        raise RenderError(f"missing template: {path}")
    text = path.read_text(encoding="utf-8")
    header = _header_docs(text)

    params: list[ScadParam] = []
    pending_comments: list[str] = []
    seen_names: set[str] = set()
    in_block_comment = False
    for raw in text.splitlines():
        line = raw.strip()
        if in_block_comment:
            if "*/" in line:
                in_block_comment = False
            continue
        if line.startswith("/*"):
            if "*/" not in line:
                in_block_comment = True
            continue
        if not line or line.startswith("//"):
            if line.startswith("//"):
                text = line.lstrip("/").strip()
                # skip decorative dividers/section rules: // ----, // ====
                if text and not re.match(r"^[-=\s]+$", text) \
                        and not re.match(r"^[-=]{3,}", text):
                    pending_comments.append(text)
            continue
        if line.startswith("use <") or line.startswith("include <"):
            continue
        m = _ASSIGN_RE.match(raw)
        if m:
            name = m.group("name")
            if name not in seen_names and not name.startswith("$"):
                value = _literal(m.group("value"))
                if value is not None:
                    info = (m.group("inline") or "").strip()
                    if not info and pending_comments:
                        info = " ".join(pending_comments)
                    if not info:
                        info = header.get(name, "")
                    params.append(ScadParam(name, value, info))
                    seen_names.add(name)
            pending_comments = []
            continue
        break  # first structural line: the top parameter block has ended
    return params


def slider_range(param: ScadParam) -> tuple[float, float] | None:
    """(min, max) 'sensibly derived' from the param's own comment.

    1. 'dial A..B' style range stated in the comment wins.
    2. 'integer >= N' floors the low end.
    3. Fallback: quarter-default..double-default (ints stay integral).
    Returns None when no sensible range exists (caller uses gr.Number).
    """
    value, info = param.value, param.info
    if not isinstance(value, (int, float)):
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*\.\.\s*(\d+(?:\.\d+)?)", info)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (lo, hi) if hi > lo else None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        ge = re.search(r">=\s*(\d+)", info)
        lo = int(ge.group(1)) if ge else max(0, value // 4 if value >= 4 else 0)
        hi = max(2 * value, lo + 12)
        return (float(lo), float(hi)) if hi > lo else None
    lo, hi = round(value / 4, 1), round(value * 2, 1)
    return (lo, hi) if hi > lo else None


# --- -D argument formatting --------------------------------------------------

def format_d_args(overrides: dict) -> list[str]:
    """One '-D key=value' per control; defaults must round-trip cleanly.

    Mirrors forge.d_args_for_params's string quoting: strings become
    key="value", booleans lowercase, numbers bare.
    """
    d: list[str] = []
    for key, value in overrides.items():
        if isinstance(value, bool):
            d += ["-D", f"{key}={'true' if value else 'false'}"]
        elif isinstance(value, str):
            d += ["-D", f'{key}="{value}"']
        else:
            d += ["-D", f"{key}={value}"]
    return d


# --- OpenSCAD CLI runs --------------------------------------------------------

def _run(args: list[str], label: str) -> subprocess.CompletedProcess:
    proc = subprocess.run([OPENSECAD] + args, capture_output=True, text=True)
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-800:]
        raise RenderError(
            f"openscad exited {proc.returncode} ({label}):\n{tail or '(no console output)'}")
    return proc


def render_stl(stem: str, overrides: dict, out_path: Path | None = None) -> Path:
    """Binary STL of a template: --export-format=binstl plus -D overrides."""
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    out = out_path or SCRATCH_DIR / f"{stem}_app.stl"
    _run(["--export-format=binstl", "-o", str(out),
          str(template_path(stem))] + format_d_args(overrides),
         f"{stem} STL")
    if not out.is_file():
        raise RenderError(f"openscad produced no STL at {out}")
    return out


def render_png(source: Path, overrides: dict, out_path: Path,
               camera: str = CAMERA_FACEON, imgsize: str = "640,480",
               label: str = "preview") -> Path:
    """PNG render via the documented pipeline: --imgsize + --camera +
    --autocenter --viewall (CAMERA_FACEON looks straight down z)."""
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    _run(["-o", str(out_path), f"--imgsize={imgsize}", "--autocenter",
          "--viewall", "--camera", camera, str(source)]
         + format_d_args(overrides), label)
    if not out_path.is_file():
        raise RenderError(f"openscad produced no PNG at {out_path}")
    return out_path


# --- binary STL probe (read-only reimplementation of core/stl_probe.py) -------

def probe_binary_stl(path: Path) -> tuple[int, int]:
    """(facet_count, byte_size): count from the 4-byte LE field at offset
    80; size must equal 84 + 50*n (binary STL invariant)."""
    data = path.read_bytes()
    if len(data) < 84 or b"facet normal" in data[:2048]:
        raise RenderError(f"{path}: not a valid binary STL "
                          f"({len(data)} bytes)")
    (n,) = struct.unpack_from("<I", data, 80)
    if len(data) != 84 + 50 * n:
        raise RenderError(f"{path}: size {len(data)} != 84 + 50*{n}")
    return n, len(data)


def probe_line(path: Path) -> str:
    """Human readout: facet count + byte size."""
    n, size = probe_binary_stl(path)
    return (f"facets {n:,} | {size:,} bytes | {path.name}")


def human_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.2f} MB"
    return f"{n / 1024:.1f} KB"
