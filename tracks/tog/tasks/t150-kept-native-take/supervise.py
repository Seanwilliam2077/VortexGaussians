"""Run two fresh, bounded browser processes and preserve each terminal receipt."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from time import monotonic

HERE = Path(__file__).resolve().parent


def run(output, private):
    output.mkdir()
    for block in (1, 2):
        dest = output / f"process-{block}"
        start = monotonic()
        when = datetime.now(timezone.utc).isoformat()
        cmd = ["node", str(HERE / "run.mjs"), str(block), str(dest), str(private)]
        with (output / f"process-{block}.log").open("w", encoding="utf8") as log:
            child = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            expired = False
            try:
                child.wait(timeout=210)
            except subprocess.TimeoutExpired:
                expired = True
                if subprocess.os.name == "nt":
                    subprocess.run(["taskkill", "/PID", str(child.pid), "/T", "/F"], stdout=log, stderr=log)
                else:
                    child.kill()
                child.wait()
        stop = dict(process=block, pid=child.pid, start_utc=when, elapsed_s=monotonic()-start,
                    budget_s=210, exit=child.returncode, expired=expired)
        (output / f"exit-{block}.json").write_text(json.dumps(stop, indent=2) + "\n", encoding="utf8")
        if expired or child.returncode:
            raise SystemExit(f"Process {block} stopped: {stop}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("output", type=Path)
    p.add_argument("--private", type=Path, required=True)
    args = p.parse_args()
    run(args.output.resolve(), args.private.resolve())
