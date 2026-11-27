"""Verify original inputs and produce the three fixed tag sets; no rendering."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
T109 = HERE.parent / "t109-common-parent-choice"
T127 = HERE.parent / "t127-woodpile-native-camera"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def labels(source, frames):
    prior = json.loads((T127 / "evidence/SCORE.json").read_bytes())
    for p in [source / "foreground.ply", source / "cameras.json", T109 / "REFERENCE.json", T109 / "shell.json.gz",
              T109 / "evidence/native/capture-report.json", *(T109 / f"evidence/native/{arm}-trace.json.gz" for arm in ("AL","AF"))]:
        if sha(p) != prior["source_sha256"][p.name]:
            raise ValueError(f"Original source identity: {p.name}")
    pngs = {name:h for row in prior["comparisons"] for name,h in row["sha256"].items()}
    if len(pngs) != 16 or any(sha(frames / name) != h for name,h in pngs.items()):
        raise ValueError("Sixteen original native color/control images required")
    spec = importlib.util.spec_from_file_location("woodpile_project", T109 / "figure/project.py")
    project = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(project)
    original = project.native_labels()
    eligible = original["AL"][0]
    if eligible != original["AF"][0] or len(eligible) != 2371:
        raise ValueError("Different original eligible IDs")
    return {"eligible":sorted(eligible), "light":sorted(original["AL"][1]), "full":sorted(original["AF"][1])}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("frames", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    sets = labels(a.source, a.frames)
    with a.output.open("x", encoding="utf-8") as target:
        json.dump(sets, target, separators=(",", ":"))
    print({key:len(v) for key,v in sets.items()})
