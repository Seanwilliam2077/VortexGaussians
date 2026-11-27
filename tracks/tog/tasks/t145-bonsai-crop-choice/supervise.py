"""Use T144's original serial process/deadline policy with the T145 worker."""
import argparse
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = next(HERE.parent.glob("t144-*/supervise.py"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    directory = parser.parse_args().out.resolve()
    spec = importlib.util.spec_from_file_location("paired_bonsai_supervisor", SOURCE)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    supervisor.HERE = HERE
    directory.mkdir(parents=True, exist_ok=False)
    for number in (1, 2):
        if not supervisor.one(directory, number):
            raise SystemExit(1)
