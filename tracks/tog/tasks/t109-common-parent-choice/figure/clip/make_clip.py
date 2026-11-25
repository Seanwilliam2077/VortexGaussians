"""Animate T109's exact onset ledgers and calibrated projected opacity contributions."""
from argparse import ArgumentParser
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import reportlab


HERE = Path(__file__).resolve().parent
FIGURE = HERE.parent
TASK = FIGURE.parent
TASKS = TASK.parent
FPS = 12
VIEWS = (0, 124)
ARMS = ("AL", "AF")
SIZE = (1120, 768)
IMAGE_SIZE = (490, 236)
BACKGROUND = "#f8f8f5"
INK = "#202a32"
SECONDARY = "#46545a"
ORANGE = "#ab3d1f"


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    out = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(out)
    return out


diagram = module("woodpile_diagram", FIGURE / "figure.py")
registered = module("woodpile_project", FIGURE / "project.py")
metrics = registered.metrics
read = metrics.read


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_labels():
    ref = read(TASK / "REFERENCE.json")
    rows = {(r["camera"], r["arm"]): r for r in ref["queries"]}
    eligible, end_hits = registered.native_labels()["AL"]
    labels = {}
    for arm in ARMS:
        trace = read(TASK / f"evidence/native/{arm}-trace.json.gz")
        assert [x["frame"] for x in trace[180:270]] == list(range(181, 271))
        labels[arm] = [set()] + [set(x["new_ids"]) & eligible for x in trace[180:270]]
        assert sum(map(len, labels[arm])) == len(set.union(*labels[arm]))
    assert set.union(*labels["AL"]) == end_hits
    return eligible, labels, rows


def footprints(data, opacity, eligible):
    """Keep unrounded per-site pixel contributions for exact temporal compositing."""
    w, h, depth, uv, covariance = data
    trans = np.ones((h, w))
    shell = np.zeros((h, w))
    parts = {}
    for j in np.argsort(depth, kind="stable"):
        if depth[j] <= 0 or opacity[j] < 1 / 255:
            continue
        u, v = uv[j]
        sx, sy = 3 * np.sqrt(np.diag(covariance[j]))
        l, r = max(0, math.ceil(u-sx)), min(w-1, math.floor(u+sx))
        t, b = max(0, math.ceil(v-sy)), min(h-1, math.floor(v+sy))
        if l > r or t > b:
            continue
        x = np.arange(l, r+1)-u
        y = (np.arange(t, b+1)-v)[:, None]
        a, ab, c = covariance[j, 0, 0], covariance[j, 0, 1], covariance[j, 1, 1]
        distance = (c*x*x-2*ab*x*y+a*y*y) / (a*c-ab*ab)
        alpha = np.minimum(.99, opacity[j]*np.exp(-.5*distance))
        alpha[(distance > 9) | (alpha < 1/255)] = 0
        box = np.s_[t:b+1, l:r+1]
        if j in eligible:
            contribution = trans[box] * alpha
            shell[box] += contribution
            parts[int(j)] = (box, contribution)
        trans[box] *= 1-alpha
    return shell, 1-trans, parts


