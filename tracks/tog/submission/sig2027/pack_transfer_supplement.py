"""Build the anonymous, deterministic evidence archive using Python 3.10+."""
import argparse
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
TASKS = HERE.parents[1] / "tasks"
CELL = re.compile(rb"(?:\x00{52})+|(.{52})", re.DOTALL)


def read(path):
    return json.loads(path.read_bytes())


def select(row, *keys):
    return {k: row[k] for k in keys}


def encode(value):
    return (json.dumps(value, indent=2, allow_nan=False) + "\n").encode()


def evidence(number):
    task, = TASKS.glob(f"t{number}-*")
    return task / "evidence"


def sparse_feedback(folder, arm):
    """Write ordered original 52-byte cells with their native linear indices."""
    rows = [json.loads(s) for s in (folder / f"{arm}-steps.ndjson").read_bytes().splitlines()]
    result = io.BytesIO()
    with (folder / f"{arm}-grids.zlib").open("rb") as f:
        for r in (r for r in rows if "feedback" in r):
            meta = r["feedback"]
            if f.tell() != meta["offset"]:
                raise ValueError("Feedback offsets")
            raw = zlib.decompress(f.read(meta["compressed_bytes"]))
            if len(raw) != meta["raw_bytes"] or hashlib.sha256(raw).hexdigest() != meta["sha256"]:
                raise ValueError("Source feedback digest")
            cells = [(m.start() // 52, m[1]) for m in CELL.finditer(raw) if m[1] is not None]
            result.write(struct.pack("<II", len(raw) // 52, len(cells)))
            for index, payload in cells:
                result.write(struct.pack("<I", index) + payload)
        if f.read(1):
            raise ValueError("Unexpected trailing feedback")
    return result.getvalue()


def npy_words(archive, name, dtype):
    """Read the pinned little-endian C-order NPY v1 arrays without NumPy."""
    raw = archive.read(name + ".npy")
    if raw[:8] != b"\x93NUMPY\x01\x00":
        raise ValueError("Unsupported NPY format")
    offset = 10 + struct.unpack_from("<H", raw, 8)[0]
    header = ast.literal_eval(raw[10:offset].decode("ascii").strip())
    if header["descr"] != dtype or header["fortran_order"]:
        raise ValueError("Unexpected numeric layout")
    return raw[offset:]


def add_boundary_witnesses(files, base):
    with zipfile.ZipFile(base / "early-001.npz") as archive:
        for arm in ("ordinary", "stiffer"):
            for key in ("X", "V"):
                files[f"flag/first-cloth-{arm}-{key}.f32"] = npy_words(archive, arm + ".cloth." + key, "<f4")
    # A few original native values let the reader inspect the first gas divergence.
    # For each physical component retain the first numerically unequal pair and
    # the largest absolute difference. The complete pressure/velocity fields are large.
    receipt = {}
    integer, floating = struct.Struct("<I"), struct.Struct("<f")
    with zipfile.ZipFile(base / "early-003.npz") as archive:
        for field, width, components in (("vel", 4, 3), ("p", 1, 1)):
            key = ".gas." + field
            inc = npy_words(archive, "index_increments" + key, "<u4")
            ordinary = npy_words(archive, "ordinary" + key, "<f4")
            xor = npy_words(archive, "xor" + key, "<u4")
            paired = zip(integer.iter_unpack(inc), integer.iter_unpack(ordinary), integer.iter_unpack(xor), strict=True)
            index = 0
            first, largest, maxima = [None] * components, [None] * components, [0.] * components
            for (delta,), (a,), (x,) in paired:
                index += delta
                axis = index % width
                if axis >= components or x == 0:
                    continue
                b = x ^ a
                difference = abs(floating.unpack(integer.pack(a))[0] - floating.unpack(integer.pack(b))[0])
                if difference > 0 and first[axis] is None:
                    first[axis] = [index, a, b]
                if difference > maxima[axis]:
                    largest[axis], maxima[axis] = [index, a, b], difference
            receipt[field] = {"first": first, "max_abs": largest}
    files["flag/first-gas-word-pairs.json"] = encode(receipt)


def add_flag(files):
    base, repeat = evidence(137), evidence(142)
    score = read(base / "SCORE.json")
    runs = {}
    for arm in ("ordinary", "stiffer"):
        files[f"flag/{arm}.sparse"] = sparse_feedback(base, arm)
        files[f"flag/{arm}.ndjson"] = (base / f"{arm}-steps.ndjson").read_bytes().replace(b"\r\n", b"\n")
        files[f"flag/{arm}-scene.json"] = encode(read(base / f"{arm}-scene.json"))
        summary = read(base / f"{arm}.json")
        runs[arm] = select(summary, "pin", "settings", "original_settings", "features", "gas_dims", "h",
                           "detail_upres", "cloth_vertices", "status", "gas_updates", "preparation_wall_s")
        runs[arm].update(select(score["workers"][arm], "exit", "timeout", "limit_s", "wall_s"))
    files["flag/repeat.ndjson"] = (repeat / "ordinary-steps.ndjson").read_bytes().replace(b"\r\n", b"\n")
    files["flag/repeat-grid-digests.json"] = encode(read(repeat / "GRID_SHA256.json"))
    runs["repeat"] = select(read(repeat / "SCORE.json"), "complete", "wall_s", "grid_pairs", "reference_rows",
                            "repeat_rows", "exact_full_record_match")
    files["flag/runs.json"] = encode(runs)
    files["flag/early-field-statistics.json"] = encode(read(base / "INITIAL_FIELDS.json"))
    add_boundary_witnesses(files, base)


def add_woodpile(files):
    base, prior = evidence(140), read(evidence(127) / "SCORE.json")
    cap, score = read(base / "CAPTURE.json"), read(base / "SCORE.json")
    material = read(evidence(109).parent / "REFERENCE.json")["queries"]
    # Source images stay out of the archive. The measured integer difference bins retain all thresholds.
    files["woodpile/contrast.json"] = gzip.decompress((base / "CONTRAST.json.gz").read_bytes())
    files["woodpile/draws.json"] = encode({"draws": cap["draws"], "source": select(cap["source"], "asset", "cameras")})
    files["woodpile/endpoints.json"] = encode(select(score, "tag_counts", "views", "gas", "material", "endpoint"))
    files["woodpile/prior.json"] = encode({
        "source": {"asset": prior["source_sha256"]["foreground.ply"], "cameras": prior["source_sha256"]["cameras.json"]},
        "denominators": {k: v["raster_total"] for k, v in prior["reference_checks"].items()},
        "gas": [select(r, "camera", "horizon", "brush", "changed_pixels", "fraction") for r in prior["comparisons"]],
        "material": [dict(camera=r["camera"], arm=r["arm"], total=r["total"], final=r["curve"][-1])
                     for r in material if r["arm"] in ("AL", "AF") and r["camera"] in (0, 124)]})


def add_bonsai(files):
    run = read(evidence(141) / "RUN.json")
    source = read(evidence(139).parent / "RESULTS.json")
    cfg = source["native_input"]
    files["bonsai/fixed-input.json"] = encode({
        **select(source, "fit_sha256", "source_rows", "view_size"),
        **select(cfg, "source_center", "geometric_shell_count", "geometric_shell_sha256", "camera_ids", "dt",
                 "seed", "view_geometry"),
        "feed_cap": cfg["params"]["spreadFeedCap"],
        # The registered geometric shell was .12 < radius <= .26 in world units.
        "shell_outer_radius": 0.26,
        "picks": [select(p, "name", "site", "radius", "initial_geometric_count", "member_sha256") for p in cfg["picks"]],
        "offline_nearest_pixels": [select(p, "display_pixel_center_xy", "fp16") for p in source["nearest_pixel_diagnostic"]]})
    files["bonsai/native.json"] = encode({
        "load": select(run["load"], "kept", "total", "scene_n", "sha256", "float_color", "sh_degree", "width",
                       "height", "center", "load_gl_error", "context_lost"),
        **select(run, "first", "rest", "parent_progress", "parent", "shell", "matte"),
        "prefix": select(run["pick_audit"], "sites", "width", "height", "nativeBuckets", "format",
                         "threshold", "sourceCameraId", "clock", "dynamicInstancesInNormalDraw", "samples"),
        "actions": [select(r, "method", "audit", "choice", "secondary", "shared_steps", "reused_steps", "branches")
                    for r in run["actions"]]})


def build(output):
    files = {"README.txt": (HERE / "transfer-guide.txt").read_bytes().replace(b"\r\n", b"\n"),
             "verify.py": (HERE / "verify_transfer.py").read_bytes().replace(b"\r\n", b"\n")}
    add_flag(files)
    add_woodpile(files)
    add_bonsai(files)
    files["MANIFEST.sha256"] = "".join(f"{hashlib.sha256(files[n]).hexdigest()}  {n}\n"
                                      for n in sorted(files)).encode()
    with zipfile.ZipFile(output, "w") as archive:
        for name, payload in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    print(f"{hashlib.sha256(output.read_bytes()).hexdigest()}  {output.name}  ({output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", nargs="?", type=Path, default=HERE / "transfer-supplement.zip")
    build(parser.parse_args().output)
