#!/usr/bin/env python3
"""forge.py: headless parametric STL pipeline around the OpenSCAD CLI.

Reads templates/box.scad + presets.json (default: the file beside this
script, under utilities/; override with --presets PATH) relative to this
script, renders one STL plus preview PNGs per preset, validates outputs,
prints a table. For multi-part presets (e.g. beads with parts
["body","letter"]) it also emits a Bambu-native project .3mf: one object,
two parts, each part pre-assigned to an extruder via
Metadata/model_settings.config (<metadata key="extruder" .../> INSIDE each
<part>). No colour painting. Templates may also live inside
projects/<name>/templates/ under the repo root - a preset's "template" key
is resolved against the utilities templates/ dir first, then every
project's templates/ dir.
Stdlib only. All OpenSCAD invocations use subprocess list args (no shell).
"""
import argparse
import base64
import json
import struct
import subprocess
import sys
import tempfile
import uuid
import zipfile
import zlib
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as _xml_escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
TEMPLATES_DIR = HERE / "templates"
DEFAULT_TEMPLATE_NAME = "box.scad"
TEMPLATE = TEMPLATES_DIR / DEFAULT_TEMPLATE_NAME
PRESETS_FILE = HERE / "presets.json"
PROJECTS_DIR = REPO_ROOT / "projects"
TEMPLATES_FALLBACK_DIRS = sorted(
    (p / "templates") for p in PROJECTS_DIR.iterdir() if p.is_dir()
    and (p / "templates").is_dir()
) if PROJECTS_DIR.is_dir() else []
PROJECTS_PRESETS_FILES = sorted(
    (p / "presets.json") for p in PROJECTS_DIR.iterdir() if p.is_dir()
    and (p / "presets.json").is_file()
) if PROJECTS_DIR.is_dir() else []


def resolve_template(name: str) -> Path:
    """Resolve a preset's "template" filename under the root templates/ dir,
    then under each project's templates/ dir (projects own their families)."""
    candidate = TEMPLATES_DIR / name
    if candidate.is_file():
        return candidate
    for d in TEMPLATES_FALLBACK_DIRS:
        candidate = d / name
        if candidate.is_file():
            return candidate
    return TEMPLATES_DIR / name


def find_word_base_preset(name: str, loaded):
    """Return a (preset_params, presets_file) pair for the word-mode base
    preset: first from the given loaded dict, then from project presets."""
    if name in loaded:
        return loaded[name], None
    for presets_file in PROJECTS_PRESETS_FILES:
        try:
            with open(presets_file, "r", encoding="utf-8") as f:
                presets = json.load(f).get("presets", {})
        except (OSError, json.JSONDecodeError):
            continue
        if name in presets:
            return presets[name], presets_file
    return None, None

# Gimbal camera presets: "tx,ty,tz,rx,ry,rz,dist"
CAMERAS = {
    "iso": "0,0,0,55,0,45,350",
    "front": "0,0,0,90,0,0,350",
    "top": "0,0,0,0,0,0,350",
    "bottom": "0,0,0,180,0,0,350",
    "hole": "0,0,0,0,90,0,350",
}

STL_MIN_BYTES = 1024       # 1 KB
PNG_MIN_BYTES = 5 * 1024   # 5 KB
THREEMF_MIN_BYTES = 10240  # 10 KB

# --- Bambu-native .3mf support -------------------------------------------
# Layout mirrors the verified reference frog_tape_dispenser_256.3mf:
# [Content_Types].xml, _rels/.rels, 3D/3dmodel.model (one assembly object
# with two components), 3D/_rels/3dmodel.model.rels,
# 3D/Objects/object_1.model (part 1 mesh), 3D/Objects/object_2.model
# (part 2 mesh), Metadata/model_settings.config (ONE <object> with TWO
# <part> entries, extruder metadata INSIDE each part),
# Metadata/project_settings.config (slicer profile base).
# Plate thumbnails, cut_information and slice_info are intentionally
# omitted (they are not needed to load the model).
THREEMF_TOP_OBJECT_ID = 3   # assembly object id (mirrors frog's object 3:
THREEMF_PART_IDS = (1, 2)   # inner ids 1,2 referenced as parts 1,2)
THREEMF_REQUIRED_ENTRIES = (
    "[Content_Types].xml",
    "_rels/.rels",
    "3D/3dmodel.model",
    "3D/_rels/3dmodel.model.rels",
    "3D/Objects/object_1.model",
    "3D/Objects/object_2.model",
    "Metadata/model_settings.config",
    "Metadata/project_settings.config",
)
THREEMF_CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
THREEMF_PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
THREEMF_BAMBU_NS = "http://schemas.bambulab.com/package/2021"
THREEMF_IDENTITY = "1 0 0 0 1 0 0 0 1 0 0 0"
THREEMF_PART_MATRIX = "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"