def panels(source, receipts):
    eligible, labels, rows = load_labels()
    cameras = {r["id"]: r for r in read(source / "cameras.json")}
    assert sha(source / "cameras.json") == read(FIGURE / "validation.json")["source_sha256"]["cameras.json"]
    pos, cov, opacity = metrics.splats(source / "foreground.ply")
    if not (FIGURE / "local/geometric-bins.npz").exists():
        registered.project(source)
    tri, normal = diagram.reconstruct()
    images = {}
    for view in VIEWS:
        archived = read(TASKS / f"t107-visible-burn-progression/evidence/weights-{view}.json.gz")
        weights = dict(archived["eligible_weights"])
        shell, coverage, parts = footprints(metrics.projection(pos, cov, cameras[view]), opacity, eligible)
        measured = {j: float(parts[j][1].sum()) if j in parts else 0.0 for j in eligible}
        np.testing.assert_allclose([measured[j] for j in sorted(eligible)],
                                   [weights[j] for j in sorted(eligible)], atol=1e-11, rtol=3e-12)
        quantized = {j: math.floor(mass*1e6+.5) for j, mass in measured.items()}
        assert all(quantized[j] == math.floor(weights[j]*1e6+.5) for j in eligible)
        total = sum(quantized.values())
        total_float = math.fsum(weights[j] for j in eligible)
        np.testing.assert_allclose(shell.sum(), total_float, rtol=3e-13)
        with np.load(FIGURE / f"local/projection-{view}.npz") as baseline:
            np.testing.assert_allclose(coverage, baseline["coverage"], atol=1e-13)
            np.testing.assert_allclose(shell, baseline["shell"], atol=1e-13)
            # Keeping the original silhouette and shell support fixes the published crop
            # even while requesting the neutral base without any colored overlay.
            zero = np.zeros_like(shell)
            base, crop = diagram.draw_scene(cameras[view], tri, normal,
                    dict(coverage=np.maximum(coverage, shell > 0), shell=zero, light=zero, full=zero))
            assert crop == diagram.crop_for(coverage, shell, 780/398)
            l, t, r, b = crop
            np.testing.assert_allclose(shell[t:b, l:r].sum(), total_float, rtol=3e-13)
            # Preserve the figure's calibrated aspect; leave additional margins in the panel.
            size = (round(IMAGE_SIZE[1]*780/398), IMAGE_SIZE[1])
            def zoom(a):
                image = Image.fromarray(a.astype("float32")).crop(crop)
                return np.asarray(image.resize(size, Image.Resampling.BILINEAR), dtype="float32")[:, :, None]
            neutral = np.asarray(base["AL"].resize(size, Image.Resampling.LANCZOS), dtype="float32")
            teal = diagram.ELIGIBLE.astype("float32")
            initial = neutral*(1-zoom(shell)) + teal*zoom(shell)
            color_change = diagram.IGNITED.astype("float32")-teal
            for arm, old in (("AL", "light"), ("AF", "full")):
                ref = rows[view, arm]
                assert total == ref["total"] and len(eligible) == ref["eligible"]
                matte = np.zeros_like(shell)
                cumulative_ids = set()
                integer = 0
                first = None
                previous_panel = None
                for step, ignitions in enumerate(labels[arm]):
                    for j in sorted(ignitions):
                        if j in parts:
                            box, contribution = parts[j]
                            matte[box] += contribution
                    integer += sum(quantized[j] for j in ignitions)
                    cumulative_ids.update(ignitions)
                    mass = float(matte[t:b, l:r].sum())
                    expected_mass = math.fsum(weights[j] for j in cumulative_ids)
                    np.testing.assert_allclose(mass, expected_mass, rtol=3e-13, atol=1e-12)
                    np.testing.assert_allclose(matte.sum(), expected_mass, rtol=3e-13, atol=1e-12)
                    if step:
                        assert [180+step, len(ignitions), len(cumulative_ids), integer] == ref["curve"][step-1]
                    if first is None and 4*integer >= total:
                        first = step+180
                    if previous_panel is None or ignitions:
                        rgb = initial + color_change * zoom(matte)
                        previous_panel = Image.fromarray(np.rint(np.clip(rgb, 0, 255)).astype("uint8"))
                    images[step, view, arm] = previous_panel
                    receipts[step, view, arm] = dict(
                        n=len(cumulative_ids), integer=integer, total=total, first=first,
                        opacity=mass, denominator_opacity=total_float)
                np.testing.assert_allclose(matte, baseline[old], rtol=3e-13, atol=1e-13)
                assert first == ref["first_frame"] and integer == ref["deadline_mass"]
    return images


FONT_DIR = Path(reportlab.__file__).parent / "fonts"
FONTS = {}


def font(size, bold=False):
    key = size, bold
    if key not in FONTS:
        FONTS[key] = ImageFont.truetype(str(FONT_DIR / ("VeraBd.ttf" if bold else "Vera.ttf")), size)
    return FONTS[key]


