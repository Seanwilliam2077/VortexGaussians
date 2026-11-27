"""Compare the exact native emission and the displayed material edit at fixed exposure."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
CAMERA = HERE.parent/"t156-rendered-surface-edits"
sys.path.insert(0, str(CAMERA))
from score_images import WEIGHTS, display


def read(directory, arm, name):
    with np.load(directory/f"{arm}-{name}.npz", allow_pickle=False) as data:
        pixels = data["pixels"]
    receipt = json.loads((directory/"RESULT.json").read_bytes())
    assert pixels.shape == (180,320,4) and pixels.dtype == np.float16 and np.isfinite(pixels).all()
    assert receipt["arms"][arm][name] == hashlib.sha256(pixels.tobytes()).hexdigest()
    return pixels


def compare(out):
    receipt = json.loads((out/"RESULT.json").read_bytes())
    assert receipt["status"] == "complete" and json.loads((out/"EXIT.json").read_bytes())["exit"] == 0
    assert all(receipt["arms"][arm]["composite_classic_dispatches"] >= 1 for arm in ("ten","five"))
    score = {}
    sheet = Image.new("RGB",(640,412),(26,27,30))
    ink = ImageDraw.Draw(sheet)
    for row, name in enumerate(("composite","emission")):
        ten, five = (read(out, arm, name) for arm in ("ten","five"))
        assert five.tobytes() == read(CAMERA/"evidence","default",name).tobytes()
        rgb = [a[..., :3].astype(np.float64) for a in (ten,five)]
        pair = list(map(display, rgb))
        raw_delta = rgb[1]-rgb[0]
        disp = np.abs(pair[1].astype(np.int16)-pair[0].astype(np.int16)).max(axis=-1)
        lum = raw_delta @ WEIGHTS
        score[name] = dict(raw_rgba_equal=ten.tobytes()==five.tobytes(),
                           changed_rgb_pixels=int(np.count_nonzero((raw_delta!=0).any(axis=-1))),
                           max_abs_rgb=float(abs(raw_delta).max()),
                           sum_abs_rgb=float(abs(raw_delta).sum()),
                           sum_abs_luminance=float(abs(lum).sum()), signed_luminance_five_minus_ten=float(lum.sum()),
                           max_display_channel_delta=int(disp.max()),
                           displayed_pixels={str(k):int(np.count_nonzero(disp>=k)) for k in (1,4,16)},
                           five_second_reference_rgba_identical=True)
        for col, (title, img) in enumerate(zip(("10 s source","5 s late edit"), pair)):
            x,y=col*320,row*206
            ink.text((x+8,y+6),f"{name.capitalize()}    {title}",fill="white")
            sheet.paste(Image.fromarray(img),(x,y+26))
    return score,sheet


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out",type=Path,default=HERE/"evidence")
    p.add_argument("--write",action="store_true")
    a=p.parse_args()
    score,sheet=compare(a.out)
    dest=a.out/"SCORE.json"; png=a.out/"late-edit-camera.png"
    if a.write:
        dest.write_text(json.dumps(score,indent=2)+"\n",encoding="utf8")
        sheet.save(png)
    else:
        assert json.loads(dest.read_bytes())==score
        with Image.open(png) as archived:
            assert np.array_equal(archived,sheet)
    print(json.dumps(score,indent=2))