THREEMF_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
    ' <Default Extension="rels"'
    ' ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
    ' <Default Extension="model"'
    ' ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
    ' <Default Extension="png" ContentType="image/png"/>\n'
    ' <Default Extension="gcode" ContentType="text/x.gcode"/>\n'
    '</Types>'
)

THREEMF_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships'
    ' xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
    ' <Relationship Target="/3D/3dmodel.model" Id="rel-1"'
    ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
    '</Relationships>'
)

THREEMF_MODEL_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships'
    ' xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
    ' <Relationship Target="/3D/Objects/object_1.model" Id="rel-1"'
    ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
    ' <Relationship Target="/3D/Objects/object_2.model" Id="rel-2"'
    ' Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
    '</Relationships>'
)

# NOTE: printer selection is the user's to set in Bambu Studio; the slicer
# profile below is only a base copied from the frog_tape_dispenser_256.3mf
# reference (Metadata/project_settings.config, zlib-compressed + base64).
# No keys were invented: the bytes decode to the reference file verbatim.
THREEMF_PROJECT_SETTINGS_BLOB = (
    "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"
)

_PROJECT_SETTINGS_CACHE = None


def project_settings_bytes() -> bytes:
    """Slicer-profile base: the frog reference project_settings, verbatim."""
    global _PROJECT_SETTINGS_CACHE
    if _PROJECT_SETTINGS_CACHE is None:
        _PROJECT_SETTINGS_CACHE = zlib.decompress(
            base64.b64decode(THREEMF_PROJECT_SETTINGS_BLOB)
        )
    return _PROJECT_SETTINGS_CACHE


def parse_stl_mesh(stl_path: Path):
    """Parse an STL into (vertices, triangles, facet_count).

    ASCII (``facet`` in the first 2KB) is parsed from ``vertex`` lines;
    otherwise binary (84-byte header + uint32 count + 50B/tri) is parsed
    with struct. Units are mm as-is; no transforms. Vertices are
    de-duplicated; every 3 vertices form one triangle.
    """
    data = stl_path.read_bytes()
    if b"facet" in data[:2048]:
        vmap: dict = {}
        verts = []
        tris = []
        cur = []
        n_facets = 0
        for line in data.split(b"\n"):
            p = line.split()
            if not p:
                continue
            if p[0] == b"vertex":
                x, y, z = float(p[1]), float(p[2]), float(p[3])
                key = (x, y, z)
                idx = vmap.get(key)
                if idx is None:
                    idx = len(verts)
                    vmap[key] = idx
                    verts.append(key)
                cur.append(idx)
                if len(cur) == 3:
                    tris.append((cur[0], cur[1], cur[2]))
                    cur = []
            elif p[0] == b"facet":
                n_facets += 1
        if cur:
            raise ValueError(f"{stl_path}: truncated ASCII STL")
        return verts, tris, n_facets
    if len(data) < 84:
        raise ValueError(f"{stl_path}: too small for a binary STL")
    (n,) = struct.unpack_from("<I", data, 80)
    if len(data) < 84 + 50 * n:
        raise ValueError(f"{stl_path}: truncated binary STL")
    rec = struct.Struct("<12fH")
    vmap = {}
    verts = []
    tris = []
    off = 84
    for _ in range(n):
        v = rec.unpack_from(data, off)
        off += 50
        tri = []
        for k in (3, 6, 9):
            key = (v[k], v[k + 1], v[k + 2])
            idx = vmap.get(key)
            if idx is None:
                idx = len(verts)
                vmap[key] = idx
                verts.append(key)
            tri.append(idx)
        tris.append((tri[0], tri[1], tri[2]))
    return verts, tris, n


