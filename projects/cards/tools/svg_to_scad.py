#!/usr/bin/env python3
"""Convert the Artemis SVG logo to an OpenSCAD 2D module.

The logo is a traced SVG made of straight line segments only (M/L/Z), so it can
be reproduced exactly as OpenSCAD polygons. Each <path> element becomes one
polygon whose subpaths are passed as ``paths``; OpenSCAD fills nested subpaths
with the even-odd rule, which matches the SVG's ``fill-rule="evenodd"``.

Run from anywhere:

    python3 projects/cards/tools/svg_to_scad.py

Writes ``projects/cards/templates/artemis_logo.scad`` from
``projects/cards/assets/artemis-logo.svg``.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SVG = PROJECT_ROOT / "assets" / "artemis-logo.svg"
DEFAULT_OUT = PROJECT_ROOT / "templates" / "artemis_logo.scad"

NUMBER = r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
TOKEN = re.compile(rf"[MLZmlz]|{NUMBER}")
PATH = re.compile(r'<path\b[^>]*\bd="([^"]+)"', re.DOTALL)
MATRIX = re.compile(r"matrix\(\s*([^)]+)\)")


def parse_matrix(svg: str) -> tuple[float, float, float, float, float, float]:
    """Return the SVG group matrix (a, b, c, d, e, f)."""
    match = MATRIX.search(svg)
    if not match:
        return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    values = [float(v) for v in re.split(r"[\s,]+", match.group(1).strip())]
    if len(values) != 6:
        raise ValueError(f"expected a 6-value matrix, got {values!r}")
    return tuple(values)  # type: ignore[return-value]


def subpaths(d: str) -> list[list[tuple[float, float]]]:
    """Split one SVG path's d attribute into closed line-only subpaths."""
    tokens = TOKEN.findall(d)
    out: list[list[tuple[float, float]]] = []
    current: list[tuple[float, float]] = []
    i = 0
    cmd = None
    cx = cy = 0.0
    start_x = start_y = 0.0

    def flush() -> None:
        nonlocal current
        if len(current) >= 3:
            out.append(current)
        current = []

    while i < len(tokens):
        token = tokens[i]
        if token.isalpha():
            cmd = token
            i += 1
            if cmd in ("Z", "z"):
                if current:
                    current.append((start_x, start_y))
                flush()
                continue
            if cmd in ("M", "m") and i + 1 < len(tokens):
                x = float(tokens[i]); y = float(tokens[i + 1]); i += 2
                if cmd == "m":
                    x += cx; y += cy
                flush()
                cx, cy = x, y
                start_x, start_y = x, y
                current = [(x, y)]
                # Following coordinate pairs are implicit linetos.
                while i + 1 < len(tokens) and not tokens[i].isalpha():
                    x = float(tokens[i]); y = float(tokens[i + 1]); i += 2
                    if cmd == "m":
                        x += cx; y += cy
                    cx, cy = x, y
                    current.append((x, y))
                continue
            if cmd in ("L", "l") and i + 1 < len(tokens):
                x = float(tokens[i]); y = float(tokens[i + 1]); i += 2
                if cmd == "l":
                    x += cx; y += cy
                cx, cy = x, y
                current.append((x, y))
                continue
            raise ValueError(f"unsupported SVG path command {cmd!r}")
        # A coordinate pair without a command: treat as a lineto.
        x = float(tokens[i]); y = float(tokens[i + 1]); i += 2
        cx, cy = x, y
        current.append((x, y))

    flush()
    return out


def transform_points(points, matrix):
    a, b, c, d, e, f = matrix
    return [(a * x + c * y + e, b * x + d * y + f) for x, y in points]


def clean(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Drop consecutive duplicates and a repeated closing point."""
    out: list[tuple[float, float]] = []
    for p in points:
        if not out or abs(p[0] - out[-1][0]) > 1e-9 or abs(p[1] - out[-1][1]) > 1e-9:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9:
        out.pop()
    return out


def fmt(v: float) -> str:
    s = f"{v:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def convert(svg_path: Path, out_path: Path) -> None:
    svg = svg_path.read_text(encoding="utf-8")
    matrix = parse_matrix(svg)
    paths = [subpaths(d) for d in PATH.findall(svg)]
    if not paths:
        raise ValueError(f"no <path> elements found in {svg_path}")

    all_pts: list[tuple[float, float]] = []
    for element in paths:
        for sp in element:
            if len(clean(sp)) >= 3:
                all_pts.extend(transform_points(clean(sp), matrix))
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    bounds = (min(xs), min(ys), max(xs), max(ys))

    lines = [
        "// Generated from assets/artemis-logo.svg by tools/svg_to_scad.py.",
        "// Do not hand-edit; re-run the converter instead.",
        f"// SVG file is 45 x 45 mm; artwork bounds: x {bounds[0]:.6f}..{bounds[2]:.6f},"
        f" y {bounds[1]:.6f}..{bounds[3]:.6f} mm.",
        "// Fill rule: even-odd (matches the SVG).",
        "",
        f"ARTEMIS_LOGO_ARTWORK_W = {fmt(bounds[2] - bounds[0])};",
        f"ARTEMIS_LOGO_ARTWORK_H = {fmt(bounds[3] - bounds[1])};",
        "",
        "module artemis_logo_2d() {",
        "  union() {",
    ]

    for index, element in enumerate(paths):
        points: list[tuple[float, float]] = []
        loops: list[list[int]] = []
        for sp in element:
            sp = clean(transform_points(clean(sp), matrix))
            if len(sp) < 3:
                continue
            base = len(points)
            points.extend(sp)
            loops.append(list(range(base, base + len(sp))))
        if not loops:
            continue
        pts = ", ".join(f"[{fmt(x)},{fmt(y)}]" for x, y in points)
        idx = ", ".join("[" + ",".join(str(v) for v in loop) + "]" for loop in loops)
        lines.append(f"    // SVG path {index + 1}: {len(loops)} loop(s), {len(points)} points")
        lines.append(f"    polygon(points=[{pts}], paths=[{idx}], convexity=10);")

    lines += ["  }", "}", ""]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes, {len(all_pts)} points)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    convert(args.svg, args.out)


if __name__ == "__main__":
    main()
