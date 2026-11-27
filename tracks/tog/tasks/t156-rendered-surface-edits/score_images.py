"""Recompute image measurements from the archived native half-float buffers."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
WEIGHTS = np.array([.2126, .7152, .0722])
ARMS = ("default", "slow")


def display(rgb):
    linear = np.clip(rgb, 0., 1.)
    srgb = np.where(linear <= .0031308, 12.92*linear, 1.055*linear**(1/2.4) - .055)
    return np.rint(255*srgb).astype(np.uint8)


def read(out, arm, name, receipt):
    with np.load(out / f"{arm}-{name}.npz", allow_pickle=False) as data:
        pixels = data["pixels"]
    assert pixels.shape == (180, 320, 4) and pixels.dtype == np.float16
    assert np.isfinite(pixels).all() and hashlib.sha256(pixels.tobytes()).hexdigest() == receipt["arms"][arm][name]
    return pixels[..., :3].astype(np.float64)


def metrics(out):
    receipt = json.loads((out / "RESULT.json").read_bytes())
    assert receipt["status"] == "complete"
    assert json.loads((out / "EXIT.json").read_bytes())["exit"] == 0
    assert all(receipt["arms"][arm]["composite_classic_dispatches"] > 0 for arm in ARMS)
    results, pairs = {}, {}
    for name in ("emission", "composite"):
        arms = {}
        rgb = [read(out, arm, name, receipt) for arm in ARMS]
        lum = [im @ WEIGHTS for im in rgb]
        for arm, value in zip(ARMS, lum):
            y, x = np.nonzero(value >= 1.)
            arms[arm] = {"luminance_sum": float(value.sum()), "peak": float(value.max()), "pixels_ge_1": len(x),
                         "bounds_xy_inclusive": [int(x.min()), int(y.min()), int(x.max()), int(y.max())] if len(x) else None}
        delta = lum[0] - lum[1]
        pair = list(map(display, rgb))
        change = np.abs(pair[0].astype(np.int16) - pair[1].astype(np.int16)).max(axis=-1)
        arms["default_minus_slow"] = {"signed_luminance_sum": float(delta.sum()), "absolute_luminance_sum": float(abs(delta).sum()),
                                     "different_linear_rgb_pixels": int(np.count_nonzero((rgb[0] != rgb[1]).any(axis=-1))),
                                     "changed_display_pixels": int(np.count_nonzero(change)),
                                     "display_pixels_ge_16": int((change >= 16).sum())}
        results[name], pairs[name] = arms, pair
    return results, pairs


def panel(pairs):
    sheet = Image.new("RGB", (640, 414), (26, 27, 30))
    ink = ImageDraw.Draw(sheet)
    for row, name in enumerate(("composite", "emission")):
        for col, (arm, timing) in enumerate(zip(ARMS, (0.35, 0.70))):
            x, y = col*320, row*207
            ink.text((x+8,y+6), f"{name.capitalize()}    catch time {timing:.2f} s", fill="white")
            sheet.paste(Image.fromarray(pairs[name][col]), (x, y+27))
    return sheet


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=HERE/"evidence")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result, pairs = metrics(args.out)
    dest = args.out/"SCORE.json"
    image = panel(pairs)
    if args.write:
        dest.write_text(json.dumps(result, indent=2)+"\n", encoding="utf8")
        image.save(args.out/"original-camera.png")
    else:
        assert json.loads(dest.read_bytes()) == result
        with Image.open(args.out/"original-camera.png") as actual:
            assert np.array_equal(actual, image)
    print(json.dumps(result, indent=2))
