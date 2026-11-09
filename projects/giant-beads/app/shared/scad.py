"""OpenSCAD CLI helpers for the giant-beads app.

The .scad templates remain the single source of truth.  This module
does the small amount of plumbing around them: find a template, read its
top literal-valued parameter block (for defaults), format -D arguments,
render a binary STL, and probe the result.  No geometry is reimplemented
in Python.

Renders land only in app/.render-scratch/.
"""
from __future__ import annotations

import re
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]        # .../giant-beads/app
PROJECT_DIR = APP_DIR.parent                         # .../giant-beads
TEMPLATES_DIR = PROJECT_DIR / "templates"
SCRATCH_DIR = APP_DIR / ".render-scratch"

OPENSECAD = "openscad"
RENDER_TIMEOUT_SECONDS = 180


class RenderError(RuntimeError):
    """OpenSCAD exited nonzero; .stderr carries the console tail."""


@dataclass(frozen=True)
class ScadParam:
    """One literal-valued parameter promoted to a usable default."""

    name: str
    value: object          # int | float | bool | str
    info: str = ""         # inline / preceding / header comment from the file


# --- template discovery -----------------------------------------------------

def template_path(stem: str) -> Path:
    return TEMPLATES_DIR / f"{stem}.scad"


# --- top parameter block parsing --------------------------------------------

_ASSIGN_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z_$][\w$]*)\s*=\s*(?P<value>.+?);\s*"
    r"(?://\s?(?P<inline>.*))?$")
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?(?:\d+\.\d*|\.\d+|\d+(?=[eE]))(?:[eE][+-]?\d+)?$")


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
    """name -> description lines from the file's leading block comment."""
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
    """Literal-valued params from the template's TOP parameter block."""
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
                comment = line.lstrip("/").strip()
                if comment and not re.match(r"^[-=\s]+$", comment) \
                        and not re.match(r"^[-=]{3,}", comment):
                    pending_comments.append(comment)
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


# --- -D argument formatting --------------------------------------------------

def format_d_args(overrides: dict) -> list[str]:
    """One '-D key=value' per override; defaults must round-trip cleanly."""
    args: list[str] = []
    for key, value in overrides.items():
        if isinstance(value, bool):
            args += ["-D", f"{key}={'true' if value else 'false'}"]
        elif isinstance(value, str):
            args += ["-D", f'{key}="{value}"']
        else:
            args += ["-D", f"{key}={value}"]
    return args


# --- OpenSCAD CLI runs --------------------------------------------------------

def _run(args: list[str], label: str) -> subprocess.CompletedProcess:
    try:
        proc = subprocess.run(
            [OPENSECAD] + args,
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise RenderError(
            f"openscad timed out after {RENDER_TIMEOUT_SECONDS} s "
            f"({label})"
        ) from exc
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-1200:]
        raise RenderError(
            f"openscad exited {proc.returncode} ({label}):\n"
            f"{tail or '(no console output)'}")
    return proc


def render_stl(stem: str, overrides: dict, out_path: Path | None = None) -> Path:
    """Binary STL of a template: --export-format=binstl plus -D overrides."""
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    out = out_path or SCRATCH_DIR / f"{stem}.stl"
    _run(
        ["--export-format=binstl", "-o", str(out),
         str(template_path(stem))] + format_d_args(overrides),
        f"{stem} STL",
    )
    if not out.is_file():
        raise RenderError(f"openscad produced no STL at {out}")
    return out


# --- binary STL probe ---------------------------------------------------------

def probe_binary_stl(path: Path) -> tuple[int, int]:
    """(facet_count, byte_size) from the binary STL header and size."""
    data = path.read_bytes()
    if len(data) < 84 or b"facet normal" in data[:2048]:
        raise RenderError(
            f"{path}: not a valid binary STL ({len(data)} bytes)")
    (n,) = struct.unpack_from("<I", data, 80)
    if n <= 0:
        raise RenderError(f"{path}: facet count at offset 80 is {n}")
    if len(data) != 84 + 50 * n:
        raise RenderError(f"{path}: size {len(data)} != 84 + 50*{n}")
    return n, len(data)


def probe_line(path: Path) -> str:
    """Human readout: facet count + byte size."""
    n, size = probe_binary_stl(path)
    return f"facets {n:,} | {size:,} bytes | {path.name}"


def human_bytes(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.2f} MB"
    return f"{n / 1024:.1f} KB"
