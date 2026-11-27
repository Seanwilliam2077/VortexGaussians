"""Run exactly two fresh, serial browser processes under the registered per-process caps."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import perf_counter

HERE = Path(__file__).resolve().parent
LIMIT = 210


def one(out, number):
    proc_dir = out / f"process-{number}"
    proc_dir.mkdir()
    started = datetime.now(timezone.utc).isoformat()
    begin = perf_counter()
    with (proc_dir / "host.log").open("w", encoding="utf8") as log:
        proc = subprocess.Popen(["node", str(HERE / "run.mjs"), str(proc_dir), str(number)],
                                stdout=log, stderr=subprocess.STDOUT, start_new_session=os.name != "nt")
        try:
            code = proc.wait(timeout=max(.01, LIMIT - (perf_counter() - begin)))
            expired = False
        except subprocess.TimeoutExpired:
            expired = True
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], stdout=log, stderr=log, check=False)
            else:
                os.killpg(proc.pid, signal.SIGKILL)
            code = proc.wait()
    elapsed = perf_counter() - begin
    receipt = dict(process=number, limit_s=LIMIT, started_utc=started, elapsed_s=elapsed,
                   returncode=code, expired=expired or elapsed > LIMIT)
    (proc_dir / "EXIT.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(receipt, flush=True)
    if code or receipt["expired"]:
        return False
    return json.loads((proc_dir / "RUN.json").read_text(encoding="utf8"))["status"] == "replication_complete"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    directory = parser.parse_args().out.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    for number in (1, 2):
        if not one(directory, number):
            sys.exit(1)
