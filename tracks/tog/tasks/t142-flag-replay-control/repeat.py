"""Run the unmodified ordinary T137 worker and account for its full process time."""
import argparse
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ORIGINAL = HERE.parent / "t137-flag-fine-gas"
sys.path.insert(0, str(HERE.parent / "t125-nvidia-dx12-admission"))
from admit import save


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    folder = args.out.resolve()
    folder.mkdir(parents=True, exist_ok=False)
    start = time.time()
    tick = time.perf_counter()
    p = subprocess.Popen([sys.executable, "-B", str(ORIGINAL / "flag.py"), "--source", str(args.source.resolve()),
                          "--out", str(folder), "--worker", "ordinary"])
    limited = False
    try:
        while p.poll() is None:
            if max(time.time() - start, time.perf_counter() - tick) >= 360:
                p.kill()
                limited = True
                break
            time.sleep(.20)
    finally:
        if p.poll() is None:
            p.kill()
        p.wait()
    save(folder / "EXIT.json", dict(pid=p.pid, exit=p.returncode, timeout=limited, budget_s=360,
                                    wall_s=time.time() - start, monotonic_s=time.perf_counter() - tick))
    sys.exit(2 if limited else p.returncode)