def page(step, hold, images, records):
    canvas = Image.new("RGB", SIZE, BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    def label(x, y, value, size=16, bold=False, color=INK):
        draw.text((x, y), value, font=font(size, bold), fill=color, anchor="lt")
    label(30, 15, "Which brush reaches 25% within 90 steps?", 31, True)
    label(31, 58, "Same woodpile and starting state. Colors measure projected opacity of the eligible shell.", 17)
    for x, rgb, txt in ((31, diagram.ELIGIBLE, "Eligible, unignited"), (255, diagram.IGNITED, "Ignited since the edit")):
        draw.rectangle((x, 91, x+13, 104), fill=tuple(rgb))
        label(x+21, 90, txt, 16)
    label(705, 90, "Native step 1/60 s   |   Playback 0.20×", 17, color=SECONDARY)
    draw.line((30, 119, 1090, 119), fill="#bcc2c0", width=1)
    label(119, 133, "Light brush", 23, True)
    label(287, 139, "radius 0.06", 16, color=SECONDARY)
    label(620, 133, "Full brush", 23, True)
    label(766, 139, "radius 0.12", 16, color=SECONDARY)
    for row, view in enumerate(VIEWS):
        y = 159 + 245*row
        label(29, y+42, "Camera", 16, color=SECONDARY)
        label(27, y+67, str(view), 31, True)
        for col, arm in enumerate(ARMS):
            x = 117 + 501*col
            # The crop and geometry are constant across time and both brush widths.
            pic = images[step, view, arm].resize((362, 185), Image.Resampling.LANCZOS)
            canvas.paste(pic, (x+52, y))
            stat = records[step, view, arm]
            pct = 100*stat["integer"]/stat["total"]
            label(x, y+194, f"{pct:.3f}%", 22, True, ORANGE if stat["first"] else INK)
            label(x+133, y+198, "of eligible opacity", 15, color=SECONDARY)
            left, right = x, x+462
            draw.rectangle((left, y+225, right, y+231), fill="#dce1de")
            if pct:
                draw.rectangle((left, y+225, left+max(0,round((right-left)*pct/100)-1), y+231),
                               fill=ORANGE if stat["first"] else "#596f77")
            target = left+round((right-left)*.25)
            draw.line((target, y+221, target, y+235), fill=INK, width=2)
            label(x+299, y+198, f"Crossed at +{stat['first']-180}" if stat["first"] else "Below 25%", 15,
                  bold=bool(stat["first"]), color=ORANGE if stat["first"] else SECONDARY)
    draw.line((30, 650, 1090, 650), fill="#bcc2c0", width=1)
    label(30, 668, f"Step  +{step:02d} / 90", 24, True)
    label(266, 674, f"Native frame  {180+step}", 16, color=SECONDARY)
    if hold == "edit":
        message = "Second brush applied at frame 180 (held)."
    elif hold == "cross":
        message = "First crossing in camera 0 (held)."
    elif hold == "end" or step == 90:
        message = "Only the full brush in camera 0 reaches 25%."
    else:
        message = "12 native steps per playback second."
    label(569, 672, message, 19, True, ORANGE if hold == "cross" else INK)
    draw.line((31, 714, 1087, 714), fill="#bec5c2", width=3)
    draw.line((31, 714, 31+round(1056*step/90), 714), fill="#466979", width=3)
    draw.ellipse((27+round(1056*step/90), 710, 35+round(1056*step/90), 718), fill="#283c46")
    label(30, 729, "Second brush", 15, color=SECONDARY)
    label(951, 729, "90-step deadline", 15, color=SECONDARY)
    return canvas


def write(source):
    records = {}
    images = panels(source, records)
    path = HERE / "brush-choice.mp4"
    # Distinct annotations mark all three still holds. Every active row is one native step.
    schedule = ([(0, "edit")]*24 + [(n, "") for n in range(1, 45)] + [(44, "cross")]*12 +
                [(n, "") for n in range(45, 91)] + [(90, "end")]*24)
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-s", f"{SIZE[0]}x{SIZE[1]}", "-framerate", str(FPS), "-i", "-",
               "-an", "-c:v", "libx264", "-threads", "2", "-preset", "fast", "-crf", "18",
               "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-map_metadata", "-1", str(path)]
    proc = subprocess.Popen(command, stdin=subprocess.PIPE)
    last, frame = None, None
    with proc.stdin:
        for entry in schedule:
            if entry != last:
                frame = page(*entry, images, records).tobytes()
                last = entry
            proc.stdin.write(frame)
    if proc.wait() != 0:
        raise RuntimeError("H.264 encoder failed")
    probe = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-count_frames",
        "-show_entries", "stream=codec_name,pix_fmt,width,height,avg_frame_rate,nb_read_frames:format=duration",
        "-of", "json", str(path)]))
    assert len(probe["streams"]) == 1
    stream = probe["streams"][0]
    assert (stream["codec_name"], stream["pix_fmt"], stream["width"], stream["height"],
            int(stream["nb_read_frames"]), stream["avg_frame_rate"]) == ("h264", "yuv420p", *SIZE, 150, "12/1")
    assert path.stat().st_size < 5_000_000 and float(probe["format"]["duration"]) == 12.5
    fields = ["step", "native_frame", "camera", "brush", "newly_ignited_to_date",
              "burnt_micro_pixels", "eligible_micro_pixels", "burnt_pixel_opacity", "eligible_pixel_opacity"]
    with (HERE / "frames.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(fields)
        for (n, v, a), row in sorted(records.items()):
            writer.writerow((n, 180+n, v, a, row["n"], row["integer"], row["total"], row["opacity"],
                             row["denominator_opacity"]))
    inputs = [TASK/"recipe.json", TASK/"REFERENCE.json", TASK/"shell.json.gz", TASK/"evidence/native/capture-report.json",
              *(TASK/f"evidence/native/{a}-trace.json.gz" for a in ARMS),
              *(TASKS/f"t107-visible-burn-progression/evidence/weights-{v}.json.gz" for v in VIEWS),
              FIGURE/"figure.py", FIGURE/"project.py", TASKS/"t107-visible-burn-progression/measure.py"]
    receipt = dict(schema="t109-calibrated-clip-v1", probe=probe, bytes=path.stat().st_size, sha256=sha(path),
            native_frame_range=[181, 270], fixed_dt=read(TASK/"recipe.json")["dt"], distinct_progress_frames=90,
            exact_curve_rows_checked=360, checked_initial_rows=4, panel_units="per-site rounded micro-pixels",
            verified_floating_matte="full-frame and fixed displayed crop on every step, rtol 3e-13 atol 1e-12",
            frame_table_sha256=sha(HERE/"frames.csv"), source_sha256={p.relative_to(TASKS).as_posix():sha(p) for p in inputs},
            external_inputs_sha256={p:sha(source/p) for p in ("cameras.json", "foreground.ply")},
            generator_sha256=sha(Path(__file__)), encoder=subprocess.check_output(["ffmpeg", "-version"],text=True).splitlines()[0])
    (HERE/"receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=TASK.parents[4]/"real-asset-ingest")
    write(parser.parse_args().source)