def _object_model_xml(obj_id: int, obj_uuid: str, verts, tris) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<model unit="millimeter" xml:lang="en-US"'
        f' xmlns="{THREEMF_CORE_NS}"'
        f' xmlns:BambuStudio="{THREEMF_BAMBU_NS}"'
        f' xmlns:p="{THREEMF_PROD_NS}" requiredextensions="p">\n',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n',
        ' <resources>\n',
        f'  <object id="{obj_id}" p:UUID="{obj_uuid}" type="model">\n',
        '   <mesh>\n    <vertices>\n',
    ]
    for (x, y, z) in verts:
        out.append(f'     <vertex x="{x!r}" y="{y!r}" z="{z!r}"/>\n')
    out.append('    </vertices>\n    <triangles>\n')
    for (a, b, c) in tris:
        out.append(f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>\n')
    out.append(
        '    </triangles>\n   </mesh>\n  </object>\n </resources>\n <build/>\n</model>\n'
    )
    return "".join(out)


def _root_model_xml(name: str, top_uuid: str, comp_uuids, build_uuid: str) -> str:
    c1, c2 = comp_uuids
    pid1, pid2 = THREEMF_PART_IDS
    title = _xml_escape(f"{name} two-color bead")
    desc = _xml_escape(
        f"{name}: one object, two parts ({name}_body on extruder 1, "
        f"{name}_letter on extruder 2). Assign real filaments per part; "
        "nothing is painted."
    )
    tid = THREEMF_TOP_OBJECT_ID
    return (
        "<?xml version='1.0' encoding='UTF-8'?>\n"
        f'<model xmlns="{THREEMF_CORE_NS}" xmlns:p="{THREEMF_PROD_NS}"'
        ' unit="millimeter" xml:lang="en-US" requiredextensions="p"'
        f' xmlns:BambuStudio="{THREEMF_BAMBU_NS}">\n'
        ' <metadata name="Application">stl-forge</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        f' <metadata name="Title">{title}</metadata>\n'
        f' <metadata name="Description">{desc}</metadata>\n'
        ' <resources>\n'
        f'  <object id="{tid}" p:UUID="{top_uuid}" type="model">\n'
        '   <components>\n'
        f'    <component p:path="/3D/Objects/object_1.model" objectid="{pid1}"'
        f' p:UUID="{c1}" transform="{THREEMF_IDENTITY}" />\n'
        f'    <component p:path="/3D/Objects/object_2.model" objectid="{pid2}"'
        f' p:UUID="{c2}" transform="{THREEMF_IDENTITY}" />\n'
        '   </components>\n'
        '  </object>\n'
        ' </resources>\n'
        f' <build p:UUID="{build_uuid}">\n'
        f'  <item objectid="{tid}" p:UUID="{build_uuid}"'
        f' transform="{THREEMF_IDENTITY}" printable="1" />\n'
        ' </build>\n'
        '</model>'
    )


def _model_settings_xml(name: str, n_body: int, n_letter: int) -> str:
    tid = THREEMF_TOP_OBJECT_ID
    pid1, pid2 = THREEMF_PART_IDS
    body_name = _xml_escape(f"{name}_body")
    letter_name = _xml_escape(f"{name}_letter")
    total = n_body + n_letter
    mesh_stat = (
        lambda n: f'<mesh_stat face_count="{n}" edges_fixed="0"'
        ' degenerate_facets="0" facets_removed="0" facets_reversed="0"'
        ' backwards_edges="0"/>'
    )
    part = (
        lambda pid, pname, src_obj, src_vol, n, extr: (
            f'    <part id="{pid}" subtype="normal_part">\n'
            f'      <metadata key="name" value="{pname}"/>\n'
            f'      <metadata key="matrix" value="{THREEMF_PART_MATRIX}"/>\n'
            f'      <metadata key="source_object_id" value="{src_obj}"/>\n'
            f'      <metadata key="source_volume_id" value="{src_vol}"/>\n'
            '      <metadata key="source_offset_x" value="0"/>\n'
            '      <metadata key="source_offset_y" value="0"/>\n'
            '      <metadata key="source_offset_z" value="0"/>\n'
            f'      <metadata key="extruder" value="{extr}"/>\n'
            f'      {mesh_stat(n)}\n'
            '    </part>\n'
        )
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<config>\n'
        f'  <object id="{tid}">\n'
        f'    <metadata key="name" value="{_xml_escape(name)}"/>\n'
        '    <metadata key="extruder" value="1"/>\n'
        f'    <metadata face_count="{total}"/>\n'
        f'{part(pid1, body_name, 0, 0, n_body, 1)}'
        f'{part(pid2, letter_name, 1, 0, n_letter, 2)}'
        '  </object>\n'
        '  <plate>\n'
        '    <metadata key="plater_id" value="1"/>\n'
        '    <metadata key="plater_name" value=""/>\n'
        '    <metadata key="locked" value="false"/>\n'
        '    <metadata key="filament_map_mode" value="Auto For Flush"/>\n'
        '    <model_instance>\n'
        f'      <metadata key="object_id" value="{tid}"/>\n'
        '      <metadata key="instance_id" value="0"/>\n'
        '      <metadata key="identify_id" value="1"/>\n'
        '    </model_instance>\n'
        '  </plate>\n'
        '  <assemble>\n'
        f'   <assemble_item object_id="{tid}" instance_id="0"'
        f' transform="{THREEMF_IDENTITY}" offset="0 0 0" />\n'
        '  </assemble>\n'
        '</config>\n'
    )


def build_bead_3mf(name: str, body_stl: Path, letter_stl: Path,
                   out_path: Path):
    """Render the Bambu-native .3mf for one bead preset.

    Returns (body_facets, letter_facets). Raises on any problem.
    """
    for label, p in (("body", body_stl), ("letter", letter_stl)):
        if not p.is_file():
            raise FileNotFoundError(f"missing {label} STL {p}")
    body_verts, body_tris, body_facets = parse_stl_mesh(body_stl)
    letter_verts, letter_tris, letter_facets = parse_stl_mesh(letter_stl)
    if body_facets <= 0 or not body_tris:
        raise ValueError(f"{name}: body mesh has no facets")
    if letter_facets <= 0 or not letter_tris:
        raise ValueError(f"{name}: letter mesh has no facets")
    if len(body_tris) != body_facets or len(letter_tris) != letter_facets:
        raise ValueError(f"{name}: parsed triangle/facet mismatch")
    pid1, pid2 = THREEMF_PART_IDS
    obj1 = _object_model_xml(pid1, str(uuid.uuid4()), body_verts, body_tris)
    obj2 = _object_model_xml(pid2, str(uuid.uuid4()), letter_verts, letter_tris)
    root = _root_model_xml(
        name, str(uuid.uuid4()),
        (str(uuid.uuid4()), str(uuid.uuid4())), str(uuid.uuid4()))
    settings = _model_settings_xml(name, body_facets, letter_facets)
    del body_verts, body_tris, letter_verts, letter_tris
    with zipfile.ZipFile(out_path, "w",
                          compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", THREEMF_CONTENT_TYPES)
        z.writestr("_rels/.rels", THREEMF_ROOT_RELS)
        z.writestr("3D/3dmodel.model", root)
        z.writestr("3D/_rels/3dmodel.model.rels", THREEMF_MODEL_RELS)
        z.writestr("3D/Objects/object_1.model", obj1)
        z.writestr("3D/Objects/object_2.model", obj2)
        z.writestr("Metadata/model_settings.config", settings)
        z.writestr("Metadata/project_settings.config",
                   project_settings_bytes())
    return body_facets, letter_facets


def validate_bead_3mf(mf_path: Path, body_facets: int,
                      letter_facets: int):
    """Validate a bead .3mf. Returns a list of failure strings (empty = ok)."""
    problems = []
    try:
        z = zipfile.ZipFile(mf_path)
    except Exception as e:  # noqa: BLE001
        return [f"zip open failed: {e}"]
    with z:
        names = set(z.namelist())
        for entry in THREEMF_REQUIRED_ENTRIES:
            if entry not in names:
                problems.append(f"missing entry {entry}")
        try:
            root_raw = z.read("3D/3dmodel.model")
        except KeyError:
            root_raw = None
        try:
            settings_raw = z.read("Metadata/model_settings.config")
        except KeyError:
            settings_raw = None
        if root_raw is not None:
            try:
                ET.fromstring(root_raw)
            except ET.ParseError as e:
                problems.append(f"3D/3dmodel.model XML parse failed: {e}")
        if settings_raw is not None:
            try:
                cfg = ET.fromstring(settings_raw)
            except ET.ParseError as e:
                problems.append(
                    f"Metadata/model_settings.config XML parse failed: {e}")
                cfg = None
            if cfg is not None:
                parts = cfg.findall(".//part")
                if len(parts) != 2:
                    problems.append(
                        f"model_settings has {len(parts)} <part> entries,"
                        " expected 2")
                else:
                    got = []
                    for part in parts:
                        ext = None
                        for md in part.findall("metadata"):
                            if md.get("key") == "extruder":
                                ext = md.get("value")
                        got.append(ext)
                    if sorted(got) != ["1", "2"]:
                        problems.append(
                            "part extruder values are"
                            f" {got}, expected 1 and 2 INSIDE the parts")
        for obj_file, want in (("3D/Objects/object_1.model", body_facets),
                               ("3D/Objects/object_2.model", letter_facets)):
            try:
                raw = z.read(obj_file)
            except KeyError:
                continue  # already reported above
            try:
                om = ET.fromstring(raw)
            except ET.ParseError as e:
                problems.append(f"{obj_file} XML parse failed: {e}")
                continue
            n_tri = sum(1 for _ in om.iter(
                f"{{{THREEMF_CORE_NS}}}triangle"))
            if n_tri != want:
                problems.append(
                    f"{obj_file} has {n_tri} triangles, source STL has"
                    f" {want} facets")
    try:
        size = mf_path.stat().st_size
    except OSError as e:
        return problems + [f"stat failed: {e}"]
    if size <= THREEMF_MIN_BYTES:
        problems.append(f".3mf too small ({size} bytes <= 10KB)")
    return problems



def d_args_for_params(params, overrides=None):
    """Build openscad -D args from a preset dict plus overrides.

    Same source排除 rule as the suite: keys template/parts/preview never
    become -D flags. Used by both the preset suite and --word mode so the
    per-letter beads render exactly as bead_default would.
    """
    merged = dict(params)
    if overrides:
        merged.update(overrides)
    d = []
    for key, value in merged.items():
        if key in ("template", "parts", "preview"):
            continue
        if isinstance(value, str):
            d += ["-D", f'{key}="{value}"']
        else:
            d += ["-D", f"{key}={value}"]
    return d


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Render parametric box STLs + previews.")
    p.add_argument("--presets", default=None,
                   help="Path to a presets JSON file"
                        " (default: utilities/presets.json)")
    p.add_argument("--only", default=None,
                   help="Comma-separated subset of preset names, e.g. 'a,b'")
    p.add_argument("--out", default="./out",
                   help="Output directory (default ./out)")
    p.add_argument("--word", default=None,
                   help="Render unique letters of WORD as one row-layout STL")
    p.add_argument("--word-gap", type=float, default=10.0,
                   help="Clear gap in mm between neighbouring bead bounding"
                   " boxes in --word mode (default 10.0)")
    ns = p.parse_args(argv)
    if ns.word is not None and ns.only is not None:
        p.error("--only cannot be used with --word")
    if ns.word is not None:
        norm = "".join(c for c in ns.word.upper() if "A" <= c <= "Z")
        if not norm:
            p.error("--word: no renderable letters")
    return ns


def count_facets(stl_path: Path) -> int:
    """Count facets: ASCII 'facet normal' lines, else binary STL header count."""
    data = stl_path.read_bytes()
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = None
    if text is not None and "facet normal" in text:
        return sum(1 for line in text.splitlines()
                   if line.lstrip().startswith("facet normal"))
    # Binary STL: 80-byte header + uint32 LE facet count at offset 80.
    if len(data) >= 84:
        (n,) = struct.unpack_from("<I", data, 80)
        # Sanity: expected size = 84 + 50*n. If it matches (roughly), trust it.
        if n > 0 and len(data) >= 84 + 50 * n - 50:
            return int(n)
    # Fallback: raw byte occurrence count.
    return data.count(b"facet normal")


def run_openscad(args, label: str):
    """Run openscad with list args, capturing output. Returns CompletedProcess."""
    proc = subprocess.run(
        ["openscad"] + args,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"[FAIL] {label}: openscad exited {proc.returncode}", file=sys.stderr)
        print(f"  cmd: openscad {' '.join(args)}", file=sys.stderr)
        if proc.stdout:
            print(f"  --- stdout ---\n{proc.stdout}", file=sys.stderr)
        if proc.stderr:
            print(f"  --- stderr ---\n{proc.stderr}", file=sys.stderr)
    return proc


def _word_normalise(raw: str) -> str:
    return "".join(c for c in raw.upper() if "A" <= c <= "Z")


def _word_dedupe(norm: str):
    seen = set()
    out = []
    for c in norm:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _binary_stl_stats(path: Path):
    """Return (facets, xmin, xmax, zmin, zmax) from a binary STL vertex stream."""
    data = path.read_bytes()
    if len(data) < 84:
        raise ValueError(f"{path}: too small for a binary STL")
    (n,) = struct.unpack_from("<I", data, 80)
    if len(data) < 84 + 50 * n:
        raise ValueError(f"{path}: truncated binary STL")
    xmin = xmax = zmin = zmax = None
    for j in range(n):
        off = 84 + j * 50
        # 12 floats at the front; vertex x at 3/6/9, vertex z at 5/8/11.
        v = struct.unpack_from("<12f", data, off)
        for k, zm in ((3, 5), (6, 8), (9, 11)):
            x = v[k]
            z = v[zm]
            if xmin is None:
                xmin = xmax = x
                zmin = zmax = z
            else:
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
                if z < zmin:
                    zmin = z
                if z > zmax:
                    zmax = z
    return n, xmin, xmax, zmin, zmax


def run_word_mode(ns, all_presets, out_dir: Path, preview_dir: Path) -> int:
    word = _word_normalise(ns.word)
    # parse_args already rejected the empty case; re-check defensively.
    if not word:
        print("forge.py: error: --word: no renderable letters",
              file=sys.stderr)
        return 2
    letters = _word_dedupe(word)
    n = len(letters)
    word_gap = float(ns.word_gap)

    base_params, base_presets_file = find_word_base_preset(
        "bead_default", all_presets)
    if base_params is None:
        print("word mode: missing bead_default preset", file=sys.stderr)
        return 1
    template_name = base_params.get("template", DEFAULT_TEMPLATE_NAME)
    template_path = resolve_template(template_name)
    if not template_path.is_file():
        print(f"word mode: missing template {template_path}",
              file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    merged_path = out_dir / f"beads_{word}.stl"

    # 1. Render one assembly bead per unique letter (bead_default + overrides).
    with tempfile.TemporaryDirectory(prefix="forge-word-") as tmp:
        tmpdir = Path(tmp)
        src_paths = []
        src_facets = []
        for letter in letters:
            src = tmpdir / f"bead_{letter}.stl"
            d = d_args_for_params(base_params, {
                "part": "assembly",
                "letter_top": letter,
                "letter_bottom": letter,
            })
            proc = run_openscad(
                ["--export-format=binstl",
                 "-o", str(src), str(template_path)] + d,
                f"word:{letter} stl",
            )
            if proc.returncode != 0:
                print(f"word mode: STL render failed for letter {letter}",
                      file=sys.stderr)
                return 1
            if not src.is_file():
                print(f"word mode: missing STL {src}", file=sys.stderr)
                return 1
            if src.stat().st_size <= STL_MIN_BYTES:
                print(f"word mode: STL too small for letter {letter}",
                      file=sys.stderr)
                return 1
            try:
                facets = count_facets(src)
            except Exception as e:  # noqa: BLE001
                print(f"word mode: facet count failed for {letter}: {e}",
                      file=sys.stderr)
                return 1
            if facets <= 0:
                print(f"word mode: facet count is {facets} for {letter}",
                      file=sys.stderr)
                return 1
            src_paths.append(src)
            src_facets.append(facets)

        # 2. Layout: row along +X centred on x=0.
        centres = []
        spans = []
        for src in src_paths:
            _, xmin, xmax, _, _ = _binary_stl_stats(src)
            centres.append((xmin + xmax) / 2.0)
            spans.append(xmax - xmin)
        bead_width = max(spans)
        pitch = bead_width + word_gap
        dxs = [i * pitch - (n - 1) * pitch / 2.0 - centres[i]
               for i in range(n)]

        # 3. Merge by direct binary concatenation with x-offset only.
        total = int(sum(src_facets))
        header = b"forge word merge"
        header = header + b"\0" * (80 - len(header))
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

    # 4. In-code assertions from the binaries at runtime (never hardcoded).
    try:
        mdata = merged_path.read_bytes()
        (merged_n,) = struct.unpack_from("<I", mdata, 80)
        msize = len(mdata)
        mn, mxmin, mxmax, mzmin, _ = _binary_stl_stats(merged_path)
    except Exception as e:  # noqa: BLE001
        print(f"word mode: merged read failed: {e}", file=sys.stderr)
        return 1
    src_sum = int(sum(src_facets))
    ok = True

    def _assert(cond, msg):
        nonlocal ok
        print(f"[word] assert {msg} {'ok' if cond else 'FAIL'}")
        if not cond:
            print(f"word mode: assertion failed: {msg}", file=sys.stderr)
            ok = False

    _assert(merged_n == src_sum,
            f"merged facets {merged_n} == sum(source facets) {src_sum}")
    _assert(mn == src_sum,
            f"reparsed merged facets {mn} == sum(source facets) {src_sum}")
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
    if not ok:
        return 1

    # 5. Previews: one wide scene of the merged row via a temp import scad.
    import_line = 'import("%s");\n' % str(
        merged_path.resolve()).replace("\\", "/").replace('"', '\\"')
    with tempfile.TemporaryDirectory(prefix="forge-word-prev-") as tmp:
        scad_path = Path(tmp) / f"beads_{word}.scad"
        scad_path.write_text(import_line, encoding="utf-8")
        for view in ("iso", "front"):
            png = preview_dir / f"beads_{word}_{view}.png"
            proc = run_openscad(
                ["-o", str(png),
                 "--imgsize=640,480",
                 "--autocenter", "--viewall",
                 "--camera", CAMERAS[view],
                 str(scad_path)],
                f"word preview {view}",
            )
            if proc.returncode != 0:
                print(f"word mode: preview {view} render failed",
                      file=sys.stderr)
                return 1
            if not png.is_file():
                print(f"word mode: missing preview {png}", file=sys.stderr)
                return 1
            if png.stat().st_size <= PNG_MIN_BYTES:
                print(f"word mode: preview {view} too small"
                      f" ({png.stat().st_size} bytes <= 5KB)",
                      file=sys.stderr)
                return 1

    # 6. Summary line.
    print(f"WORD {word} letters {' '.join(letters)} -> {merged_path}"
          f" facets {merged_n} bytes {msize}")
    return 0


def main(argv=None) -> int:
    ns = parse_args(argv)

    if not TEMPLATE.is_file():
        print(f"Missing template: {TEMPLATE}", file=sys.stderr)
        return 1
    presets_path = Path(ns.presets) if ns.presets else PRESETS_FILE
    if not presets_path.is_file():
        print(f"Missing presets file: {presets_path}", file=sys.stderr)
        return 1

    with open(presets_path, "r", encoding="utf-8") as f:
        all_presets = json.load(f).get("presets", {})

    if ns.word is not None:
        out_dir = Path(ns.out)
        preview_dir = out_dir / "previews"
        return run_word_mode(ns, all_presets, out_dir, preview_dir)

    if ns.only:
        wanted = [s.strip() for s in ns.only.split(",") if s.strip()]
        missing = [w for w in wanted if w not in all_presets]
        if missing:
            print(f"Unknown preset(s) in --only: {', '.join(missing)}", file=sys.stderr)
            print(f"Available: {', '.join(sorted(all_presets))}", file=sys.stderr)
            return 1
        names = wanted
    else:
        names = sorted(all_presets.keys())

    out_dir = Path(ns.out)
    preview_dir = out_dir / "previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    failures = []
    rows = []

    for name in names:
        params = all_presets[name]
        # Per-preset template selection: optional "template" key (filename
        # only, resolved relative to templates/). Default: "box.scad".
        template_name = params.get("template", DEFAULT_TEMPLATE_NAME)
        template_path = resolve_template(template_name)
        parts = params.get("parts")
        preview_part = params.get("preview")
        # Expected STL labels for this preset (used even on early failure).
        # Multi-part presets also export the combined `<name>.stl`
        # (part label `assembly`) in addition to one `<name>_<part>.stl`
        # per entry in `parts`. Single-part presets export one `<name>.stl`.
        expected_targets = []
        if parts:
            expected_targets.append(("assembly", out_dir / f"{name}.stl"))
            for p in parts:
                expected_targets.append((p, out_dir / f"{name}_{p}.stl"))
        else:
            expected_targets.append((None, out_dir / f"{name}.stl"))
        if not template_path.is_file():
            for part_label, stl_file in expected_targets:
                label = f"{name}:{part_label}" if part_label else name
                failures.append(f"{label}: missing template {template_path}")
                rows.append({
                    "preset": label,
                    "stl": str(stl_file),
                    "bytes": 0,
                    "facets": 0,
                    "previews": "",
                    "ok": False,
                })
            continue
        base_d_args = d_args_for_params(params)

        preview_d_args = base_d_args + (
            ["-D", f'part="{preview_part}"'] if preview_part else []
        )

        stl_targets = []
        if parts:
            # Combined bead file first, then one per split part.
            stl_targets.append((
                "assembly",
                out_dir / f"{name}.stl",
                base_d_args + ["-D", 'part="assembly"'],
            ))
            for part_label in parts:
                stl_path = out_dir / f"{name}_{part_label}.stl"
                d = base_d_args + ["-D", f'part="{part_label}"']
                stl_targets.append((part_label, stl_path, d))
        else:
            stl_path = out_dir / f"{name}.stl"
            stl_targets.append((None, stl_path, base_d_args))

        # 1. Render STLs (one per part, or one for single-part presets).
        stl_procs_ok = {}
        for part_label, stl_path, d in stl_targets:
            label = f"{name}:{part_label}" if part_label else name
            stl_proc = run_openscad(
                ["--export-format=binstl",
                 "-o", str(stl_path), str(template_path)] + d,
                f"{label} stl",
            )
            if stl_proc.returncode != 0:
                failures.append(f"{label}: STL render failed")
                stl_procs_ok[label] = False
            else:
                stl_procs_ok[label] = True

        # 2. Render preview PNGs once per preset.
        png_paths = {}
        previews_ok = True
        for view, cam in CAMERAS.items():
            png = preview_dir / f"{name}_{view}.png"
            png_paths[view] = png
            proc = run_openscad(
                ["-o", str(png),
                 "--imgsize=640,480",
                 "--autocenter", "--viewall",
                 "--camera", cam,
                 str(template_path)] + preview_d_args,
                f"{name} preview {view}",
            )
            if proc.returncode != 0:
                failures.append(f"{name}: preview {view} render failed")
                previews_ok = False

        for view, png in png_paths.items():
            if not png.is_file():
                failures.append(f"{name}: missing preview {png}")
                previews_ok = False
            elif png.stat().st_size <= PNG_MIN_BYTES:
                failures.append(
                    f"{name}: preview {view} too small "
                    f"({png.stat().st_size} bytes <= 5KB)")
                previews_ok = False

        previews_str = ", ".join(str(png_paths[v]) for v in CAMERAS)

        # 3. Validate each STL.
        for part_label, stl_path, d in stl_targets:
            label = f"{name}:{part_label}" if part_label else name
            stl_bytes = 0
            facets = 0
            stl_ok = stl_procs_ok.get(label, False)
            if not stl_path.is_file():
                failures.append(f"{label}: missing STL {stl_path}")
                stl_ok = False
            else:
                stl_bytes = stl_path.stat().st_size
                if stl_bytes <= STL_MIN_BYTES:
                    failures.append(
                        f"{label}: STL too small ({stl_bytes} bytes <= 1KB)")
                    stl_ok = False
                else:
                    try:
                        facets = count_facets(stl_path)
                    except Exception as e:  # noqa: BLE001
                        failures.append(f"{label}: facet count failed: {e}")
                        stl_ok = False
                    if facets <= 0:
                        failures.append(f"{label}: facet count is {facets}")
                        stl_ok = False
            row_ok = bool(stl_ok and previews_ok)
            rows.append({
                "preset": label,
                "stl": str(stl_path),
                "bytes": stl_bytes,
                "facets": facets,
                "previews": previews_str,
                "ok": row_ok,
            })

        # 3b. Bambu-native .3mf for multi-part presets (one object, two
        # parts, extruder 1/2 pre-assigned inside the parts; no painting).
        if parts:
            mf_path = out_dir / f"{name}.3mf"
            mf_bytes = 0
            mf_facets = 0
            mf_ok = True
            if len(parts) != 2:
                failures.append(
                    f"{name}:3mf: expected 2 parts, found {len(parts)}")
                mf_ok = False
            else:
                body_stl = out_dir / f"{name}_{parts[0]}.stl"
                letter_stl = out_dir / f"{name}_{parts[1]}.stl"
                try:
                    n_body, n_letter = build_bead_3mf(
                        name, body_stl, letter_stl, mf_path)
                    mf_problems = validate_bead_3mf(
                        mf_path, n_body, n_letter)
                    if mf_problems:
                        mf_ok = False
                        for note in mf_problems:
                            failures.append(f"{name}:3mf: {note}")
                    else:
                        mf_facets = n_body + n_letter
                except Exception as e:  # noqa: BLE001
                    failures.append(f"{name}:3mf: build failed: {e}")
                    mf_ok = False
            if mf_path.is_file() and mf_ok:
                mf_bytes = mf_path.stat().st_size
            row_ok = bool(mf_ok and previews_ok)
            if not previews_ok:
                failures.append(f"{name}:3mf: previews failed")
            rows.append({
                "preset": f"{name}:3mf",
                "stl": str(mf_path),
                "bytes": mf_bytes,
                "facets": mf_facets,
                "previews": previews_str,
                "ok": row_ok,
            })

    # 4. Summary table: one row per rendered STL (preset+part).
    print(f"{'preset':<22} {'stl path':<32} {'bytes':>9} {'facets':>8}  preview paths")
    print("-" * 140)
    for r in rows:
        print(f"{r['preset']:<22} {r['stl']:<32} {r['bytes']:>9} "
              f"{r['facets']:>8}  {r['previews']}")

    if failures:
        print("\nFAILURES:", file=sys.stderr)
        for msg in failures:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    n_3mf = sum(1 for r in rows if r["preset"].endswith(":3mf"))
    n_stl = len(rows) - n_3mf
    print(f"\nOK: {n_stl} STL(s) + {n_3mf} 3MF(s) from {len(names)} preset(s)"
          f" rendered to {out_dir}/ (previews in {preview_dir}/)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
