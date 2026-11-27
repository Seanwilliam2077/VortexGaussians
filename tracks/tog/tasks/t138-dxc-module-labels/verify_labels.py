"""Check native module renaming, stage identity, clock, physical restore and any final pixels."""
import argparse
import json
from pathlib import Path

from run_labels import render
from verify_render import verify


def check(folder, *, limit=render.LIMIT, compiled_on_construction=("main","caustics")):
    native = verify(folder,limit=limit,compiled_on_construction=compiled_on_construction)
    rows = [json.loads(line) for line in (folder / "MODULES.ndjson").read_bytes().splitlines()]
    for row in rows:
        render.require(":" in row["original"] and row["submitted"] == row["original"].replace(":", "_"),
                       "Unexpected module-label edit")
    if native["stage"]["worker_status"] == "complete":
        for entry in compiled_on_construction:
            label = "stage.wgsl:" + entry
            render.require(any(r["original"] == label and r["wgsl_sha256"] == render.observe.SOURCE_SHA
                               for r in rows), "Missing original stage shader")
    return dict(measurement=native, translated_module_labels=len(rows))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    print(json.dumps(check(parser.parse_args().folder), indent=2))
